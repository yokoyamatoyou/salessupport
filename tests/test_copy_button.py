import sys
from pathlib import Path
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1] / "app"))
from components.copy_button import copy_button

def test_copy_button_renders(monkeypatch):
    called = {}
    monkeypatch.setattr(st, "button", lambda *args, **kwargs: True)
    import components.copy_button as cb
    monkeypatch.setattr(cb, "st_javascript", lambda code, **kwargs: called.setdefault("code", code))
    messages = []
    monkeypatch.setattr(st, "success", lambda msg: messages.append(msg))

    copy_button("hello", key="test")

    assert "navigator.clipboard.writeText" in called["code"]
    assert any("コピー" in m for m in messages)
