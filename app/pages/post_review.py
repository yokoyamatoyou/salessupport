"""
商談後ふりかえり解析ページ
"""
import streamlit as st
import json
from typing import List
from core.models import SalesType
from services.post_analyzer import PostAnalyzerService
from services.settings_manager import SettingsManager
from services.storage_service import get_storage_provider
from datetime import datetime
from components.sales_type import sales_type_selectbox
from components.copy_button import copy_button
from translations import t

def show_post_review_page():
    st.header(t("post_review_header"))
    st.write(t("post_review_desc"))
    
    # セッション状態の初期化
    if 'post_review_form_data' not in st.session_state:
        st.session_state.post_review_form_data = {}
    
    # 入力フォーム
    with st.form("post_review_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            sales_type = sales_type_selectbox(key="post_review_sales_type")
            
            industry = st.text_input(
                t("post_review_industry_label"),
                placeholder="例: IT、製造業、金融業",
                help="対象となる業界を入力してください",
                key="post_review_industry"
            )
            
            product = st.text_input(
                t("post_review_product_label"),
                placeholder="例: SaaS、コンサルティング",
                help="提供する商品・サービスを入力してください",
                key="post_review_product"
            )
        
        with col2:
            # 商談結果の基本情報
            meeting_date = st.date_input(
                "商談日 *",
                value=datetime.now().date(),
                key="post_review_meeting_date"
            )
            
            meeting_duration = st.selectbox(
                "商談時間",
                options=["30分未満", "30分-1時間", "1-2時間", "2時間以上"],
                key="post_review_duration"
            )
            
            meeting_type = st.selectbox(
                "商談形態",
                options=["初回訪問", "提案", "商談", "クロージング", "その他"],
                key="post_review_type"
            )
        
        # 商談内容の詳細入力
        st.markdown("### 📝 商談内容の詳細")
        
        meeting_content = st.text_area(
            "商談の議事録・メモ *",
            placeholder="商談で話し合った内容、顧客の反応、課題、次回の予定などを詳しく記録してください...",
            height=200,
            help="できるだけ詳細に記録することで、より精度の高い分析が可能になります",
            key="post_review_content"
        )
        
        # 顧客の反応・課題
        col1, col2 = st.columns(2)
        with col1:
            customer_reaction = st.selectbox(
                "顧客の反応",
                options=["非常に良い", "良い", "普通", "悪い", "非常に悪い", "不明"],
                key="post_review_reaction"
            )
        
        with col2:
            challenges = st.text_input(
                "主な課題・懸念",
                placeholder="例: 価格、機能、競合、タイミング",
                key="post_review_challenges"
            )
        
        # 次回予定
        next_meeting = st.text_input(
            "次回商談予定",
            placeholder="例: 来週火曜日、来月、未定",
            key="post_review_next"
        )
        
        # ファイルアップロード（オプション）
        uploaded_file = st.file_uploader(
            "議事録ファイル（オプション）",
            type=['txt', 'md', 'docx'],
            help="テキストファイルやMarkdownファイルをアップロードできます"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.type == "text/plain":
                    file_content = uploaded_file.read().decode("utf-8")
                else:
                    # その他のファイル形式の処理（簡略化）
                    file_content = f"ファイル内容: {uploaded_file.name}"
                
                st.info(f"📎 ファイル '{uploaded_file.name}' がアップロードされました")
                if st.button("📋 ファイル内容を商談内容に反映"):
                    st.session_state.post_review_content = file_content
                    st.rerun()
                    
            except Exception as e:
                st.error(f"ファイルの読み込みに失敗しました: {e}")
        
        # 分析実行ボタン
        submitted = st.form_submit_button("🔍 分析を実行", type="primary")
    
    # フォーム送信後の処理
    if submitted:
        if not all([sales_type, industry, product, meeting_content]):
            st.error("❌ 必須項目（営業タイプ、業界、商品・サービス、商談内容）を入力してください")
            return
        
        try:
            with st.spinner("🤖 AIが商談内容を分析中..."):
                # 設定マネージャーを初期化
                settings_manager = SettingsManager()
                
                # 分析サービスを初期化
                analyzer = PostAnalyzerService(settings_manager)
                
                # 分析実行
                analysis_result = analyzer.analyze_meeting(
                    meeting_content=meeting_content,
                    sales_type=sales_type,
                    industry=industry,
                    product=product
                )
            
            # 成功メッセージ
            st.success("✅ 商談内容の分析が完了しました！")
            
            # 分析結果を表示
            display_analysis_result(analysis_result)
            
            # 保存機能
            if st.button("💾 分析結果を保存", use_container_width=False):
                session_id = save_post_review(
                    sales_type=sales_type,
                    industry=industry,
                    product=product,
                    meeting_date=meeting_date,
                    meeting_duration=meeting_duration,
                    meeting_type=meeting_type,
                    meeting_content=meeting_content,
                    customer_reaction=customer_reaction,
                    challenges=challenges,
                    next_meeting=next_meeting,
                    analysis_result=analysis_result
                )
                st.success(f"結果を保存しました（Session ID: {session_id}）")
                
        except Exception as e:
            st.error(f"❌ 分析の実行に失敗しました: {str(e)}")
            st.info("しばらく時間をおいて再度お試しください。問題が続く場合は管理者にお問い合わせください。")

def display_analysis_result(analysis: dict):
    """分析結果の表示"""
    st.markdown("---")
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
        color: white;
    ">
        <h2 style="margin: 0; color: white;">🔍 分析結果</h2>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">商談の振り返りと次回への改善点をご確認ください</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 要約
    if "summary" in analysis:
        st.markdown("### 📋 商談の要約")
        st.info(analysis["summary"])
    
    # BANT分析
    if "bant" in analysis:
        st.markdown("### 🎯 BANT分析")
        bant = analysis["bant"]
        
        col1, col2 = st.columns(2)
        with col1:
            if "budget" in bant:
                st.metric("💰 予算", bant["budget"])
            if "authority" in bant:
                st.metric("👑 権限", bant["authority"])
        
        with col2:
            if "need" in bant:
                st.metric("🎯 ニーズ", bant["need"])
            if "timeline" in bant:
                st.metric("⏰ タイムライン", bant["timeline"])
    
    # CHAMP分析
    if "champ" in analysis:
        st.markdown("### 🏆 CHAMP分析")
        champ = analysis["champ"]
        
        col1, col2 = st.columns(2)
        with col1:
            if "challenges" in champ:
                st.metric("🚧 課題", champ["challenges"])
            if "authority" in champ:
                st.metric("👑 権限・影響力", champ["authority"])
        
        with col2:
            if "money" in champ:
                st.metric("💰 資金", champ["money"])
            if "prioritization" in champ:
                st.metric("⭐ 優先度", champ["prioritization"])
    
    # 反論対応
    if "objections" in analysis and analysis["objections"]:
        st.markdown("### 🛡️ 反論への対応策")
        for i, objection in enumerate(analysis["objections"], 1):
            if isinstance(objection, dict):
                with st.expander(f"反論 {i}: {objection.get('theme', 'テーマ')}", expanded=True):
                    if "details" in objection:
                        st.markdown(f"**詳細：** {objection['details']}")
                    if "counter" in objection:
                        st.markdown(f"**対応策：** {objection['counter']}")
                        
                        # コピーボタン
                        copy_button(objection['counter'], key=f"copy_objection_{i}", use_container_width=True)
    
    # リスク分析
    if "risks" in analysis and analysis["risks"]:
        st.markdown("### ⚠️ リスク分析")
        for i, risk in enumerate(analysis["risks"], 1):
            if isinstance(risk, dict):
                risk_color = {
                    "high": "#ef4444",
                    "medium": "#f59e0b", 
                    "low": "#10b981"
                }.get(risk.get("prob", "medium"), "#6b7280")
                
                st.markdown(f"""
                <div style="
                    border-left: 4px solid {risk_color};
                    padding: 15px;
                    margin: 10px 0;
                    background: #f9fafb;
                    border-radius: 0 8px 8px 0;
                ">
                    <h4 style="margin: 0 0 10px 0; color: #374151;">リスク {i}: {risk.get('type', 'タイプ')}</h4>
                    <p style="margin: 5px 0; color: #6b7280;"><strong>確率:</strong> {risk.get('prob', '不明')}</p>
                    <p style="margin: 5px 0; color: #6b7280;"><strong>理由:</strong> {risk.get('reason', '不明')}</p>
                    <p style="margin: 5px 0; color: #6b7280;"><strong>軽減策:</strong> {risk.get('mitigation', '不明')}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # 次のアクション
    if "next_actions" in analysis and analysis["next_actions"]:
        st.markdown("### 🚀 次のアクション")
        for i, action in enumerate(analysis["next_actions"], 1):
            st.markdown(f"""
            <div style="
                background: #f0f9ff;
                border-left: 4px solid #0ea5e9;
                padding: 15px;
                margin: 10px 0;
                border-radius: 0 8px 8px 0;
            ">
                <p style="margin: 0; color: #0c4a6e;">{i}. {action}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # コピーボタン
            copy_button(action, key=f"copy_action_{i}", use_container_width=True)
    
    # フォローアップメール
    if "followup_email" in analysis:
        st.markdown("### 📧 フォローアップメール")
        email = analysis["followup_email"]
        
        if "subject" in email and "body" in email:
            st.markdown("**件名：**")
            st.code(email["subject"], language="text")
            
            st.markdown("**本文：**")
            st.code(email["body"], language="text")
            
            # メール全体をコピー
            full_email = f"件名: {email['subject']}\n\n{email['body']}"
            copy_button(full_email, key="copy_email", label="📋 メール全体をコピー", use_container_width=True)
    
    # 指標更新
    if "metrics_update" in analysis:
        st.markdown("### 📊 営業指標の更新")
        metrics = analysis["metrics_update"]
        
        col1, col2 = st.columns(2)
        with col1:
            if "stage" in metrics:
                st.metric("現在のステージ", metrics["stage"])
        with col2:
            if "win_prob_delta" in metrics:
                st.metric("勝率の変化", metrics["win_prob_delta"])
    
    # 全体をコピー
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**📋 全体をコピー：**")
    with col2:
        formatted_json = json.dumps(analysis, ensure_ascii=False, indent=2)
        copy_button(formatted_json, key="copy_all", label="📋 全体コピー", use_container_width=True)

def save_post_review(**kwargs) -> str:
    """商談後ふりかえり解析の結果をセッション形式で保存し、Session IDを返す"""
    try:
        provider = get_storage_provider()
        payload = {
            "type": "post_review",
            "input": {
                "sales_type": kwargs.get("sales_type"),
                "industry": kwargs.get("industry"),
                "product": kwargs.get("product"),
                "meeting_date": str(kwargs.get("meeting_date")),
                "meeting_duration": kwargs.get("meeting_duration"),
                "meeting_type": kwargs.get("meeting_type"),
                "meeting_content": kwargs.get("meeting_content"),
                "customer_reaction": kwargs.get("customer_reaction"),
                "challenges": kwargs.get("challenges"),
                "next_meeting": kwargs.get("next_meeting"),
            },
            "output": {
                "analysis_result": kwargs.get("analysis_result"),
            },
        }
        session_id = provider.save_session(payload)
        return session_id
    except Exception as e:
        st.error(f"保存に失敗しました: {str(e)}")
        raise

