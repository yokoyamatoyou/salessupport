"""Streamlit component for copying text to the clipboard."""

import json
import streamlit as st
from streamlit_javascript import st_javascript


def copy_button(
    text: str,
    *,
    key: str | None = None,
    label: str = "📋 コピー",
    use_container_width: bool = False,
) -> None:
    """Render a button that copies text to the clipboard using ``st_javascript``.

    Using ``st_javascript`` avoids injecting raw HTML and sanitises the input via
    ``json.dumps`` before sending it to the browser clipboard API.
    """

    if st.button(label, key=key, use_container_width=use_container_width):
        escaped = json.dumps(text)
        st_javascript(f"navigator.clipboard.writeText({escaped});")
        st.success("✅ クリップボードにコピーしました")

