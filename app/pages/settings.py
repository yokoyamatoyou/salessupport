import os
import streamlit as st
import json
from pathlib import Path
from services.settings_manager import SettingsManager
from core.models import LLMMode, SearchProvider
from translations import t

def show_settings_page():
    """設定ページを表示"""
    st.title(t("settings_page_title"))
    st.markdown(t("settings_page_desc"))
    
    # 設定マネージャーの初期化
    settings_manager = SettingsManager()
    
    # タブで設定を分類
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        t("tab_llm"),
        t("tab_search"),
        t("tab_ui"),
        t("tab_data"),
        t("tab_import_export"),
        t("tab_crm"),
    ])
    
    with tab1:
        show_llm_settings(settings_manager)
    
    with tab2:
        show_search_settings(settings_manager)
    
    with tab3:
        show_ui_settings(settings_manager)
    
    with tab4:
        show_data_settings(settings_manager)
    
    with tab5:
        show_import_export(settings_manager)

    with tab6:
        show_crm_settings(settings_manager)

def show_llm_settings(settings_manager: SettingsManager):
    """LLM設定を表示"""
    st.header(t("tab_llm"))
    
    settings = settings_manager.load_settings()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # デフォルトLLMモード
        default_mode = st.selectbox(
            "デフォルトLLMモード",
            options=list(LLMMode),
            index=list(LLMMode).index(settings.default_llm_mode),
            help="LLMの動作モードを選択"
        )
        
        # 最大トークン数
        max_tokens = st.slider(
            "最大トークン数",
            min_value=100,
            max_value=4000,
            value=settings.max_tokens,
            step=100,
            help="生成されるテキストの最大長"
        )
    
    with col2:
        # 温度（創造性）
        temperature = st.slider(
            "創造性（温度）",
            min_value=0.0,
            max_value=2.0,
            value=settings.temperature,
            step=0.1,
            help="値が高いほど創造的、低いほど決定論的"
        )
        
        # 設定の説明
        st.info("""
        **LLMモード説明:**
        - **Speed**: 高速で簡潔な回答
        - **Deep**: 詳細で分析的な回答
        - **Creative**: 創造的で独創的な回答
        """)
    
    # 保存ボタン
    if st.button("LLM設定を保存", type="primary"):
        settings.default_llm_mode = default_mode
        settings.max_tokens = max_tokens
        settings.temperature = temperature
        
        if settings_manager.save_settings(settings):
            st.success("LLM設定を保存しました！")
        else:
            st.error("設定の保存に失敗しました。")

def show_search_settings(settings_manager: SettingsManager):
    """検索設定を表示"""
    st.header(t("tab_search"))
    
    settings = settings_manager.load_settings()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 検索プロバイダー
        search_provider = st.selectbox(
            "検索プロバイダー",
            options=list(SearchProvider),
            index=list(SearchProvider).index(settings.search_provider),
            help="業界ニュースの検索に使用するサービス"
        )
        
        # 検索結果の最大件数
        search_limit = st.slider(
            "検索結果の最大件数",
            min_value=1,
            max_value=20,
            value=settings.search_results_limit,
            step=1,
            help="取得する検索結果の件数"
        )
    
    with col2:
        # プロバイダー説明
        st.info("""
        **検索プロバイダー説明:**
        - **None**: 検索機能を無効化
        - **Stub**: テスト用のダミーデータ
        - **CSE**: Google Custom Search Engine
        - **NewsAPI**: ニュースAPI
        - **Hybrid**: CSEとNewsAPIの複合検索
        """)
        
        # 追加の検索制御
        trusted_domains = st.text_area(
            "信頼ドメイン（改行区切り）",
            value="\n".join(settings.search_trusted_domains),
            help="信頼度を加点するドメイン（例: www.nikkei.com）"
        )
        time_window = st.slider(
            "新鮮度評価のタイムウィンドウ（日）",
            min_value=7,
            max_value=365,
            value=settings.search_time_window_days,
            step=1,
            help="新しい記事ほどスコアが高くなる期間"
        )
        language = st.selectbox(
            "ニュース言語（NewsAPI）",
            options=["ja", "en"],
            index=0 if settings.search_language == "ja" else 1,
            help="NewsAPIの言語指定"
        )
        
        # 検索設定の詳細説明
        st.info("""
        **検索設定の効果:**
        
        **信頼ドメイン**: 特定のドメイン（日経、Reuters等）からの記事に信頼度ボーナスを付与。
        これにより、より信頼性の高い情報源が優先的に表示されます。
        
        **タイムウィンドウ**: 新しい記事ほど高スコア。業界の最新動向をキャッチできます。
        
        **言語設定**: 日本語/英語のニュースを選択。業界によって最適な言語が異なります。
        
        **検索結果**: これらの設定に基づいてスコアリングされ、最も関連性の高い記事が上位に表示されます。
        """)
    
    # 保存ボタン
    if st.button("検索設定を保存", type="primary"):
        settings.search_provider = search_provider
        settings.search_results_limit = search_limit
        settings.search_trusted_domains = [d.strip() for d in trusted_domains.split("\n") if d.strip()]
        settings.search_time_window_days = time_window
        settings.search_language = language
        
        if settings_manager.save_settings(settings):
            st.success("検索設定を保存しました！")
        else:
            st.error("設定の保存に失敗しました。")

