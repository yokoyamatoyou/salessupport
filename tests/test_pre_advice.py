import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).resolve().parents[1] / "app"))
from pages.pre_advice import (
    render_form,
    process_form_data,
    validate_input,
    display_result,
)
import pages.pre_advice as pre_advice
from core.models import SalesType, SalesInput


def test_step_progression(monkeypatch):
    st.session_state.clear()
    st.session_state.pre_form_step = 1
    monkeypatch.setattr(st, "rerun", lambda: None)

    def fake_submit(label, **kwargs):
        return True

    monkeypatch.setattr(st, "form_submit_button", fake_submit)
    render_form()
    assert st.session_state.pre_form_step == 2


def test_step_titles_and_progress(monkeypatch):
    st.session_state.clear()
    st.session_state.pre_form_step = 1
    monkeypatch.setattr(st, "rerun", lambda: None)

    progress_calls = []
    markdown_calls = []

    monkeypatch.setattr(st, "progress", lambda v: progress_calls.append(v))
    monkeypatch.setattr(st, "markdown", lambda text, **kwargs: markdown_calls.append(text))

    responses = iter([True, False, True, False, False])

    def fake_submit(label, **kwargs):
        return next(responses)

    monkeypatch.setattr(st, "form_submit_button", fake_submit)

    render_form()
    assert progress_calls[-1] == 1 / 3
    assert any("基本情報" in m for m in markdown_calls)

    progress_calls.clear()
    markdown_calls.clear()
    render_form()
    assert progress_calls[-1] == 2 / 3
    assert any("詳細" in m for m in markdown_calls)

    progress_calls.clear()
    markdown_calls.clear()
    render_form()
    assert progress_calls[-1] == 1
    assert any("制約" in m for m in markdown_calls)


def test_final_submission(monkeypatch):
    st.session_state.clear()
    st.session_state.pre_form_step = 3
    st.session_state.sales_type_select = SalesType.HUNTER
    st.session_state.industry_input = "IT"
    st.session_state.product_input = "SaaS"
    st.session_state.description_text = "desc"
    st.session_state.competitor_text = "comp"
    st.session_state.stage_select = "初期接触"
    st.session_state.purpose_input = "新規顧客獲得"
    st.session_state.constraints_input = "予算"

    def fake_submit(label, **kwargs):
        return label == "🚀 アドバイスを生成"

    monkeypatch.setattr(st, "form_submit_button", fake_submit)
    submitted, data = render_form()
    assert submitted is True
    assert data["industry"] == "IT"


def test_process_and_validate(monkeypatch):
    st.session_state.clear()
    st.session_state.quickstart_mode = False
    form_data = {
        "sales_type": SalesType.HUNTER,
        "industry": "IT",
        "product": "SaaS",
        "description": "desc",
        "description_url": None,
        "competitor": "comp",
        "competitor_url": None,
        "stage": "初期接触",
        "purpose": "新規顧客獲得",
        "constraints_input": "予算制限\n期間延長",
    }
    sales_input = process_form_data(form_data)
    assert sales_input.constraints == ["予算制限", "期間延長"]
    assert validate_input(sales_input) == []

    invalid = SalesInput(
        sales_type=SalesType.HUNTER,
        industry="IT",
        product="SaaS",
        description=None,
        description_url=None,
        competitor=None,
        competitor_url=None,
        stage="初期接触",
        purpose="",
        constraints=[],
    )
    assert validate_input(invalid)


def test_display_result_calls(monkeypatch):
    st.session_state.clear()
    st.session_state.selected_icebreaker = "hello"
    st.session_state.icebreak_last_news = [{"title": "t", "url": "u", "source": "web"}]

    called = {}

    def fake_display_advice(advice):
        called["display_advice"] = True

    def fake_save(si, adv):
        called["save"] = (si, adv)

    markdown_calls = []
    monkeypatch.setattr(st, "markdown", lambda text, **kwargs: markdown_calls.append(text))
    monkeypatch.setattr(pre_advice, "display_advice", fake_display_advice)
    monkeypatch.setattr(pre_advice, "render_save_section", fake_save)

    si = SalesInput(
        sales_type=SalesType.HUNTER,
        industry="IT",
        product="SaaS",
        description=None,
        description_url=None,
        competitor=None,
        competitor_url=None,
        stage="初期接触",
        purpose="新規顧客獲得",
        constraints=[],
    )
    display_result({}, si)
    assert called["display_advice"] is True
    assert called["save"] == (si, {})
    assert any("hello" in m for m in markdown_calls)

