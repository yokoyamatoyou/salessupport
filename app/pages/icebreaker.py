import streamlit as st
import json
import uuid
from datetime import datetime
from core.models import SalesType, SalesStyle
from services.icebreaker import IcebreakerService
from components.copy_button import copy_button
from app.components.practical_icebreaker import PracticalIcebreakerGenerator
from translations import t

def show_icebreaker_page():
    """改善版アイスブレイクページ"""
    st.header("❄️ 実践的なアイスブレイク生成")
    st.write("営業スタイルに合わせた、自然で効果的なアイスブレイクを生成します")

    # モード選択
    use_enhanced = st.checkbox(
        "実践モードを使用する",
        value=st.session_state.get("use_enhanced_icebreaker", True),
        help="営業スタイル診断と実践的な表現を使用します"
    )
    st.session_state.use_enhanced_icebreaker = use_enhanced

    # 履歴からの即時再生成（オートラン）の処理
    if st.session_state.get("icebreaker_autorun"):
        st.info("履歴から即時再生成を実行しています...")
        st.session_state["icebreaker_autorun"] = False
        st.session_state["autorun_session_id"] = None

    if use_enhanced:
        # 実践モード：営業スタイル診断 + 実践的なアイスブレイク
        show_enhanced_icebreaker_flow()
    else:
        # 従来モード：後方互換性のため維持
        show_traditional_icebreaker_flow()


def show_enhanced_icebreaker_flow():
    """実践モードのアイスブレイク生成フロー"""
    from components.sales_style_diagnosis import SalesStyleDiagnosis

    # 営業スタイル診断
    diagnosis = SalesStyleDiagnosis()
    diagnosed_style = diagnosis.render_diagnosis_ui()

    if not diagnosed_style:
        return

    # 診断完了後の入力フォーム
    st.markdown("---")
    st.markdown("### 📝 アイスブレイク生成情報")

    with st.form("enhanced_icebreaker_form"):
        col1, col2 = st.columns([2, 1])

        with col1:
            industry = st.text_input(
                "業界 *",
                placeholder="例: IT、製造業、金融業、医療、小売",
                help="業界を入力すると、より適切なアイスブレイクが生成されます"
            )

            company_hint = st.text_input(
                "会社ヒント（任意）",
                placeholder="例: 大手企業、スタートアップ、伝統企業、〇〇グループ",
                help="会社の特徴があれば、より自然な表現になります"
            )

            meeting_context = st.selectbox(
                "ミーティングの文脈",
                ["", "初回商談", "フォローアップ", "提案説明", "クロージング"],
                help="ミーティングの状況を選択すると、より適切なアイスブレイクが生成されます"
            )

        with col2:
            search_enabled = st.checkbox(
                "業界ニュースを活用",
                value=True,
                help="業界の最新ニュースを活用して時事的な話題を追加"
            )

            count = st.selectbox(
                "生成数",
                [3, 5, 7],
                index=0,
                help="生成するアイスブレイクの数"
            )

        submitted = st.form_submit_button("🚀 実践的なアイスブレイクを生成", type="primary", use_container_width=True)

    if submitted:
        if not industry:
            st.error("❌ 業界を入力してください")
            return

        try:
            with st.spinner("🤖 営業スタイルに最適化されたアイスブレイクを生成中..."):
                # 実践的なアイスブレイク生成
                generator = PracticalIcebreakerGenerator()

                icebreakers = []
                for _ in range(count):
                    icebreaker = generator.generate_contextual_icebreaker(
                        diagnosed_style,
                        industry,
                        company_hint,
                        meeting_context
                    )
                    if icebreaker not in icebreakers:  # 重複除去
                        icebreakers.append(icebreaker)

                # 必要に応じて従来のサービスも活用
                if search_enabled and len(icebreakers) < count:
                    from services.settings_manager import SettingsManager
                    settings_manager = SettingsManager()
                    service = IcebreakerService(settings_manager)

                    # スタイルを従来のSalesTypeにマッピング
                    style_mapping = {
                        SalesStyle.RELATIONSHIP_BUILDER: SalesType.RELATION,
                        SalesStyle.PROBLEM_SOLVER: SalesType.PROBLEM_SOLVER,
                        SalesStyle.VALUE_PROPOSER: SalesType.CHALLENGER,
                        SalesStyle.SPECIALIST: SalesType.CONSULTANT,
                        SalesStyle.DEAL_CLOSER: SalesType.CLOSER,
                    }
                    legacy_type = style_mapping.get(diagnosed_style, SalesType.HUNTER)

                    additional = service.generate_icebreakers(
                        sales_type=legacy_type,
                        industry=industry,
                        company_hint=company_hint,
                        search_enabled=search_enabled
                    )

                    # 新しい表現を追加
                    for item in additional:
                        if item not in icebreakers and len(icebreakers) < count:
                            icebreakers.append(item)

            # スタイル別Tipsを取得
            style_tips = generator.get_style_specific_tips(diagnosed_style)

            # 結果表示
            display_enhanced_icebreakers(
                diagnosed_style, industry, icebreakers,
                search_enabled, company_hint, style_tips
            )

        except Exception as e:
            st.error(f"❌ アイスブレイク生成に失敗しました: {e}")
            st.info("しばらく時間をおいて再度お試しください。")


