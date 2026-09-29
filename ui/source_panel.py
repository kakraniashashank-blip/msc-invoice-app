"""
Source panel — left sidebar for URL input, link review, file upload, and source management.
"""
import streamlit as st
from crawler.scraper import scrape_seed_url
from crawler.classifier import classify_links
from crawler.fetcher import fetch_documents
from processing.extractor import extract_document
from processing.chunker import chunk_documents
from knowledge.embeddings import embed_documents


# Category display config
CATEGORY_ICONS = {
    "FINANCIAL_REPORT": "📊",
    "EARNINGS_TRANSCRIPT": "🎙️",
    "PRESS_RELEASE": "📰",
    "REGULATORY_FILING": "📋",
    "OTHER_RELEVANT": "📄",
    "IRRELEVANT": "🚫",
}


def render_source_panel(gemini_client, api_key: str, store):
    """Render the left panel: source ingestion and management."""

    st.subheader("📁 Sources")

    # ── Workspace selector ────────────────────────────────────
    workspaces = store.list_workspaces()
    if workspaces:
        options = workspaces + ["+ New workspace"]
        choice = st.selectbox("Workspace", options, key="ws_select")
        if choice == "+ New workspace":
            new_name = st.text_input("Workspace name", key="new_ws_name")
            if new_name:
                st.session_state["active_workspace"] = new_name
        else:
            st.session_state["active_workspace"] = choice
    else:
        new_name = st.text_input(
            "Workspace name", value="my-research", key="new_ws_name"
        )
        st.session_state["active_workspace"] = new_name

    active_ws = st.session_state.get("active_workspace", "")
    if not active_ws:
        st.info("Enter a workspace name to get started.")
        return

    # Show workspace stats if it exists
    if active_ws in workspaces:
        try:
            stats = store.get_workspace_stats(active_ws)
            st.caption(
                f"📚 {stats['doc_count']} docs · {stats['chunk_count']} chunks"
            )
        except Exception:
            pass

    st.markdown("---")

    # ── Seed URL input ────────────────────────────────────────
    st.markdown("**🌐 Add from URL**")
    seed_url = st.text_input(
        "Seed URL",
        placeholder="https://example.com/investor-relations",
        key="seed_url",
        label_visibility="collapsed",
    )

    if st.button("🔍 Discover Links", use_container_width=True, disabled=not seed_url):
        with st.spinner("Scanning page for links..."):
            links = scrape_seed_url(seed_url)

        if not links:
            st.warning("No links found on that page.")
        else:
            with st.spinner(f"Classifying {len(links)} links with AI..."):
                classified = classify_links(links, seed_url, api_key)
            st.session_state["discovered_links"] = classified
            st.session_state["link_source_url"] = seed_url

    # ── Link review & confirmation ────────────────────────────
    if "discovered_links" in st.session_state:
        links = st.session_state["discovered_links"]
        st.markdown(f"**Found {len(links)} links**")

        # Group by category
        categories = {}
        for link in links:
            cat = link.get("category", "OTHER_RELEVANT")
            categories.setdefault(cat, []).append(link)

        # Render checkboxes grouped by category
        selected_urls = []
        for cat in [
            "FINANCIAL_REPORT",
            "EARNINGS_TRANSCRIPT",
            "PRESS_RELEASE",
            "REGULATORY_FILING",
            "OTHER_RELEVANT",
            "IRRELEVANT",
        ]:
            if cat not in categories:
                continue
            cat_links = categories[cat]
            icon = CATEGORY_ICONS.get(cat, "📄")
            default_open = cat != "IRRELEVANT"

            with st.expander(
                f"{icon} {cat.replace('_', ' ').title()} ({len(cat_links)})",
                expanded=default_open,
            ):
                for i, link in enumerate(cat_links):
                    default_checked = link.get("recommended", False)
                    key = f"link_{cat}_{i}"
                    checked = st.checkbox(
                        f"{link.get('anchor_text', link['url'])[:80]}",
                        value=default_checked,
                        key=key,
                        help=f"{link.get('reason', '')} | {link['url']}",
                    )
                    if checked:
                        selected_urls.append(link["url"])

        st.caption(f"✅ {len(selected_urls)} selected")

        if st.button(
            "📥 Fetch & Index Selected",
            use_container_width=True,
            type="primary",
            disabled=len(selected_urls) == 0,
        ):
            _ingest_urls(selected_urls, gemini_client, store, active_ws)
            # Clear discovered links after ingestion
            del st.session_state["discovered_links"]
            st.rerun()

    st.markdown("---")

    # ── Direct PDF upload ─────────────────────────────────────
    st.markdown("**📄 Upload PDFs**")
    uploaded_files = st.file_uploader(
        "Upload documents",
        accept_multiple_files=True,
        type=["pdf"],
        key="pdf_upload",
        label_visibility="collapsed",
    )

    if uploaded_files and st.button(
        "📥 Index Uploads", use_container_width=True
    ):
        _ingest_uploads(uploaded_files, gemini_client, store, active_ws)
        st.rerun()

    # ── Workspace management ──────────────────────────────────
    st.markdown("---")
    if active_ws in workspaces:
        if st.button("🗑️ Delete workspace", use_container_width=True):
            store.delete_workspace(active_ws)
            if "active_workspace" in st.session_state:
                del st.session_state["active_workspace"]
            st.rerun()