def show_ui_settings(settings_manager: SettingsManager):
    """UI設定を表示"""
    st.header(t("tab_ui"))
    
    settings = settings_manager.load_settings()
    
    col1, col2 = st.columns(2)

    with col1:
        # 言語設定
        language_options = ["ja", "en", "es"]
        language = st.selectbox(
            t("language_setting"),
            options=language_options,
            index=language_options.index(settings.language) if settings.language in language_options else 0,
            help=t("language_setting_help"),
            key="language_select",
        )
        if st.session_state.get("language") != language:
            st.session_state["language"] = language
        
        # テーマ設定
        theme = st.selectbox(
            "テーマ設定",
            options=["light", "dark"],
            index=0 if settings.theme == "light" else 1,
            help="UIのテーマ"
        )
    
    with col2:
        # 自動保存
        auto_save = st.checkbox(
            "自動保存を有効にする",
            value=settings.auto_save,
            help="生成されたアドバイスや分析を自動で保存"
        )
        show_tutorial = st.checkbox(
            t("show_tutorial_on_start"),
            value=settings.show_tutorial_on_start,
            help=t("show_tutorial_on_start_help"),
        )

        if st.button(t("show_tutorial_again")):
            st.session_state["force_show_tutorial"] = True
            st.rerun()

        
        # 設定の説明
        st.info("""
        **UI設定の説明:**
        - **言語**: 現在は日本語と英語をサポート
        - **テーマ**: ライトとダークテーマ
        - **自動保存**: 作業内容の自動保存
        """)
    
    # 営業タイプ別の色設定
    st.subheader("🎨 営業タイプ別の色設定")
    st.write("各営業タイプの表示色をカスタマイズできます。")
    
    # デフォルトの色設定
    default_colors = {
        "hunter": "#FF6B6B",      # 赤
        "closer": "#4ECDC4",      # 青緑
        "relation": "#45B7D1",    # 青
        "consultant": "#96CEB4",  # 緑
        "challenger": "#FFEAA7",  # 黄
        "storyteller": "#DDA0DD", # 紫
        "analyst": "#98D8C8",     # 薄緑
        "problem_solver": "#F7DC6F", # オレンジ
        "farmer": "#BB8FCE"       # 薄紫
    }
    
    # 現在の色設定を取得（デフォルトとマージ）
    current_colors = {**default_colors, **settings.sales_type_colors}
    
    # 色設定の編集
    col1, col2, col3 = st.columns(3)
    
    for i, (sales_type, color) in enumerate(current_colors.items()):
        col = col1 if i % 3 == 0 else col2 if i % 3 == 1 else col3
        
        with col:
            st.color_picker(
                f"{sales_type.title()}",
                value=color,
                key=f"color_{sales_type}",
                help=f"{sales_type.title()}タイプの表示色を設定"
            )
    
    # 色設定の保存
    if st.button("色設定を保存", type="primary"):
        # 変更された色設定を収集
        for sales_type in current_colors.keys():
            new_color = st.session_state.get(f"color_{sales_type}")
            if new_color and new_color != current_colors[sales_type]:
                settings.sales_type_colors[sales_type] = new_color
        
        if settings_manager.save_settings(settings):
            st.success("色設定を保存しました！")
        else:
            st.error("色設定の保存に失敗しました。")
    
    # 色設定のリセット
    if st.button("色設定をデフォルトにリセット", type="secondary"):
        settings.sales_type_colors = {}
        if settings_manager.save_settings(settings):
            st.success("色設定をデフォルトにリセットしました！")
            st.rerun()
        else:
            st.error("色設定のリセットに失敗しました。")
    
    # 保存ボタン
    if st.button("UI設定を保存", type="primary"):
        settings.language = language
        settings.theme = theme
        settings.auto_save = auto_save
        settings.show_tutorial_on_start = show_tutorial
        
        if settings_manager.save_settings(settings):
            st.success("UI設定を保存しました！")
        else:
            st.error("設定の保存に失敗しました。")