def show_traditional_icebreaker_flow():
    """従来モードのアイスブレイク生成フロー（後方互換性）"""
    # 従来のフォームと処理をここに実装
    st.info("従来モードは準備中です。実践モードをご利用ください。")


def display_enhanced_icebreakers(
    sales_style: SalesStyle,
    industry: str,
    icebreakers: list,
    search_enabled: bool,
    company_hint: str,
    style_tips: dict
):
    """実践的なアイスブレイクの結果表示"""
    st.success("✅ 実践的なアイスブレイクが生成されました！")

    # スタイル情報表示
    from components.sales_style_diagnosis import SalesStyleDiagnosis
    diagnosis = SalesStyleDiagnosis()
    style_info = diagnosis.get_style_info(sales_style)

    st.markdown(f"### 🎯 {style_info['name']}")
    st.markdown(f"**{style_info['description']}**")

    # アイスブレイク一覧
    st.markdown("### 💬 生成されたアイスブレイク")

    for i, icebreaker in enumerate(icebreakers, 1):
        with st.container():
            st.markdown(f"**{i}.** {icebreaker}")

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                copy_button(icebreaker, key=f"copy_enhanced_{i}", use_container_width=True)
            with col2:
                if st.button("👍 良い", key=f"good_{i}", help="この表現が良い"):
                    st.success("フィードバックを記録しました！")
            with col3:
                if st.button("📝 詳細", key=f"detail_{i}"):
                    show_icebreaker_detail(icebreaker, style_tips)

            st.markdown("---")

    # スタイル別アドバイス
    st.markdown("### 💡 この営業スタイルでの使い方")

    with st.expander("効果的な使用Tips", expanded=True):
        st.markdown(f"**トーン:** {style_tips['tone']}")
        st.markdown(f"**焦点:** {style_tips['focus']}")
        st.markdown(f"**フォローアップ:** {style_tips['follow_up']}")

        st.markdown("**使用例:**")
        for example in style_tips['examples'][:2]:
            st.markdown(f"• {example}")

    # 保存機能
    st.markdown("### 💾 保存と共有")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 セッションに保存", use_container_width=True):
            session_id = save_enhanced_icebreakers(
                sales_style, industry, icebreakers, company_hint, search_enabled
            )
            if session_id:
                st.success(f"保存しました！セッションID: {session_id[:8]}...")

    with col2:
        if st.button("📥 JSONでダウンロード", use_container_width=True):
            download_enhanced_icebreakers_json(
                sales_style, industry, icebreakers, company_hint, search_enabled
            )


def show_icebreaker_detail(icebreaker: str, style_tips: dict):
    """アイスブレイクの詳細表示"""
    with st.expander("詳細分析", expanded=False):
        st.markdown("**表現の特徴:**")
        st.markdown("- 自然で会話らしい流れ")
        st.markdown("- 相手の反応を引き出しやすい")
        st.markdown("- 営業目的を意識しつつ自然")

        st.markdown(f"**{style_tips['tone']}** な表現を採用")
        st.markdown(f"**{style_tips['focus']}** に適した内容")


def save_enhanced_icebreakers(sales_style: SalesStyle, industry: str, icebreakers: list,
                             company_hint: str, search_enabled: bool):
    """実践モードのアイスブレイクを保存"""
    try:
        session_id = str(uuid.uuid4())

        session_data = {
            "session_id": session_id,
            "type": "enhanced_icebreaker",
            "created_at": datetime.now().isoformat(),
            "sales_style": sales_style.value,
            "industry": industry,
            "company_hint": company_hint,
            "search_enabled": search_enabled,
            "icebreakers": icebreakers,
            "style_info": {
                "name": f"{sales_style.value}スタイル",
                "description": "実践的な営業表現"
            }
        }

        if "enhanced_icebreaker_sessions" not in st.session_state:
            st.session_state.enhanced_icebreaker_sessions = {}

        st.session_state.enhanced_icebreaker_sessions[session_id] = session_data

        # ストレージサービスでの保存も試行
        try:
            from services.storage_service import get_storage_provider
            provider = get_storage_provider()
            payload = {
                "type": "enhanced_icebreaker",
                "input": {
                    "sales_style": sales_style.value,
                    "industry": industry,
                    "company_hint": company_hint,
                    "search_enabled": search_enabled,
                },
                "output": {
                    "icebreakers": icebreakers,
                    "style_info": session_data["style_info"]
                },
            }
            provider.save_session(payload, session_id=session_id)

        except Exception:
            pass  # ストレージ保存はオプション

        return session_id

    except Exception as e:
        st.error(f"保存に失敗しました: {e}")
        return None