def _ingest_urls(urls: list[str], gemini_client, store, workspace: str):
    """Fetch, extract, chunk, embed, and store documents from URLs."""
    progress = st.progress(0, text="Fetching documents...")

    def on_progress(done, total):
        progress.progress(done / total, text=f"Fetching {done}/{total}...")

    fetched = fetch_documents(urls, progress_callback=on_progress)
    successful = [doc for doc in fetched if doc.get("content") and not doc.get("error")]

    if not successful:
        st.error("Failed to fetch any documents.")
        return

    progress.progress(0.5, text="Extracting text...")

    # Extract text from all fetched docs
    all_extracted = []
    for doc in successful:
        extracted = extract_document(doc)
        all_extracted.extend(extracted)

    if not all_extracted:
        st.error("No text could be extracted from the fetched documents.")
        return

    progress.progress(0.6, text="Chunking documents...")
    chunks = chunk_documents(all_extracted)

    if not chunks:
        st.error("No chunks produced.")
        return

    progress.progress(0.7, text=f"Embedding {len(chunks)} chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = embed_documents(gemini_client, texts)

    progress.progress(0.9, text="Storing in knowledge base...")
    count = store.create_workspace(workspace, chunks, embeddings)

    progress.progress(1.0, text=f"✅ Indexed {count} chunks from {len(successful)} docs")
    st.success(f"Indexed **{count}** chunks from **{len(successful)}** documents.")


def _ingest_uploads(files, gemini_client, store, workspace: str):
    """Process uploaded PDF files."""
    progress = st.progress(0, text="Processing uploads...")

    all_extracted = []
    for i, f in enumerate(files):
        doc = {
            "content_type": "pdf",
            "content": f.getvalue(),
            "filename": f.name,
            "url": f.name,
        }
        extracted = extract_document(doc)
        all_extracted.extend(extracted)
        progress.progress((i + 1) / len(files) / 2, text=f"Extracted {f.name}")

    if not all_extracted:
        st.error("No text could be extracted.")
        return

    chunks = chunk_documents(all_extracted)
    progress.progress(0.6, text=f"Embedding {len(chunks)} chunks...")

    texts = [c["text"] for c in chunks]
    embeddings = embed_documents(gemini_client, texts)

    progress.progress(0.9, text="Storing...")
    count = store.create_workspace(workspace, chunks, embeddings)

    progress.progress(1.0, text="Done!")
    st.success(f"Indexed **{count}** chunks from **{len(files)}** uploads.")