def show_data_settings(settings_manager: SettingsManager):
    """データ設定を表示"""
    st.header(t("tab_data"))
    
    settings = settings_manager.load_settings()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # データディレクトリ
        data_dir = st.text_input(
            "データ保存ディレクトリ",
            value=settings.data_dir,
            help="生成されたデータの保存場所"
        )
        
        # ディレクトリの存在確認
        if Path(data_dir).exists():
            st.success(f"ディレクトリが存在します: {data_dir}")
        else:
            st.warning(f"ディレクトリが存在しません: {data_dir}")
    
    with col2:
        # カスタムプロンプト
        st.subheader("カスタムプロンプト")
        
        # 新しいプロンプトの追加
        prompt_name = st.text_input("プロンプト名", placeholder="例: 業界別アドバイス")
        prompt_content = st.text_area("プロンプト内容", placeholder="カスタムプロンプトを入力...")
        
        if st.button("プロンプトを追加"):
            if prompt_name and prompt_content:
                settings.custom_prompts[prompt_name] = prompt_content
                if settings_manager.save_settings(settings):
                    st.success(f"プロンプト '{prompt_name}' を追加しました！")
                else:
                    st.error("プロンプトの追加に失敗しました。")
            else:
                st.warning("プロンプト名と内容を入力してください。")
    
    # 既存のカスタムプロンプト表示
    if settings.custom_prompts:
        st.subheader("既存のカスタムプロンプト")
        for name, content in settings.custom_prompts.items():
            with st.expander(f"📝 {name}"):
                st.text_area(f"内容: {name}", value=content, key=f"prompt_{name}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"更新: {name}", key=f"update_{name}"):
                        new_content = st.session_state.get(f"prompt_{name}", content)
                        settings.custom_prompts[name] = new_content
                        if settings_manager.save_settings(settings):
                            st.success(f"プロンプト '{name}' を更新しました！")
                        else:
                            st.error("プロンプトの更新に失敗しました。")
                
                with col2:
                    if st.button(f"削除: {name}", key=f"delete_{name}"):
                        del settings.custom_prompts[name]
                        if settings_manager.save_settings(settings):
                            st.success(f"プロンプト '{name}' を削除しました！")
                        else:
                            st.error("プロンプトの削除に失敗しました。")
    
    # データ設定の保存
    if st.button("データ設定を保存", type="primary"):
        settings.data_dir = data_dir
        
        if settings_manager.save_settings(settings):
            st.success("データ設定を保存しました！")
        else:
            st.error("設定の保存に失敗しました。")

def show_import_export(settings_manager: SettingsManager):
    """インポート/エクスポート設定を表示"""
    st.header(t("tab_import_export"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 設定をエクスポート")
        
        # エクスポートファイル名
        export_filename = st.text_input(
            "エクスポートファイル名",
            value="sales_saas_settings.json",
            help="エクスポートする設定ファイルの名前"
        )
        
        if st.button("設定をエクスポート", type="primary"):
            if settings_manager.export_settings(export_filename):
                st.success(f"設定をエクスポートしました: {export_filename}")
                
                # ダウンロードリンク
                with open(export_filename, 'r', encoding='utf-8') as f:
                    st.download_button(
                        label="📥 設定ファイルをダウンロード",
                        data=f.read(),
                        file_name=export_filename,
                        mime="application/json"
                    )
            else:
                st.error("設定のエクスポートに失敗しました。")
    
    with col2:
        st.subheader("📥 設定をインポート")
        
        # ファイルアップロード
        uploaded_file = st.file_uploader(
            "設定ファイルを選択",
            type=['json'],
            help="JSON形式の設定ファイルをアップロード"
        )
        
        if uploaded_file is not None:
            if st.button("設定をインポート", type="primary"):
                # 一時ファイルとして保存
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                
                if settings_manager.import_settings(temp_path):
                    st.success("設定をインポートしました！")
                    # 一時ファイルを削除
                    Path(temp_path).unlink(missing_ok=True)
                else:
                    st.error("設定のインポートに失敗しました。")
    
    # 設定のリセット
    st.subheader("🔄 設定をリセット")
    st.warning("⚠️ この操作は現在の設定をすべて削除し、デフォルト設定に戻します。")
    
    if st.button("設定をデフォルトにリセット", type="secondary"):
        if settings_manager.reset_to_defaults():
            st.success("設定をデフォルトにリセットしました！")
            st.rerun()  # ページを再読み込み
        else:
            st.error("設定のリセットに失敗しました。")


def show_crm_settings(settings_manager: SettingsManager):
    """CRM連携設定を表示"""
    st.header(t("tab_crm"))

    settings = settings_manager.load_settings()
    crm_enabled = st.checkbox(
        t("crm_enable"),
        value=getattr(settings, "crm_enabled", False),
        help=t("crm_enable_help"),
    )

    api_key = os.getenv("CRM_API_KEY")
    if not api_key:
        st.warning(t("crm_api_key_missing"))

    if st.button("CRM設定を保存", type="primary"):
        settings.crm_enabled = crm_enabled
        if settings_manager.save_settings(settings):
            st.success("CRM設定を保存しました！")
        else:
            st.error("設定の保存に失敗しました。")
