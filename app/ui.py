import os
import streamlit as st
from dotenv import load_dotenv
from streamlit_javascript import st_javascript
from translations import t, get_language
from services.settings_manager import SettingsManager

# 環境変数を読み込み
load_dotenv()


def main():
    st.set_page_config(
        page_title=t("app_title"),
        page_icon="🏢",
        layout="wide",
    )

    # モバイルUI最適化のCSSを読み込み
    css_path = os.path.join(os.path.dirname(__file__), "static", "responsive.css")
    if os.path.exists(css_path):
        with open(css_path, encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    settings_manager = SettingsManager()
    settings = settings_manager.load_settings()

    # 初回アクセス時にチュートリアルを表示
    if settings.show_tutorial_on_start and not st.session_state.get("tutorial_shown"):
        st.session_state["show_tutorial_modal"] = True

    if st.session_state.get("force_show_tutorial"):
        st.session_state["show_tutorial_modal"] = True
        st.session_state["force_show_tutorial"] = False

    if st.session_state.get("show_tutorial_modal"):
        @st.dialog(t("tutorial_title"))
        def show_tutorial():
            st.write(t("tutorial_message"))
            if st.button(t("tutorial_close"), key="tutorial_close_button"):
                st.session_state["show_tutorial_modal"] = False
                st.session_state["tutorial_shown"] = True
                if settings.show_tutorial_on_start:
                    settings_manager.update_setting("show_tutorial_on_start", False)
                st.rerun()

        show_tutorial()

    # 画面幅を取得してセッションステートに保存
    if "screen_width" not in st.session_state:
        width = st_javascript("return window.innerWidth;")
        if width is None:
            params = st.experimental_get_query_params()
            try:
                width = int(params.get("width", [1000])[0])
            except (ValueError, TypeError):
                width = 1000
        st.session_state.screen_width = width

    # デフォルト言語を日本語に設定
    if "language" not in st.session_state:
        st.session_state["language"] = "ja"
        # 設定マネージャーにも保存
        settings_manager.update_setting("language", "ja")

    current_lang = get_language()
    # 強制的に日本語を設定
    if current_lang != "ja":
        st.session_state["language"] = "ja"
        current_lang = "ja"
    lang_options = {
        "ja": "\U0001F1EF\U0001F1F5 日本語",
        "en": "\U0001F1FA\U0001F1F8 English",
        "es": "\U0001F1EA\U0001F1F8 Español",
    }
    header_cols = st.columns([8, 2])
    with header_cols[0]:
        st.title(t("app_title"))
    with header_cols[1]:
        selected_lang = st.selectbox(
            "language",
            options=list(lang_options.keys()),
            index=list(lang_options.keys()).index(current_lang),
            format_func=lambda x: lang_options[x],
            key="language_select",
            label_visibility="collapsed",
        )
        if selected_lang != current_lang:
            st.session_state["language"] = selected_lang
            settings_manager.update_setting("language", selected_lang)
            st.rerun()

    st.markdown("---")

    is_mobile = st.session_state.get("screen_width", 1000) < 700

    # セッションステート初期化
    st.session_state.setdefault("show_sidebar", False)
    st.session_state.setdefault("quickstart_mode", False)

    # 環境変数の確認
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("⚠️ OPENAI_API_KEYが設定されていません。一部機能が制限されます。")

    if is_mobile:
        # ハンバーガーメニューでサイドバーをトグル表示
        cols = st.columns([1, 9])
        with cols[0]:
            st.markdown(
                f'<button id="menu-toggle" aria-label="メニュー">{t("sidebar_toggle_label")}</button>',
                unsafe_allow_html=True,
            )
            clicked_ts = st_javascript(
                """
                const btn = document.getElementById('menu-toggle');
                if (btn) {
                    btn.setAttribute('aria-label', 'メニュー');
                    btn.onclick = () => Streamlit.setComponentValue(Date.now());
                }
                """,
                key="menu_toggle_js",
            )
            last_clicked = st.session_state.get("menu_toggle_last")
            if clicked_ts and clicked_ts != last_clicked:
                st.session_state.show_sidebar = not st.session_state.show_sidebar
                st.session_state.menu_toggle_last = clicked_ts
            # aria-label: toggle navigation menu

        if st.session_state.show_sidebar:
            with st.expander(t("menu"), expanded=True):
                # aria-label: mobile sidebar content
                st.checkbox(
                    t("quickstart_mode"),
                    help=t("quickstart_help"),
                    key="quickstart_mode",
                )  # aria-label: toggle quickstart mode

        st.caption(t("tab_navigation_hint"))

        page_keys = [
            "pre_advice",
            "post_review",
            "icebreaker",
            "history",
            "settings",
            "search_enhancement",
        ]
        # 日本語で直接指定（翻訳が正しく動作しない場合のフォールバック）
        page_labels = {
            "pre_advice": "事前アドバイス生成",
            "post_review": "商談後ふりかえり解析",
            "icebreaker": "アイスブレイク生成",
            "history": "履歴",
            "settings": "設定・カスタマイズ",
            "search_enhancement": "検索機能の高度化",
        }
        # aria-label: page navigation tabs
        tabs = st.tabs([page_labels[k] for k in page_keys])
        with tabs[0]:
            from pages.pre_advice import show_pre_advice_page

            show_pre_advice_page()
        with tabs[1]:
            from pages.post_review import show_post_review_page

            show_post_review_page()
        with tabs[2]:
            from pages.icebreaker import show_icebreaker_page

            show_icebreaker_page()
        with tabs[3]:
            from pages.history import show_history_page

            show_history_page()
        with tabs[4]:
            from pages.settings import show_settings_page

            show_settings_page()
        with tabs[5]:
            from pages.search_enhancement import show_enhanced_search_page

            show_enhanced_search_page()
    else:
        # デスクトップでは従来どおりサイドバーを使用
        st.sidebar.title(t("menu"))
        if "page_select" not in st.session_state:
            st.session_state.page_select = "pre_advice"

        page_keys = [
            "pre_advice",
            "post_review",
            "icebreaker",
            "history",
            "settings",
            "search_enhancement",
        ]
        page_labels = {k: t(k) for k in page_keys}

        page = st.sidebar.selectbox(
            t("select_page"),
            options=page_keys,
            format_func=lambda x: page_labels[x],
            key="page_select",
        )

        st.sidebar.checkbox(
            t("quickstart_mode"),
            help=t("quickstart_help"),
            key="quickstart_mode",
        )

        if page == "pre_advice":
            from pages.pre_advice import show_pre_advice_page

            show_pre_advice_page()
        elif page == "post_review":
            from pages.post_review import show_post_review_page

            show_post_review_page()
        elif page == "icebreaker":
            from pages.icebreaker import show_icebreaker_page

            show_icebreaker_page()
        elif page == "settings":
            from pages.settings import show_settings_page

            show_settings_page()
        elif page == "history":
            from pages.history import show_history_page

            show_history_page()
        elif page == "search_enhancement":
            from pages.search_enhancement import show_enhanced_search_page

            show_enhanced_search_page()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"アプリケーション起動エラー: {e}")
        st.error("詳細なエラー情報を確認してください")
        import traceback
        st.code(traceback.format_exc())

