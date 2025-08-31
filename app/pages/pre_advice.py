"""
Pre-advice page - Main entry point
This module orchestrates the pre-advice generation workflow.
"""

from typing import Dict, Any, Optional
import streamlit as st
from translations import t

from services.pre_advisor import PreAdvisorService
from services.crm_importer import CRMImporter
from services.settings_manager import SettingsManager
from core.logging_config import get_logger

# Import refactored modules
from .pre_advice_forms import render_sales_style_selection, render_simplified_form, render_form
from .pre_advice_handlers import apply_crm_data, process_form_data, process_simplified_form_data, validate_input
from .pre_advice_ui import display_result
from .pre_advice_storage import save_pre_advice

# Setup logger
logger = get_logger(__name__)


def get_screen_width() -> int:
    """画面幅を取得するヘルパー関数"""
    return st.session_state.get("screen_width", 1000)


def show_pre_advice_page() -> None:
    """事前アドバイスページを表示（リファクタ済み）"""
    st.header("📝 事前アドバイス生成")
    st.write("営業スタイルに合わせた商談準備をサポートします")

    # モード選択
    use_simplified = st.checkbox(
        "簡略モードを使用する",
        value=st.session_state.get("use_simplified_mode", True),
        help="営業スタイル診断と簡略化された入力フォームを使用します"
    )
    st.session_state.use_simplified_mode = use_simplified

    settings_manager: SettingsManager = SettingsManager()
    settings = settings_manager.load_settings()

    # CRM連携（オプション）
    if settings.crm_enabled:
        with st.expander("CRM連携", expanded=False):
            crm_id: str = st.text_input("CRM顧客ID", key="crm_customer_id")
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
                except ConnectionError as e:
                    st.error("CRMサーバーに接続できません。ネットワーク接続を確認してください。")
                    logger.warning(f"CRM connection error: {e}")
                except ValueError as e:
                    st.error("CRM顧客IDの形式が正しくありません。")
                    logger.warning(f"CRM data validation error: {e}")
                except Exception as e:
                    st.error("CRM連携で予期しないエラーが発生しました。")
                    logger.error(f"CRM unexpected error: {e}", exc_info=True)

    is_mobile: bool = get_screen_width() < 700

    if "pre_advice_form_data" not in st.session_state:
        st.session_state.pre_advice_form_data = {}

    # フォーム表示（簡略化モード or 従来モード）
    if use_simplified:
        # 簡略化モード
        submitted, form_data = render_simplified_form()
        if submitted:
            # バリデーション
            if not form_data["industry"]:
                st.error("❌ 業界を入力してください")
                return
            if not form_data["product"]:
                st.error("❌ 商品・サービスを入力してください")
                return

            # SalesInput生成
            sales_input = process_simplified_form_data(form_data)

            try:
                # 強化されたプログレス表示
                progress_placeholder = st.empty()
                status_placeholder = st.empty()

                with progress_placeholder.container():
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                # ステップ1: 入力検証
                status_text.text("🔍 入力を検証中...")
                progress_bar.progress(10)

                # ステップ2: AI分析準備
                status_text.text("🤖 AI分析を開始...")
                progress_bar.progress(30)

                # ステップ3: アドバイス生成
                status_text.text("📝 アドバイスを生成中...")
                progress_bar.progress(60)

                # LLM呼び出し
                service = PreAdvisorService(settings_manager)
                advice = service.generate_advice(sales_input)

                # ステップ4: 結果整理
                status_text.text("✨ 結果を整理中...")
                progress_bar.progress(90)

                # 完了
                progress_bar.progress(100)
                status_text.text("✅ 完了！")

                # 少し待ってからクリア
                import time
                time.sleep(0.5)
                progress_placeholder.empty()

                st.success("✅ アドバイスの生成が完了しました！")
                display_result(advice, sales_input)

            except Exception as e:
                # エラー時はプログレスをクリア
                if 'progress_placeholder' in locals():
                    progress_placeholder.empty()

                st.error(f"❌ アドバイスの生成に失敗しました: {str(e)}")
                st.info("しばらく時間をおいて再度お試しください。")

        # アイスブレイクセクション
            if is_mobile:
            with st.expander("❄️ アイスブレイク生成", expanded=False):
                render_icebreaker_section()
                else:
            render_icebreaker_section()

                else:
        # 従来モード（後方互換性）
            if is_mobile:
            tab_form, tab_ice = st.tabs(["入力フォーム", "アイスブレイク"])
            with tab_form:
                submitted, form_data = render_form()
            with tab_ice:
                render_icebreaker_section()
                else:
            submitted, form_data = render_form()
            render_icebreaker_section()

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
            except ConnectionError as e:
                st.error("❌ サーバーに接続できません。ネットワーク接続を確認してください。")
                logger.error(f"API connection error: {e}")
            except ValueError as e:
                st.error("❌ 入力データに問題があります。内容を確認してください。")
                logger.warning(f"Input validation error: {e}")
            except Exception as e:
                st.error("❌ アドバイスの生成に失敗しました。しばらく時間をおいて再度お試しください。")
                logger.error(f"Advice generation unexpected error: {e}", exc_info=True)

def render_icebreaker_section():
    """アイスブレイク生成セクションを表示"""
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
        except ConnectionError as e:
            st.warning("アイスブレイク生成で接続エラーが発生しました。ネットワーク接続を確認してください。")
            logger.error(f"Icebreaker connection error: {e}")
            st.session_state.icebreakers = []
        except ValueError as e:
            st.warning("アイスブレイク生成で入力データに問題があります。")
            logger.warning(f"Icebreaker input error: {e}")
            st.session_state.icebreakers = []
        except Exception as e:
            st.warning("アイスブレイク生成に失敗しました（フォールバックを表示）")
            logger.error(f"Icebreaker unexpected error: {e}", exc_info=True)
                st.session_state.icebreakers = []

    if st.session_state.icebreakers:
        st.markdown("#### 🎯 アイスブレイク候補")
        for idx, line in enumerate(st.session_state.icebreakers, 1):
            with st.container():
                st.markdown(f"**{idx}.** {line}")
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button(f"🎯 選択", key=f"select_{idx}", use_container_width=True, type="primary"):
                        st.session_state.selected_icebreaker = line
                        st.rerun()
                with col2:
                    from components.copy_button import copy_button
                    copy_button(line, key=f"copy_{idx}", use_container_width=True)
                with col3:
                    if st.button(f"👁️ 詳細", key=f"detail_{idx}", use_container_width=True):
                        st.info(f"**アイスブレイク詳細：**\n\n{line}")

        if st.session_state.selected_icebreaker:
            st.markdown("### ❄️ 選択中のアイスブレイク")
        st.markdown(f"> {st.session_state.selected_icebreaker}")
            copy_button(st.session_state.selected_icebreaker, key="selected_icebreaker_copy")
        # 業界入力