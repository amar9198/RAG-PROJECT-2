"""BookMind AI: Your Personal AI Book Assistant (Streamlit UI).

Run with:  streamlit run app.py
"""

from __future__ import annotations

import html
from dataclasses import asdict
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import database as db  # noqa: E402
import rag_pipeline as rag  # noqa: E402

st.set_page_config(
    page_title="BookMind AI",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAV = ["Dashboard", "Upload a Book", "Chat with Your Book", "Document Library", "Settings"]
NAV_ICONS = {
    "Dashboard": "🏠",
    "Upload a Book": "📤",
    "Chat with Your Book": "💬",
    "Document Library": "📚",
    "Settings": "⚙️",
}

STATUS_LABELS = {
    db.STATUS_UPLOADED: ("Uploaded", "bm-badge-grey"),
    db.STATUS_PROCESSING: ("Processing", "bm-badge-amber"),
    db.STATUS_INDEXED: ("Indexed", "bm-badge-green"),
    db.STATUS_FAILED: ("Failed", "bm-badge-red"),
}

CSS = """



<style>
:root {
    --pink-bg: #FFF1F5;
    --pink-soft: #FCE7F0;
    --pink: #DB5A87;
    --pink-hover: #BE426F;
    --plum: #6D214F;
    --muted: #79566A;
    --white: #FFFFFF;
    --border: #EBD3DE;
}

/* Main page */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--pink-bg) !important;
    color: var(--plum) !important;
}

.block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Headings and content */
.stApp h1,
.stApp h2,
.stApp h3,
.stApp p,
.stApp label,
.stApp [data-testid="stMarkdownContainer"] {
    color: var(--plum);
}

.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] p {
    color: var(--muted) !important;
}

/* Sidebar */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background: var(--plum) !important;
}

section[data-testid="stSidebar"] .bm-brand,
section[data-testid="stSidebar"] .bm-side-value {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] .bm-tagline,
section[data-testid="stSidebar"] .bm-side-label {
    color: #F9DDE9 !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label,
section[data-testid="stSidebar"] [data-testid="stRadio"] label p,
section[data-testid="stSidebar"] [data-testid="stRadio"] label span {
    color: #FFFFFF !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #873761 !important;
    border-radius: 9px;
}

/* Hero banner */
.bm-hero {
    background: linear-gradient(120deg, #6D214F, #B84276) !important;
    border-radius: 18px;
    padding: 2rem;
    margin-bottom: 1.3rem;
}

.bm-hero h1 {
    color: #FFFFFF !important;
}

.bm-hero p {
    color: #FFEAF2 !important;
}

/* White cards */
.bm-card,
.bm-empty,
[data-testid="stChatMessage"] {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    box-shadow: 0 3px 12px rgba(109, 33, 79, 0.05);
}

.bm-card-label,
.bm-meta {
    color: var(--muted) !important;
}

.bm-card-value,
.bm-book-title,
.bm-empty b {
    color: var(--plum) !important;
}

.bm-empty {
    padding: 2rem;
    text-align: center;
    color: var(--muted) !important;
}

/* Chat responses */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    color: var(--plum) !important;
}

/* Upload area */
[data-testid="stFileUploaderDropzone"] {
    background: #FFFFFF !important;
    border: 2px dashed #D987A9 !important;
    border-radius: 14px !important;
}

[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span {
    color: var(--plum) !important;
}

[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploader"] button {
    background: var(--pink) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--pink) !important;
    border-radius: 9px !important;
}

[data-testid="stFileUploaderDropzone"] button *,
[data-testid="stFileUploader"] button * {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}

/* Text fields and dropdowns */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    color: var(--plum) !important;
    -webkit-text-fill-color: var(--plum) !important;
    border-color: #D9B8C8 !important;
}

[data-testid="stChatInput"],
[data-testid="stChatInput"] > div {
    background: #FFFFFF !important;
    border: 1px solid #D9B8C8 !important;
    border-radius: 13px !important;
}

[data-testid="stChatInput"] textarea {
    color: var(--plum) !important;
    -webkit-text-fill-color: var(--plum) !important;
    caret-color: var(--pink) !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #896C7C !important;
    -webkit-text-fill-color: #896C7C !important;
    opacity: 1 !important;
}

/* Buttons */
.stButton > button,
.stFormSubmitButton > button {
    background: var(--pink) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--pink) !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
}

.stButton > button *,
.stFormSubmitButton > button * {
    color: #FFFFFF !important;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: var(--pink-hover) !important;
    border-color: var(--pink-hover) !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {
    color: var(--plum) !important;
}

/* Status badges */
.bm-badge-green { background: #DCFCE7; color: #166534 !important; }
.bm-badge-amber { background: #FEF3C7; color: #92400E !important; }
.bm-badge-red { background: #FEE2E2; color: #991B1B !important; }
.bm-badge-grey { background: #F1E8ED; color: #624456 !important; }
.bm-badge-blue { background: #FCE7F0; color: #8A2457 !important; }

@media (max-width: 640px) {
    .block-container { padding: 1rem 0.75rem 2rem; }
    .bm-hero { padding: 1.3rem; }
}
</style>

"""
st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def esc(value) -> str:
    return html.escape(str(value))


def fmt_size(num_bytes: int | None) -> str:
    if not num_bytes:
        return "n/a"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def fmt_date(iso: str | None) -> str:
    if not iso:
        return "n/a"
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y, %H:%M UTC")
    except ValueError:
        return iso


def status_badge(status: str) -> str:
    label, css = STATUS_LABELS.get(status, (status.title(), "bm-badge-grey"))
    return f'<span class="bm-badge {css}">{esc(label)}</span>'


def stat_card(label: str, value, small: bool = False) -> None:
    cls = "bm-card-value small" if small else "bm-card-value"
    st.markdown(
        f'<div class="bm-card"><div class="bm-card-label">{esc(label)}</div>'
        f'<div class="{cls}">{esc(value)}</div></div>',
        unsafe_allow_html=True,
    )


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f'<div class="bm-empty"><b>{esc(title)}</b><br>{esc(body)}</div>',
        unsafe_allow_html=True,
    )


