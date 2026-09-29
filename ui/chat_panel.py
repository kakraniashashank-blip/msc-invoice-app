"""
Chat panel — center panel for conversational Q&A with source citations.
"""
import streamlit as st
from chat.engine import ChatEngine


def render_chat_panel(chat_engine: ChatEngine):
    """Render the center panel: chat messages with streaming and citations."""

    active_ws = st.session_state.get("active_workspace", "")

    st.subheader("💬 Research Chat")

    if not active_ws:
        st.info("👈 Create or select a workspace to start chatting.")
        return

    # Check if workspace has any data
    try:
        stats = chat_engine.store.get_workspace_stats(active_ws)
        if stats["chunk_count"] == 0:
            st.info("📥 Add some sources first, then ask questions about them.")
            return
    except Exception:
        st.info("📥 Add some sources first, then ask questions about them.")
        return

    st.caption(f"Workspace: **{active_ws}**")

    # ── Initialize chat history ───────────────────────────────
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # If workspace changed, clear chat
    if st.session_state.get("chat_workspace") != active_ws:
        st.session_state["messages"] = []
        st.session_state["chat_workspace"] = active_ws

    # ── Render chat history ───────────────────────────────────
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Show sources for assistant messages
            if msg["role"] == "assistant" and msg.get("sources"):
                _render_sources(msg["sources"])

    # ── Chat input ────────────────────────────────────────────
    is_generating = st.session_state.get("is_generating", False)

    if prompt := st.chat_input(
        "Ask a question about your documents...",
        disabled=is_generating,
    ):
        # Add user message
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        st.session_state["is_generating"] = True

        with st.chat_message("assistant"):
            # Build chat history for context (exclude sources from history sent to LLM)
            chat_history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state["messages"][:-1]  # exclude current question
            ]

            try:
                stream_fn, sources = chat_engine.ask_with_sources(
                    question=prompt,
                    workspace=active_ws,
                    chat_history=chat_history,
                )

                # Stream the response
                full_response = st.write_stream(stream_fn())

                # Show sources
                _render_sources(sources)

            except Exception as e:
                full_response = f"⚠️ Error: {e}"
                sources = []
                st.error(full_response)

        # Save assistant message
        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": full_response,
                "sources": sources,
            }
        )
        st.session_state["is_generating"] = False

    # ── Clear chat button ─────────────────────────────────────
    if st.session_state["messages"]:
        if st.button("🗑️ Clear chat", key="clear_chat"):
            st.session_state["messages"] = []
            st.rerun()


def _render_sources(sources: list[dict]):
    """Render source citation cards in an expander."""
    if not sources:
        return

    with st.expander(f"📚 Sources Referenced ({len(sources)})"):
        for i, src in enumerate(sources, 1):
            title = src.get("doc_title", "Unknown")
            page = src.get("page", "N/A")
            url = src.get("source_url", "")
            snippet = src.get("text", "")

            # Truncate snippet for display
            display_snippet = snippet[:300] + "..." if len(snippet) > 300 else snippet

            st.markdown(
                f"**[{i}] {title}** (Page {page})"
            )
            if url:
                st.caption(f"🔗 {url}")
            st.markdown(
                f"> {display_snippet}",
            )
            if i < len(sources):
                st.markdown("---")
