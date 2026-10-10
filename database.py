"""Persistent storage for BookMind AI.

Two things are stored on disk:

* ChromaDB (``chroma_db/``): one shared collection holding every book's chunks.
  Each chunk carries ``doc_id`` metadata, and retrieval always filters on it,
  so one book can never leak into answers about another.
* A small JSON registry (``data/library.json``): one record per uploaded book
  (filename, size, pages, status, chunk count, upload time...).
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_mistralai import MistralAIEmbeddings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = str(BASE_DIR / "chroma_db")
REGISTRY_PATH = BASE_DIR / "data" / "library.json"

# A new collection name (instead of Chroma's default "langchain") keeps the
# multi-book index separate from anything the old single-book main.py stored.
COLLECTION_NAME = "bookmind_chunks"
EMBEDDING_MODEL = "mistral-embed"

STATUS_UPLOADED = "uploaded"
STATUS_PROCESSING = "processing"
STATUS_INDEXED = "indexed"
STATUS_FAILED = "failed"

_lock = threading.RLock()


# --------------------------------------------------------------------------
# Vector store
# --------------------------------------------------------------------------
def get_embeddings() -> MistralAIEmbeddings:
    return MistralAIEmbeddings(model=EMBEDDING_MODEL)


def get_vectorstore(embeddings: Any | None = None) -> Chroma:
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings or get_embeddings(),
    )


def count_vectors(vectorstore: Chroma) -> int:
    """Total number of chunks stored across all books."""
    return int(vectorstore._collection.count())


def delete_chunks(vectorstore: Chroma, doc_id: str) -> int:
    """Delete only the chunks that belong to ``doc_id``. Returns how many."""
    found = vectorstore.get(where={"doc_id": doc_id}, include=["metadatas"])
    ids = found.get("ids", [])
    for start in range(0, len(ids), 500):
        vectorstore.delete(ids=ids[start : start + 500])
    return len(ids)


# --------------------------------------------------------------------------
# Library registry
# --------------------------------------------------------------------------
def _read() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        # Keep the unreadable file for manual recovery instead of overwriting it.
        backup = REGISTRY_PATH.with_suffix(".corrupt")
        try:
            os.replace(REGISTRY_PATH, backup)
        except OSError:
            pass
        logger.error("Library registry was unreadable; moved to %s", backup.name)
        return []


def _write(records: list[dict]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(records, indent=2), encoding="utf-8")
    os.replace(tmp, REGISTRY_PATH)  # atomic: never leaves a half-written file


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_books() -> list[dict]:
    """All books, newest first."""
    with _lock:
        return sorted(_read(), key=lambda b: b.get("uploaded_at", ""), reverse=True)


def get_book(doc_id: str | None) -> dict | None:
    if not doc_id:
        return None
    with _lock:
        return next((b for b in _read() if b["id"] == doc_id), None)


def find_by_hash(sha256: str) -> dict | None:
    with _lock:
        return next((b for b in _read() if b.get("sha256") == sha256), None)


def create_book(
    *,
    filename: str,
    size_bytes: int,
    pages: int,
    sha256: str,
    chunk_size: int,
    chunk_overlap: int,
) -> dict:
    record = {
        "id": uuid.uuid4().hex,
        "filename": filename,
        "size_bytes": size_bytes,
        "pages": pages,
        "chunks": 0,
        "status": STATUS_UPLOADED,
        "error": None,
        "uploaded_at": now_iso(),
        "sha256": sha256,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "embedding_model": EMBEDDING_MODEL,
    }
    with _lock:
        records = _read()
        records.append(record)
        _write(records)
    return record


def update_book(doc_id: str, **fields: Any) -> dict | None:
    with _lock:
        records = _read()
        for record in records:
            if record["id"] == doc_id:
                record.update(fields)
                _write(records)
                return record
    return None


def remove_record(doc_id: str) -> None:
    with _lock:
        _write([b for b in _read() if b["id"] != doc_id])


def delete_book(vectorstore: Chroma, doc_id: str) -> None:
    """Remove one book's chunks and its registry record, nothing else.

    The record is only removed after the chunks are gone, so a failure here
    never leaves orphaned vectors that the library can no longer see.
    """
    delete_chunks(vectorstore, doc_id)
    remove_record(doc_id)


def recover_interrupted(vectorstore: Chroma) -> int:
    """Mark books left in 'uploaded'/'processing' (e.g. after a crash) as failed
    and clear any partial chunks they wrote. Call once at application start."""
    recovered = 0
    for book in list_books():
        if book["status"] in (STATUS_UPLOADED, STATUS_PROCESSING):
            try:
                delete_chunks(vectorstore, book["id"])
            except Exception as exc:  # best effort
                logger.error("Could not clear partial chunks: %s", type(exc).__name__)
            update_book(
                book["id"],
                status=STATUS_FAILED,
                chunks=0,
                error="Processing was interrupted. Upload the book again to retry.",
            )
            recovered += 1
    return recovered