def download_enhanced_icebreakers_json(sales_style: SalesStyle, industry: str,
                                      icebreakers: list, company_hint: str, search_enabled: bool):
    """実践モードのアイスブレイクをJSONダウンロード"""
    try:
        download_data = {
            "type": "enhanced_icebreaker",
            "created_at": datetime.now().isoformat(),
            "sales_style": sales_style.value,
            "industry": industry,
            "company_hint": company_hint,
            "search_enabled": search_enabled,
            "icebreakers": icebreakers,
            "style_info": {
                "name": f"{sales_style.value}スタイル",
                "description": "実践的な営業表現"
            }
        }

        json_str = json.dumps(download_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 JSONファイルをダウンロード",
            data=json_str,
            file_name=f"enhanced_icebreaker_{industry}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"ダウンロードに失敗しました: {e}")


def get_sales_type_emoji(sales_type: SalesType) -> str:
    """営業タイプに対応する絵文字を取得（後方互換性）"""
    emojis = {
        SalesType.HUNTER: "🏹",
        SalesType.CLOSER: "🔒",
        SalesType.RELATION: "🤝",
        SalesType.CONSULTANT: "🧭",
        SalesType.CHALLENGER: "⚡",
        SalesType.STORYTELLER: "📖",
        SalesType.ANALYST: "📊",
        SalesType.PROBLEM_SOLVER: "🧩",
        SalesType.FARMER: "🌾"
    }
    return emojis.get(sales_type, "👤")



def display_icebreakers(sales_type: SalesType, industry: str, icebreakers: list, search_enabled: bool, company_hint: str = None):
    """アイスブレイク結果を表示"""
    st.success("✅ アイスブレイクが生成されました！")
    
    # 営業タイプと業界の情報
    st.subheader(f"🎯 {sales_type.value} ({get_sales_type_emoji(sales_type)}) - {industry}業界")
    if company_hint:
        st.info(f"会社ヒント: {company_hint}")
    
    # 生成されたアイスブレイク
    st.subheader("💬 生成されたアイスブレイク")
    
    # モバイル対応のレイアウト
    for i, icebreaker in enumerate(icebreakers, 1):
        with st.container():
            # アイスブレイクテキストとコピーボタンを横並びで表示
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"**{i}. {icebreaker}**")
            
            with col2:
                copy_button(icebreaker, key=f"copy_{i}", use_container_width=True)
            
            # 使用シーン別のアドバイス（モバイル対応）
            with st.expander(f"使用シーン {i}", expanded=False):
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    st.write("**📞 電話**")
                    st.write("自然な流れで導入")
                with col2:
                    st.write("**🏢 訪問**")
                    st.write("場の雰囲気を読む")
                with col3:
                    st.write("**📧 メール**")
                    st.write("件名や導入で活用")
            
            st.divider()
    
    # 営業タイプ別の使用アドバイス
    st.subheader("💡 営業タイプ別の使用アドバイス")
    
    advice = get_sales_type_advice(sales_type)
    with st.expander("使用上のポイント", expanded=False):
        for point in advice:
            st.write(f"• {point}")
    
    # 業界ニュースの活用状況
    if search_enabled:
        st.subheader("📰 業界ニュース活用状況")
        st.info("業界の最新ニュースを活用して、時事的で親しみやすいアイスブレイクを生成しました。")
    else:
        st.subheader("📰 業界ニュース活用状況")
        st.warning("業界ニュースの活用を無効にしているため、一般的なアイスブレイクを生成しました。")
    
    # 保存セクション
    st.subheader("💾 アイスブレイクの保存")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("💾 セッションに保存", use_container_width=True):
            session_id = save_icebreakers(sales_type, industry, icebreakers, company_hint, search_enabled)
            if session_id:
                st.success(f"アイスブレイクをセッションに保存しました！セッションID: {session_id[:8]}...")
    
    with col2:
        if st.button("📥 JSONでダウンロード", use_container_width=True):
            download_icebreakers_json(sales_type, industry, icebreakers, company_hint, search_enabled)

