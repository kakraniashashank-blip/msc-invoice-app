"""
Notes panel — right sidebar for research scratchpad.
"""
import streamlit as st


def render_notes_panel():
    """Render the right panel: simple scratchpad for research notes."""

    st.subheader("📝 Notes")

    active_ws = st.session_state.get("active_workspace", "")

    if not active_ws:
        st.info("Select a workspace to start taking notes.")
        return

    # Per-workspace notes stored in session state
    notes_key = f"notes_{active_ws}"
    if notes_key not in st.session_state:
        st.session_state[notes_key] = ""

    notes = st.text_area(
        "Research scratchpad",
        value=st.session_state[notes_key],
        height=450,
        placeholder="Jot down key takeaways, draft outlines, or save important findings here...",
        key=f"notes_input_{active_ws}",
        label_visibility="collapsed",
    )

    # Save notes back to session state
    st.session_state[notes_key] = notes

    st.caption("Notes are saved for this session.")
