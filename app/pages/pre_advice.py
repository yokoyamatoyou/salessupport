"""Pre-advice page - Main entry point.

This module orchestrates the pre-advice generation workflow used in the
Streamlit application.  The original version of this file had become badly
corrupted which resulted in an ``IndentationError`` during import.  The tests
only rely on a small subset of the functionality (form handling utilities and
result display helpers), therefore this rewritten version focuses on providing
clean and well structured implementations of the page level helpers while
retaining the original behaviour.
"""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from core.logging_config import get_logger
from services.crm_importer import CRMImporter
from services.pre_advisor import PreAdvisorService
from services.settings_manager import SettingsManager
from translations import t

# Refactored sub modules which contain the detailed form and processing logic
from .pre_advice_forms import (
    render_form,
    render_sales_style_selection,
    render_simplified_form,
)
from .pre_advice_handlers import (
    apply_crm_data,
    process_form_data,
    process_simplified_form_data,
    update_form_data,
    validate_input,
)
from .pre_advice_storage import save_pre_advice
from .pre_advice_ui import display_result, display_advice, render_save_section

logger = get_logger(__name__)


def get_screen_width() -> int:
    """Return the cached screen width from the Streamlit session state."""

    return st.session_state.get("screen_width", 1000)


def show_pre_advice_page() -> None:
    """Render the pre-advice page in the Streamlit UI.

    The function offers two modes: a simplified wizard style input and the
    classic detailed form.  The implementation here mirrors the behaviour of
    the original module but is intentionally concise so that the test suite can
    import it without encountering syntax errors.
    """

    st.header("📝 事前アドバイス生成")
    st.write("営業スタイルに合わせた商談準備をサポートします")

    use_simplified = st.checkbox(
        "簡略モードを使用する",
        value=st.session_state.get("use_simplified_mode", True),
        help="営業スタイル診断と簡略化された入力フォームを使用します",
    )
    st.session_state.use_simplified_mode = use_simplified

    settings_manager = SettingsManager()
    settings = settings_manager.load_settings()

    # Optional CRM integration
    if settings.crm_enabled:
        with st.expander("CRM連携", expanded=False):
            crm_id = st.text_input("CRM顧客ID", key="crm_customer_id")
            if st.button("CRMから読み込む"):
                try:
                    importer = CRMImporter()
                    data = importer.fetch_customer(crm_id)
                    if data:
                        apply_crm_data(data)
                        st.success("CRMデータを読み込みました")
                        st.rerun()
                    else:
                        st.warning("CRMデータが見つかりません")
                except ConnectionError as e:  # pragma: no cover - network error
                    st.error("CRMサーバーに接続できません。ネットワーク接続を確認してください。")
                    logger.warning(f"CRM connection error: {e}")
                except ValueError as e:  # pragma: no cover - invalid format
                    st.error("CRM顧客IDの形式が正しくありません。")
                    logger.warning(f"CRM data validation error: {e}")
                except Exception as e:  # pragma: no cover - unexpected
                    st.error("CRM連携で予期しないエラーが発生しました。")
                    logger.error(f"CRM unexpected error: {e}", exc_info=True)

    is_mobile = get_screen_width() < 700

    if "pre_advice_form_data" not in st.session_state:
        st.session_state.pre_advice_form_data = {}

    if use_simplified:
        # --- Simplified mode -------------------------------------------------
        submitted, form_data = render_simplified_form()
        if submitted:
            if not form_data["industry"]:
                st.error("❌ 業界を入力してください")
                return
            if not form_data["product"]:
                st.error("❌ 商品・サービスを入力してください")
                return

            sales_input = process_simplified_form_data(form_data)

            try:
                progress_placeholder = st.empty()
                with progress_placeholder.container():
                    progress = st.progress(0)
                    status = st.empty()

                status.text("🔍 入力を検証中...")
                progress.progress(10)
                status.text("🤖 AI分析を開始...")
                progress.progress(30)
                status.text("📝 アドバイスを生成中...")
                progress.progress(60)

                service = PreAdvisorService(settings_manager)
                advice = service.generate_advice(sales_input)

                status.text("✨ 結果を整理中...")
                progress.progress(90)

                progress.progress(100)
                status.text("✅ 完了！")
                progress_placeholder.empty()

                st.success("✅ アドバイスの生成が完了しました！")
                display_result(advice, sales_input)
            except Exception as e:  # pragma: no cover - fallback handling
                progress_placeholder.empty()
                st.error(f"❌ アドバイスの生成に失敗しました: {e}")
                st.info("しばらく時間をおいて再度お試しください。")

        # Icebreaker section for simplified mode
        if is_mobile:
            with st.expander("❄️ アイスブレイク生成", expanded=False):
                render_icebreaker_section(settings_manager)
        else:
            render_icebreaker_section(settings_manager)

    else:
        # --- Classic mode ----------------------------------------------------
        if is_mobile:
            tab_form, tab_ice = st.tabs(["入力フォーム", "アイスブレイク"])
            with tab_form:
                submitted, form_data = render_form()
            with tab_ice:
                render_icebreaker_section(settings_manager)
        else:
            submitted, form_data = render_form()
            render_icebreaker_section(settings_manager)

        autorun = st.session_state.pop("pre_advice_autorun", False)
        if submitted or autorun:
            sales_input = process_form_data(form_data)
            errors = validate_input(sales_input)
            if errors:
                st.error("❌ 入力内容に問題があります。以下を確認してください：")
                for error in errors:
                    st.error(f"• {error}")
                return
            try:
                with st.spinner("🤖 AIがアドバイスを生成中..."):
                    service = PreAdvisorService(settings_manager)
                    advice = service.generate_advice(sales_input)
                st.success("✅ アドバイスの生成が完了しました！")
                display_result(advice, sales_input)
            except ConnectionError as e:  # pragma: no cover - network error
                st.error("❌ サーバーに接続できません。ネットワーク接続を確認してください。")
                logger.error(f"API connection error: {e}")
            except ValueError as e:  # pragma: no cover - validation
                st.error("❌ 入力データに問題があります。内容を確認してください。")
                logger.warning(f"Input validation error: {e}")
            except Exception as e:  # pragma: no cover - unexpected
                st.error("❌ アドバイスの生成に失敗しました。しばらく時間をおいて再度お試しください。")
                logger.error(f"Advice generation unexpected error: {e}", exc_info=True)


