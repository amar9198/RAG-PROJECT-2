"""RAG logic for BookMind AI (shared by the Streamlit app and the CLI).

Same architecture as the original main.py: Mistral embeddings -> ChromaDB ->
MMR retrieval -> ChatPromptTemplate -> Groq LLM, answering only from context.
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Callable

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

import database as db

logger = logging.getLogger(__name__)

LLM_MODEL = "openai/gpt-oss-120b"
NOT_FOUND_ANSWER = "I could not find the answer in the document."
REQUIRED_KEYS = ("MISTRAL_API_KEY", "GROQ_API_KEY")

MAX_FILE_MB = 50
MIN_AVG_CHARS_PER_PAGE = 25  # below this we treat the PDF as scanned / image-only
EMBED_BATCH_SIZE = 32

ProgressFn = Callable[[float, str], None]


# --------------------------------------------------------------------------
# Settings and errors
# --------------------------------------------------------------------------
@dataclass
class RAGSettings:
    chunk_size: int = 1000
    chunk_overlap: int = 200
    k: int = 4
    fetch_k: int = 10
    lambda_mult: float = 0.5


class BookMindError(Exception):
    """An error whose message is safe and useful to show to the user."""


class InvalidPDFError(BookMindError):
    pass


class OCRRequiredError(BookMindError):
    pass


class DuplicateBookError(BookMindError):
    def __init__(self, message: str, book: dict):
        super().__init__(message)
        self.book = book


def missing_api_keys() -> list[str]:
    return [name for name in REQUIRED_KEYS if not os.getenv(name, "").strip()]


def _redact(text: str) -> str:
    """Strip any API key value that might appear inside an error message."""
    for name in REQUIRED_KEYS:
        value = os.getenv(name, "").strip()
        if value:
            text = text.replace(value, "[hidden]")
    return text


def friendly_error(exc: Exception) -> str:
    """Turn any exception into a message that is safe to show in the UI."""
    if isinstance(exc, BookMindError):
        return str(exc)
    logger.error("%s: %s", type(exc).__name__, _redact(str(exc)))
    text = f"{type(exc).__name__} {exc}".lower()
    if any(s in text for s in ("401", "403", "unauthorized", "invalid api key", "authentication")):
        return "The AI provider rejected the API key. Check MISTRAL_API_KEY and GROQ_API_KEY in your .env file."
    if any(s in text for s in ("429", "rate limit", "rate_limit", "too many requests")):
        return "The AI provider's rate limit was reached. Wait a moment and try again."
    if any(s in text for s in ("timeout", "timed out", "connection", "network", "503", "502")):
        return "Could not reach the AI provider. Check your internet connection and try again."
    return f"Something went wrong ({type(exc).__name__}). Check the terminal logs for details."


def _is_transient(exc: Exception) -> bool:
    text = f"{type(exc).__name__} {exc}".lower()
    return any(s in text for s in ("429", "rate limit", "timeout", "timed out", "502", "503", "connection"))


# --------------------------------------------------------------------------
# PDF validation
# --------------------------------------------------------------------------
def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_upload(filename: str, data: bytes) -> None:
    if not data:
        raise InvalidPDFError("The uploaded file is empty.")
    if not filename.lower().endswith(".pdf"):
        raise InvalidPDFError("Only PDF files are supported.")
    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise InvalidPDFError(f"This file is larger than the {MAX_FILE_MB} MB limit.")
    if b"%PDF-" not in data[:1024]:
        raise InvalidPDFError("This file doesn't look like a valid PDF.")


def inspect_pdf(data: bytes) -> dict:
    """Return basic info (page count). Raises InvalidPDFError if unreadable."""
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise InvalidPDFError("This PDF is password-protected. Remove the password and upload it again.")
        pages = len(reader.pages)
    except InvalidPDFError:
        raise
    except Exception as exc:
        raise InvalidPDFError("This PDF appears to be corrupted or unreadable.") from exc
    if pages == 0:
        raise InvalidPDFError("This PDF has no pages.")
    return {"pages": pages}


# --------------------------------------------------------------------------
# Indexing
# --------------------------------------------------------------------------
def _add_with_retry(vectorstore, docs: list[Document], ids: list[str], attempts: int = 3) -> None:
    for attempt in range(attempts):
        try:
            vectorstore.add_documents(docs, ids=ids)
            return
        except Exception as exc:
            if attempt == attempts - 1 or not _is_transient(exc):
                raise
            time.sleep(2 * 2**attempt)


def process_book(
    vectorstore,
    filename: str,
    data: bytes,
    settings: RAGSettings,
    progress: ProgressFn | None = None,
) -> dict:
    """Validate, read, chunk, embed and store one PDF.

    Returns ``{"book": record, "warnings": [...]}``. Raises BookMindError
    (with a user-safe message) on failure; a failed attempt leaves no chunks behind.
    """
    report = progress or (lambda _f, _m: None)

    report(0.02, "Validating file...")
    validate_upload(filename, data)
    sha = sha256_of(data)

    existing = db.find_by_hash(sha)
    if existing:
        if existing["status"] == db.STATUS_INDEXED:
            raise DuplicateBookError(
                f"'{existing['filename']}' is already in your library.", existing
            )
        if existing["status"] == db.STATUS_PROCESSING:
            raise DuplicateBookError(f"'{existing['filename']}' is already being processed.", existing)
        # An earlier attempt failed: clear it and try again.
        db.delete_book(vectorstore, existing["id"])

    info = inspect_pdf(data)
    book = db.create_book(
        filename=filename,
        size_bytes=len(data),
        pages=info["pages"],
        sha256=sha,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    doc_id = book["id"]
    db.update_book(doc_id, status=db.STATUS_PROCESSING)
    warnings: list[str] = []

    try:
        report(0.08, "Reading PDF text...")
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(data)
                tmp_path = tmp.name
            pages = PyPDFLoader(tmp_path).load()
        except Exception as exc:
            raise InvalidPDFError("The text in this PDF could not be read.") from exc
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        total_chars = sum(len(p.page_content.strip()) for p in pages)
        if total_chars < MIN_AVG_CHARS_PER_PAGE * max(info["pages"], 1):
            raise OCRRequiredError(
                "This PDF has little or no selectable text, so it is probably a scan (images of pages). "
                "Run it through an OCR tool such as OCRmyPDF, then upload the result."
            )
        empty_pages = sum(1 for p in pages if not p.page_content.strip())
        if empty_pages:
            warnings.append(f"{empty_pages} of {info['pages']} pages had no extractable text and were skipped.")

        report(0.15, "Splitting text into chunks...")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )
        chunks = [c for c in splitter.split_documents(pages) if c.page_content.strip()]
        if not chunks:
            raise OCRRequiredError("No readable text was found in this PDF.")

        uploaded_at = book["uploaded_at"]
        ids: list[str] = []
        for i, chunk in enumerate(chunks):
            chunk.metadata = {
                "doc_id": doc_id,
                "filename": filename,
                "page_number": int(chunk.metadata.get("page", 0)) + 1,  # PyPDF pages are 0-based
                "chunk_index": i,
                "uploaded_at": uploaded_at,
            }
            ids.append(f"{doc_id}-{i}")

        total = len(chunks)
        for start in range(0, total, EMBED_BATCH_SIZE):
            end = min(start + EMBED_BATCH_SIZE, total)
            _add_with_retry(vectorstore, chunks[start:end], ids[start:end])
            report(0.15 + 0.83 * end / total, f"Embedding and indexing chunks ({end}/{total})...")

        book = db.update_book(doc_id, status=db.STATUS_INDEXED, chunks=total, error=None)
        report(1.0, "Done.")
        return {"book": book, "warnings": warnings}

    except Exception as exc:
        message = friendly_error(exc)
        try:
            db.delete_chunks(vectorstore, doc_id)  # no partial index left behind
        except Exception as cleanup_exc:
            logger.error("Cleanup failed: %s", type(cleanup_exc).__name__)
        db.update_book(doc_id, status=db.STATUS_FAILED, chunks=0, error=message)
        raise BookMindError(message) from exc


# --------------------------------------------------------------------------
# Question answering
# --------------------------------------------------------------------------
PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful AI assistant.

Use ONLY the provided context to answer the question.

If the answer is not present in the context,
say: "I could not find the answer in the document."
""",
        ),
        (
            "human",
            """Context:
{context}

Question:
{question}
""",
        ),
    ]
)


