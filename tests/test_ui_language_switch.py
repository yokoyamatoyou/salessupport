import streamlit as st
from pathlib import Path
from services.settings_manager import SettingsManager
from app import translations


def test_language_switch_persists(tmp_path, monkeypatch):
    config_file = tmp_path / "config" / "settings.json"
    manager = SettingsManager(str(config_file))
    monkeypatch.setattr(translations, "SettingsManager", lambda: manager)

    st.session_state.clear()
    assert translations.get_language() == "ja"

    st.session_state["language"] = "en"
    manager.update_setting("language", "en")
    assert translations.t("menu") == "Menu"

    st.session_state.clear()
    assert translations.get_language() == "en"
    assert translations.t("menu") == "Menu"