def goto(page: str) -> None:
    st.session_state.nav = page


def select_book(doc_id: str, then_chat: bool = False) -> None:
    st.session_state.selected_book_id = doc_id
    if then_chat:
        st.session_state.nav = "Chat with Your Book"


def flash(kind: str, message: str) -> None:
    st.session_state.flash = (kind, message)


def show_flash() -> None:
    item = st.session_state.pop("flash", None)
    if item:
        kind, message = item
        getattr(st, kind)(message)


@st.cache_resource(show_spinner=False)
def get_vectorstore():
    vs = db.get_vectorstore()
    db.recover_interrupted(vs)
    return vs


@st.cache_resource(show_spinner=False)
def get_llm():
    return rag.get_llm()


@st.cache_data(show_spinner=False, max_entries=8)
def inspect_cached(data: bytes) -> dict:
    try:
        return {"pages": rag.inspect_pdf(data)["pages"], "error": None}
    except rag.BookMindError as exc:
        return {"pages": None, "error": str(exc)}


def selected_book() -> dict | None:
    book = db.get_book(st.session_state.selected_book_id)
    if book and book["status"] == db.STATUS_INDEXED:
        return book
    return None


def current_settings() -> rag.RAGSettings:
    return rag.RAGSettings(**st.session_state.settings)


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("nav", "Dashboard")
ss.setdefault("selected_book_id", None)
ss.setdefault("chats", {})  # doc_id -> list of messages (one history per book)
ss.setdefault("settings", asdict(rag.RAGSettings()))
ss.setdefault("confirm_delete", None)

MISSING_KEYS = rag.missing_api_keys()
READY = not MISSING_KEYS