def get_llm() -> ChatGroq:
    return ChatGroq(model=LLM_MODEL, temperature=0)


def build_retriever(vectorstore, doc_id: str, settings: RAGSettings):
    """MMR retriever restricted to one book via a metadata filter."""
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": settings.k,
            "fetch_k": max(settings.fetch_k, settings.k),
            "lambda_mult": settings.lambda_mult,
            "filter": {"doc_id": doc_id},
        },
    )


def _text_of(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # some providers return content blocks
        return "".join(
            part if isinstance(part, str) else part.get("text", "") for part in content
        )
    return str(content)


def answer_question(
    vectorstore, llm, doc_id: str, question: str, settings: RAGSettings
) -> tuple[str, list[Document]]:
    """Answer from the selected book only. Returns (answer, source chunks)."""
    question = question.strip()
    if not question:
        raise BookMindError("Please enter a question.")

    docs = build_retriever(vectorstore, doc_id, settings).invoke(question)
    docs = [d for d in docs if d.metadata.get("doc_id") == doc_id]  # belt and braces
    if not docs:
        return NOT_FOUND_ANSWER, []

    context = "\n\n".join(d.page_content for d in docs)
    final_prompt = PROMPT.invoke({"context": context, "question": question})
    answer = _text_of(llm.invoke(final_prompt).content).strip()
    return answer or NOT_FOUND_ANSWER, docs


def describe_sources(docs: list[Document], snippet_chars: int = 320) -> list[dict]:
    return [
        {
            "filename": d.metadata.get("filename", "unknown"),
            "page": d.metadata.get("page_number"),
            "snippet": d.page_content.strip()[:snippet_chars]
            + ("..." if len(d.page_content.strip()) > snippet_chars else ""),
        }
        for d in docs
    ]