def render_icebreaker_section(settings_manager: SettingsManager) -> None:
    """Display the optional icebreaker generation section."""

    from services.icebreaker import IcebreakerService

    st.markdown("---")
    st.markdown("### ❄️ アイスブレイク生成（任意）")

    if get_screen_width() < 800:
        ib_col1, ib_col2, ib_col3 = st.columns([1, 1, 1])
    else:
        ib_col1, ib_col2, ib_col3 = st.columns([2, 1, 1])

    with ib_col1:
        st.text_input(
            "会社ヒント",
            placeholder="例: 大手企業、最近M&Aあり、採用強化中 など",
            help="相手企業に関するヒントがあれば入力してください",
            key="company_hint_input",
        )
    with ib_col2:
        st.checkbox(
            "業界ニュースを使用",
            value=True,
            key="use_news_checkbox",
        )
    with ib_col3:
        generate_icebreak = st.button(
            "❄️ アイスブレイクを生成", use_container_width=True, type="primary"
        )

    if "icebreakers" not in st.session_state:
        st.session_state.icebreakers = []
    if "selected_icebreaker" not in st.session_state:
        st.session_state.selected_icebreaker = None

    sales_type_val = st.session_state.pre_advice_form_data.get("sales_type")
    industry_val = st.session_state.pre_advice_form_data.get("industry")

    if sales_type_val and industry_val and generate_icebreak:
        try:
            service = IcebreakerService(settings_manager)
            with st.spinner("❄️ アイスブレイク生成中..."):
                st.session_state.icebreakers = service.generate_icebreakers(
                    sales_type=sales_type_val,
                    industry=industry_val,
                    company_hint=st.session_state.pre_advice_form_data.get("company_hint") or None,
                    search_enabled=st.session_state.pre_advice_form_data.get("use_news_checkbox", True),
                )
            st.success("✅ アイスブレイクを生成しました！")
        except Exception as e:  # pragma: no cover - fallback handling
            logger.error(f"Icebreaker generation error: {e}", exc_info=True)
            st.session_state.icebreakers = []

    if st.session_state.icebreakers:
        st.markdown("#### 🎯 アイスブレイク候補")
        for idx, line in enumerate(st.session_state.icebreakers, 1):
            with st.container():
                st.markdown(f"**{idx}.** {line}")
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button(
                        f"🎯 選択", key=f"select_{idx}", use_container_width=True, type="primary"
                    ):
                        st.session_state.selected_icebreaker = line
                        st.rerun()
                with col2:
                    from components.copy_button import copy_button

                    copy_button(line, key=f"copy_{idx}", use_container_width=True)
                with col3:
                    if st.button(
                        f"👁️ 詳細", key=f"detail_{idx}", use_container_width=True
                    ):
                        st.info(f"**アイスブレイク詳細：**\n\n{line}")

        if st.session_state.selected_icebreaker:
            st.markdown("### ❄️ 選択中のアイスブレイク")
            st.markdown(f"> {st.session_state.selected_icebreaker}")
            from components.copy_button import copy_button

            copy_button(
                st.session_state.selected_icebreaker,
                key="selected_icebreaker_copy",
            )


__all__ = [
    "show_pre_advice_page",
    "render_form",
    "process_form_data",
    "validate_input",
    "display_result",
    "display_advice",
    "render_save_section",
    "render_sales_style_selection",
    "render_simplified_form",
    "get_screen_width",
]