def keys_banner() -> None:
    if MISSING_KEYS:
        st.error(
            "Missing API key(s): "
            + ", ".join(MISSING_KEYS)
            + ". Add them to a `.env` file next to `app.py` (see `.env.example`) and restart the app."
        )


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="bm-brand">📘 BookMind AI</div>'
        '<div class="bm-tagline">Your Personal AI Book Assistant</div>',
        unsafe_allow_html=True,
    )
    st.radio(
        "Navigation",
        NAV,
        key="nav",
        format_func=lambda page: f"{NAV_ICONS[page]}  {page}",
        label_visibility="collapsed",
    )
    st.divider()

    active = selected_book()
    st.markdown(
        '<div class="bm-side-label">Selected book</div>'
        f'<div class="bm-side-value">{esc(active["filename"]) if active else "None selected"}</div>',
        unsafe_allow_html=True,
    )

    if not READY:
        db_status = "🔴 API keys missing"
    else:
        try:
            db_status = f"🟢 Ready ({db.count_vectors(get_vectorstore()):,} chunks stored)"
        except Exception:
            db_status = "🔴 Unavailable"
    st.markdown(
        '<div class="bm-side-label">Vector database</div>'
        f'<div class="bm-side-value">{esc(db_status)}</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def page_dashboard() -> None:
    books = db.list_books()
    indexed = [b for b in books if b["status"] == db.STATUS_INDEXED]
    active = selected_book()

    st.markdown(
        '<div class="bm-hero"><h1>Your Personal AI Book Assistant</h1>'
        "<p>Welcome to BookMind AI. Upload a book, explore its knowledge, and get answers in seconds.</p></div>",
        unsafe_allow_html=True,
    )
    st.button("Upload a new PDF book", type="primary", on_click=goto, args=("Upload a Book",))
    st.write("")

    c1, c2, c3 = st.columns(3)
    with c1:
        stat_card("Uploaded books", len(books))
    with c2:
        stat_card("Processed documents", len(indexed))
    with c3:
        stat_card("Indexed text chunks", f"{sum(b.get('chunks', 0) for b in indexed):,}")

    c4, c5, c6 = st.columns(3)
    with c4:
        stat_card("Current selected book", active["filename"] if active else "None", small=True)
    with c5:
        stat_card("Embedding model", db.EMBEDDING_MODEL, small=True)
    with c6:
        stat_card("LLM model", rag.LLM_MODEL, small=True)

    if not books:
        empty_state("Your library is empty", "Upload a PDF to get started.")


def chunking_controls() -> None:
    cfg = st.session_state.settings
    c1, c2 = st.columns(2)
    with c1:
        cfg["chunk_size"] = st.number_input(
            "Chunk size (characters)",
            min_value=200,
            max_value=4000,
            value=int(cfg["chunk_size"]),
            step=100,
            help="How much text goes into each searchable chunk. Applies to books processed from now on.",
        )
    with c2:
        overlap = min(int(cfg["chunk_overlap"]), int(cfg["chunk_size"]) - 1)
        cfg["chunk_overlap"] = st.number_input(
            "Chunk overlap (characters)",
            min_value=0,
            max_value=int(cfg["chunk_size"]) - 1,
            value=overlap,
            step=50,
            help="Characters shared between neighbouring chunks so ideas aren't cut in half.",
        )


def page_upload() -> None:
    st.title("Upload a Book")
    keys_banner()
    st.caption(f"PDF files only, up to {rag.MAX_FILE_MB} MB. The PDF needs selectable text (not a scan).")

    uploaded = st.file_uploader(
        "Choose a PDF",
        type=["pdf"],
        disabled=not READY,
        help="Your book is split into chunks and indexed so you can chat with it.",
    )
    with st.expander("Chunking options"):
        chunking_controls()

    if uploaded is None:
        empty_state("No book selected", "Choose a PDF above, then select Process Book.")
        return

    data = uploaded.getvalue()
    info = inspect_cached(data)
    problem = info["error"]
    if not problem:
        try:
            rag.validate_upload(uploaded.name, data)
        except rag.BookMindError as exc:
            problem = str(exc)

    c1, c2, c3 = st.columns(3)
    with c1:
        stat_card("Filename", uploaded.name, small=True)
    with c2:
        stat_card("File size", fmt_size(len(data)), small=True)
    with c3:
        stat_card("Pages", info["pages"] if info["pages"] else "n/a", small=True)

    existing = None
    if problem:
        st.error(problem)
    else:
        existing = db.find_by_hash(rag.sha256_of(data))
        if existing and existing["status"] == db.STATUS_INDEXED:
            st.info(f"'{existing['filename']}' is already in your library, so it won't be indexed twice.")
            st.button(
                "Chat with this book",
                on_click=select_book,
                args=(existing["id"], True),
                key="dup_chat",
            )

    already_done = bool(existing and existing["status"] == db.STATUS_INDEXED)
    if st.button("Process Book", type="primary", disabled=bool(problem) or already_done or not READY):
        bar = st.progress(0.0, text="Starting...")

        def on_progress(fraction: float, message: str) -> None:
            bar.progress(min(max(fraction, 0.0), 1.0), text=message)

        try:
            result = rag.process_book(
                get_vectorstore(), uploaded.name, data, current_settings(), on_progress
            )
        except rag.DuplicateBookError as exc:
            bar.empty()
            st.warning(str(exc))
        except Exception as exc:
            bar.empty()
            st.error(rag.friendly_error(exc))
        else:
            bar.empty()
            book = result["book"]
            ss.selected_book_id = book["id"]
            st.success(
                f"'{book['filename']}' is indexed: {book['pages']} pages, {book['chunks']:,} chunks. "
                "It is now your selected book."
            )
            for warning in result["warnings"]:
                st.warning(warning)
            st.button("Start chatting", type="primary", on_click=goto, args=("Chat with Your Book",))


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for src in sources:
            page = f"page {src['page']}" if src.get("page") else "page unknown"
            st.markdown(f"**{src['filename']}**, {page}")
            st.caption(src["snippet"])


def page_chat() -> None:
    st.title("Chat with Your Book")
    keys_banner()
    if not READY:
        return

    indexed = [b for b in db.list_books() if b["status"] == db.STATUS_INDEXED]
    if not indexed:
        empty_state("No indexed books yet", "Upload and process a PDF, then come back to ask questions.")
        st.button("Upload a Book", type="primary", on_click=goto, args=("Upload a Book",))
        return

    ids = [b["id"] for b in indexed]
    names = {b["id"]: b["filename"] for b in indexed}
    current = ss.selected_book_id if ss.selected_book_id in ids else ids[0]

    left, right = st.columns([4, 1])
    with left:
        doc_id = st.selectbox(
            "Active book",
            ids,
            index=ids.index(current),
            format_func=lambda i: names[i],
            help="Answers come only from this book. Each book keeps its own conversation.",
        )
    ss.selected_book_id = doc_id
    history = ss.chats.setdefault(doc_id, [])
    with right:
        st.write("")
        st.write("")
        st.button(
            "Clear chat",
            disabled=not history,
            on_click=lambda: ss.chats.__setitem__(doc_id, []),
            help="Remove the messages in this conversation.",
        )

    if not history:
        empty_state(
            f"Ask anything about {names[doc_id]}",
            "Answers use only the text of this book, with the pages they came from.",
        )

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            render_sources(msg.get("sources", []))

    question = st.chat_input("Ask a question about your book...")
    if not question:
        return

    history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        sources: list[dict] = []
        with st.spinner("Searching the book and writing an answer..."):
            try:
                answer, docs = rag.answer_question(
                    get_vectorstore(), get_llm(), doc_id, question, current_settings()
                )
                if answer.strip() != rag.NOT_FOUND_ANSWER:
                    sources = rag.describe_sources(docs)
            except Exception as exc:
                answer = rag.friendly_error(exc)
        st.markdown(answer)
        render_sources(sources)
    history.append({"role": "assistant", "content": answer, "sources": sources})


def delete_book_now(book: dict) -> None:
    try:
        db.delete_book(get_vectorstore(), book["id"])
    except Exception as exc:
        flash("error", f"Could not delete '{book['filename']}': {rag.friendly_error(exc)}")
    else:
        ss.chats.pop(book["id"], None)
        if ss.selected_book_id == book["id"]:
            ss.selected_book_id = None
        flash("success", f"Deleted '{book['filename']}'. Your other books were not touched.")
    ss.confirm_delete = None


def page_library() -> None:
    st.title("Document Library")
    keys_banner()
    books = db.list_books()
    if not books:
        empty_state("No books yet", "Books you upload will appear here.")
        st.button("Upload a Book", type="primary", on_click=goto, args=("Upload a Book",))
        return

    for book in books:
        is_active = book["id"] == ss.selected_book_id and book["status"] == db.STATUS_INDEXED
        with st.container(border=True):
            info_col, action_col = st.columns([3, 1])
            with info_col:
                active_badge = '<span class="bm-badge bm-badge-blue">Selected</span>' if is_active else ""
                chunk_text = f"{book.get('chunks', 0):,}"
                st.markdown(
                    f'<div class="bm-book-title">{esc(book["filename"])}'
                    f'{status_badge(book["status"])}{active_badge}</div>'
                    f'<div class="bm-meta">Size: {esc(fmt_size(book.get("size_bytes")))} &nbsp;|&nbsp; '
                    f'Pages: {esc(book.get("pages") or "n/a")} &nbsp;|&nbsp; '
                    f'Chunks: {esc(chunk_text)} &nbsp;|&nbsp; '
                    f'Uploaded: {esc(fmt_date(book.get("uploaded_at")))}</div>',
                    unsafe_allow_html=True,
                )
                if book["status"] == db.STATUS_FAILED and book.get("error"):
                    st.error(book["error"])
            with action_col:
                st.button(
                    "Select" if not is_active else "Selected",
                    key=f"select_{book['id']}",
                    disabled=book["status"] != db.STATUS_INDEXED or is_active,
                    on_click=select_book,
                    args=(book["id"],),
                    use_container_width=True,
                )
                if st.button(
                    "Delete",
                    key=f"delete_{book['id']}",
                    disabled=not READY,
                    use_container_width=True,
                    help="Remove this book and its indexed chunks." if READY else "Add your API keys to manage books.",
                ):
                    ss.confirm_delete = book["id"]

            if ss.confirm_delete == book["id"]:
                st.warning(
                    f"Delete '{book['filename']}'? Its indexed chunks and library entry will be removed. "
                    "This can't be undone, and no other book is affected."
                )
                yes, no, _ = st.columns([1, 1, 3])
                with yes:
                    st.button(
                        "Yes, delete",
                        type="primary",
                        key=f"confirm_{book['id']}",
                        on_click=delete_book_now,
                        args=(book,),
                    )
                with no:
                    st.button(
                        "Cancel",
                        key=f"cancel_{book['id']}",
                        on_click=lambda: ss.__setitem__("confirm_delete", None),
                    )


def reset_settings() -> None:
    ss.settings = asdict(rag.RAGSettings())


def page_settings() -> None:
    st.title("Settings")
    keys_banner()
    cfg = ss.settings

    st.subheader("Chunking")
    chunking_controls()

    st.subheader("Retrieval")
    c1, c2, c3 = st.columns(3)
    with c1:
        cfg["k"] = st.number_input(
            "Passages used (k)", min_value=1, max_value=20, value=int(cfg["k"]),
            help="How many passages are sent to the model as context.",
        )
    with c2:
        cfg["fetch_k"] = st.number_input(
            "Candidates considered (fetch_k)", min_value=int(cfg["k"]), max_value=100,
            value=max(int(cfg["fetch_k"]), int(cfg["k"])),
            help="How many passages are fetched before MMR picks the final set. Must be at least k.",
        )
    with c3:
        cfg["lambda_mult"] = st.slider(
            "Diversity (lambda_mult)", 0.0, 1.0, float(cfg["lambda_mult"]), 0.05,
            help="0 favours variety across passages, 1 favours the closest matches.",
        )
    st.button("Reset to defaults", on_click=reset_settings)

    st.subheader("Models")
    c1, c2 = st.columns(2)
    with c1:
        stat_card("Embedding model", db.EMBEDDING_MODEL, small=True)
    with c2:
        stat_card("LLM model (temperature 0)", rag.LLM_MODEL, small=True)

    st.subheader("API keys")
    for name in rag.REQUIRED_KEYS:
        (st.success if name not in MISSING_KEYS else st.error)(
            f"{name}: {'configured' if name not in MISSING_KEYS else 'missing'}"
        )
    st.caption("Keys are read from your `.env` file and are never shown in the app.")


# --------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------
show_flash()
{
    "Dashboard": page_dashboard,
    "Upload a Book": page_upload,
    "Chat with Your Book": page_chat,
    "Document Library": page_library,
    "Settings": page_settings,
}[ss.nav]()