def get_sales_type_advice(sales_type: SalesType) -> list:
    """営業タイプ別の使用アドバイスを取得"""
    advice = {
        SalesType.HUNTER: [
            "前向きで行動促進的なトーンを保つ",
            "簡潔で分かりやすい表現を使用",
            "顧客の関心を素早く引きつける"
        ],
        SalesType.CLOSER: [
            "価値訴求から始めて締めの一言で終わる",
            "顧客の課題解決への意欲を高める",
            "具体的なメリットを提示する"
        ],
        SalesType.RELATION: [
            "共感を示し、親近感を醸成する",
            "顧客の近況に興味を示す",
            "柔らかく親しみやすい口調を使用"
        ],
        SalesType.CONSULTANT: [
            "顧客の課題を仮説として提示する",
            "問いかけ形式で顧客の思考を促進する",
            "専門性と親しみやすさのバランスを取る"
        ],
        SalesType.CHALLENGER: [
            "従来の常識に疑問を投げかける",
            "新しい視点やアプローチを提示する",
            "顧客の思考を刺激する内容にする"
        ],
        SalesType.STORYTELLER: [
            "具体的な事例や物語を交える",
            "顧客がイメージしやすい内容にする",
            "感情に訴える要素を含める"
        ],
        SalesType.ANALYST: [
            "事実やデータに基づく内容にする",
            "論理的で分かりやすい説明を心がける",
            "顧客の理解を促進する"
        ],
        SalesType.PROBLEM_SOLVER: [
            "顧客が直面している課題に焦点を当てる",
            "解決への道筋を明確にする",
            "次の一歩を具体的に提示する"
        ],
        SalesType.FARMER: [
            "長期的な関係構築を意識する",
            "顧客の成長や発展を支援する姿勢を示す",
            "紹介や紹介の機会を創出する"
        ]
    }
    
    return advice.get(sales_type, [
        "顧客の反応を見ながら適切に調整する",
        "自然な流れで商談に導入する",
        "顧客の関心を引きつける内容にする"
    ])

def save_icebreakers(sales_type: SalesType, industry: str, icebreakers: list, company_hint: str = None, search_enabled: bool = True):
    """アイスブレイク結果をセッションに保存"""
    try:
        # セッションIDを生成
        session_id = str(uuid.uuid4())
        
        # 保存データを構築
        session_data = {
            "session_id": session_id,
            "type": "icebreaker",
            "created_at": datetime.now().isoformat(),
            "sales_type": sales_type.value,
            "industry": industry,
            "company_hint": company_hint,
            "search_enabled": search_enabled,
            "icebreakers": icebreakers,
            "emoji": get_sales_type_emoji(sales_type)
        }
        
        # セッション状態に保存
        if "icebreaker_sessions" not in st.session_state:
            st.session_state.icebreaker_sessions = {}

        st.session_state.icebreaker_sessions[session_id] = session_data
        
        # 履歴ページで表示できるように保存
        try:
            from services.storage_service import get_storage_provider

            provider = get_storage_provider()
            payload = {
                "type": "icebreaker",
                "input": {
                    "sales_type": sales_type.value,
                    "industry": industry,
                    "company_hint": company_hint,
                    "search_enabled": search_enabled,
                },
                "output": {
                    "icebreakers": icebreakers,
                    "emoji": get_sales_type_emoji(sales_type),
                    "sales_type": sales_type.value,
                    "industry": industry,
                },
            }
            provider.save_session(payload, session_id=session_id)
            provider.update_tags(session_id, [f"{sales_type.value}", f"{industry}業界"])
            st.success("履歴にも保存しました！履歴ページで確認できます。")

        except Exception as storage_error:
            st.warning(f"履歴への保存に失敗しました: {storage_error}")

        return session_id

    except Exception as e:
        st.error(f"保存に失敗しました: {e}")
        return None

def download_icebreakers_json(sales_type: SalesType, industry: str, icebreakers: list, company_hint: str = None, search_enabled: bool = True):
    """アイスブレイク結果をJSONファイルでダウンロード"""
    try:
        # ダウンロードデータを構築
        download_data = {
            "type": "icebreaker",
            "created_at": datetime.now().isoformat(),
            "sales_type": sales_type.value,
            "industry": industry,
            "company_hint": company_hint,
            "search_enabled": search_enabled,
            "icebreakers": icebreakers,
            "emoji": get_sales_type_emoji(sales_type)
        }
        
        # JSONファイルとしてダウンロード
        import io
        json_str = json.dumps(download_data, ensure_ascii=False, indent=2)
        
        st.download_button(
            label="📥 JSONファイルをダウンロード",
            data=json_str,
            file_name=f"icebreaker_{industry}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"ダウンロードに失敗しました: {e}")
