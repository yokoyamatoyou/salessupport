"""
検索機能の高度化ページ
LLMの知識を活用した検索結果の品質向上とスコアリングアルゴリズムの改善
"""

import os
import streamlit as st
import json
from datetime import datetime
from services.search_enhancer import SearchEnhancerService
from services.settings_manager import SettingsManager
from services.storage_service import get_storage_provider
from translations import t

def main():
    st.set_page_config(
        page_title=t("search_enhancement_title"),
        page_icon="🔍",
        layout="wide"
    )

    st.title(t("search_enhancement_title"))
    st.markdown(t("search_enhancement_desc"))

    missing_keys = [k for k in ("CSE_API_KEY", "NEWSAPI_KEY") if not os.getenv(k)]
    if missing_keys:
        st.warning(f"未設定のAPIキー: {', '.join(missing_keys)}")
    
    # サービスの初期化
    try:
        settings_manager = SettingsManager()
        search_enhancer = SearchEnhancerService(settings_manager)
        storage_provider = get_storage_provider()
    except Exception as e:
        st.error(f"サービスの初期化に失敗しました: {e}")
        return
    
    # サイドバー設定
    with st.sidebar:
        st.header(t("tab_search"))
        
        # 検索タイプの選択
        search_type = st.selectbox(
            "検索タイプ",
            ["クエリ最適化", "品質評価", "業界戦略", "結果統合", "継続改善", "高度化検索"],
            help="実行したい検索機能の種類を選択してください"
        )
        
        # 業界の選択
        industry = st.selectbox(
            "業界",
            ["", "IT", "製造業", "金融業", "医療", "小売", "その他"],
            help="検索対象の業界を選択してください"
        )
        
        # 検索目的
        purpose = st.text_area(
            "検索目的",
            placeholder="例: 競合分析、市場調査、技術動向把握...",
            help="検索の目的や背景を記述してください"
        )
        
        # 結果数の設定
        num_results = st.slider(
            "検索結果数",
            min_value=3,
            max_value=10,
            value=5,
            help="取得する検索結果の数を設定してください"
        )
    
    # メインコンテンツ
    if search_type == "クエリ最適化":
        show_query_optimization(search_enhancer, industry, purpose)
    elif search_type == "品質評価":
        show_quality_assessment(search_enhancer)
    elif search_type == "業界戦略":
        show_industry_strategy(search_enhancer, industry, purpose)
    elif search_type == "結果統合":
        show_result_integration(search_enhancer)
    elif search_type == "継続改善":
        show_continuous_improvement(search_enhancer)
    elif search_type == "高度化検索":
        show_enhanced_search(search_enhancer, industry, purpose, num_results)

def show_query_optimization(search_enhancer, industry, purpose):
    """クエリ最適化の表示"""
    st.header("🔧 検索クエリ最適化")
    st.markdown("元の検索クエリを最適化して、より効果的な検索結果を得られるようにします")
    
    # クエリ入力
    original_query = st.text_input(
        "元の検索クエリ",
        placeholder="例: AI技術 製造業 最新動向",
        help="最適化したい検索クエリを入力してください"
    )
    
    if st.button("クエリを最適化", type="primary"):
        if not original_query:
            st.warning("検索クエリを入力してください")
            return
        
        with st.spinner("クエリ最適化を実行中..."):
            try:
                result = search_enhancer.enhance_search_query(original_query, industry, purpose)
                
                if "error" in result:
                    st.error(f"クエリ最適化に失敗しました: {result['error']}")
                    return
                
                # 最適化されたクエリの表示
                st.success("クエリ最適化が完了しました！")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("元のクエリ")
                    st.info(original_query)
                
                with col2:
                    st.subheader("最適化されたクエリ")
                    if result.get("optimized_queries"):
                        for i, opt_query in enumerate(result["optimized_queries"][:3]):
                            with st.expander(f"最適化案 {i+1}: {opt_query['query']}"):
                                st.write(f"**理由:** {opt_query['reason']}")
                                st.write(f"**期待される改善:** {opt_query['expected_improvement']}")
                
                # 検索戦略の表示
                if result.get("search_strategy"):
                    st.subheader("検索戦略")
                    st.info(result["search_strategy"])
                
                # 結果の保存
                if st.button("最適化結果を保存"):
                    save_optimization_result(original_query, result, industry, purpose)
                    
            except Exception as e:
                st.error(f"クエリ最適化の実行中にエラーが発生しました: {e}")

def show_quality_assessment(search_enhancer):
    """品質評価の表示"""
    st.header("📊 検索結果の品質評価")
    st.markdown("検索結果の信頼性、関連性、時効性を総合的に評価します")
    
    # 検索クエリ入力
    query = st.text_input(
        "検索クエリ",
        placeholder="例: AI技術 製造業 最新動向",
        help="評価対象の検索クエリを入力してください"
    )
    
    # 検索結果の入力（JSON形式）
    search_results_json = st.text_area(
        "検索結果（JSON形式）",
        placeholder='[{"title": "記事タイトル", "url": "https://...", "snippet": "記事の要約"}]',
        help="評価したい検索結果をJSON形式で入力してください"
    )
    
    if st.button("品質評価を実行", type="primary"):
        if not query or not search_results_json:
            st.warning("検索クエリと検索結果を入力してください")
            return
        
        try:
            search_results = json.loads(search_results_json)
        except json.JSONDecodeError:
            st.error("検索結果のJSON形式が正しくありません")
            return
        
        with st.spinner("品質評価を実行中..."):
            try:
                result = search_enhancer.assess_search_quality(query, search_results)
                
                if "error" in result:
                    st.error(f"品質評価に失敗しました: {result['error']}")
                    return
                
                st.success("品質評価が完了しました！")
                
                # 品質スコアの表示
                if result.get("quality_scores"):
                    st.subheader("品質スコア詳細")
                    
                    for score_data in result["quality_scores"]:
                        with st.expander(f"URL: {score_data['url'][:50]}..."):
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("信頼性", f"{score_data['reliability_score']:.3f}")
                            with col2:
                                st.metric("関連性", f"{score_data['relevance_score']:.3f}")
                            with col3:
                                st.metric("新鮮度", f"{score_data['freshness_score']:.3f}")
                            with col4:
                                st.metric("総合スコア", f"{score_data['overall_score']:.3f}")
                            
                            st.write(f"**評価根拠:** {score_data['reasoning']}")
                            
                            if score_data.get("improvement_suggestions"):
                                st.write("**改善提案:**")
                                for suggestion in score_data["improvement_suggestions"]:
                                    st.write(f"• {suggestion}")
                
                # 全体評価の表示
                if result.get("overall_assessment"):
                    st.subheader("全体評価")
                    st.info(result["overall_assessment"])
                
            except Exception as e:
                st.error(f"品質評価の実行中にエラーが発生しました: {e}")

def show_industry_strategy(search_enhancer, industry, purpose):
    """業界戦略の表示"""
    st.header("🏭 業界別検索戦略")
    st.markdown("各業界の特性に応じた最適な検索アプローチを提案します")
    
    if not industry:
        st.warning("サイドバーで業界を選択してください")
        return
    
    if not purpose:
        st.warning("サイドバーで検索目的を入力してください")
        return
    
    # 対象期間の設定
    time_period = st.selectbox(
        "対象期間",
        ["7日", "30日", "60日", "90日", "180日"],
        help="検索対象とする期間を選択してください"
    )
    
    if st.button("業界戦略を取得", type="primary"):
        with st.spinner("業界戦略を取得中..."):
            try:
                result = search_enhancer.get_industry_search_strategy(industry, purpose, time_period)
                
                if "error" in result:
                    st.error(f"業界戦略の取得に失敗しました: {result['error']}")
                    return
                
                st.success("業界戦略の取得が完了しました！")
                
                # 信頼できる情報源
                if result.get("trusted_sources"):
                    st.subheader("信頼できる情報源")
                    for source in result["trusted_sources"]:
                        st.write(f"• {source}")
                
                # キーワード戦略
                if result.get("keyword_strategy"):
                    st.subheader("キーワード戦略")
                    strategy = result["keyword_strategy"]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**主要キーワード:**")
                        for keyword in strategy.get("primary_keywords", []):
                            st.write(f"• {keyword}")
                    
                    with col2:
                        st.write("**補助キーワード:**")
                        for keyword in strategy.get("secondary_keywords", []):
                            st.write(f"• {keyword}")
                    
                    with col3:
                        st.write("**除外キーワード:**")
                        for keyword in strategy.get("exclude_keywords", []):
                            st.write(f"• {keyword}")
                
                # 時効性の考慮事項
                if result.get("time_considerations"):
                    st.subheader("時効性の考慮事項")
                    st.info(result["time_considerations"])
                
                # 検索アプローチ
                if result.get("search_approach"):
                    st.subheader("推奨する検索アプローチ")
                    st.success(result["search_approach"])
                
                # 品質指標
                if result.get("quality_indicators"):
                    st.subheader("品質指標")
                    for indicator in result["quality_indicators"]:
                        st.write(f"• {indicator}")
                
            except Exception as e:
                st.error(f"業界戦略の取得中にエラーが発生しました: {e}")

def show_result_integration(search_enhancer):
    """結果統合の表示"""
    st.header("🔗 検索結果の統合と要約")
    st.markdown("複数の検索結果から一貫性のある洞察を抽出し、アクション可能な推奨事項を提示します")
    
    # 検索クエリ入力
    query = st.text_input(
        "検索クエリ",
        placeholder="例: AI技術 製造業 最新動向",
        help="統合対象の検索クエリを入力してください"
    )
    
    # 検索結果の入力（JSON形式）
    search_results_json = st.text_area(
        "検索結果（JSON形式）",
        placeholder='[{"title": "記事タイトル", "url": "https://...", "snippet": "記事の要約"}]',
        help="統合したい検索結果をJSON形式で入力してください"
    )
    
    if st.button("結果統合を実行", type="primary"):
        if not query or not search_results_json:
            st.warning("検索クエリと検索結果を入力してください")
            return
        
        try:
            search_results = json.loads(search_results_json)
        except json.JSONDecodeError:
            st.error("検索結果のJSON形式が正しくありません")
            return
        
        with st.spinner("結果統合を実行中..."):
            try:
                result = search_enhancer.integrate_search_results(query, search_results)
                
                if "error" in result:
                    st.error(f"結果統合に失敗しました: {result['error']}")
                    return
                
                st.success("結果統合が完了しました！")
                
                # 主要洞察
                if result.get("key_insights"):
                    st.subheader("🔍 主要洞察")
                    for insight in result["key_insights"]:
                        st.write(f"• {insight}")
                
                # トレンド
                if result.get("trends"):
                    st.subheader("📈 トレンド")
                    for trend in result["trends"]:
                        st.write(f"• {trend}")
                
                # 機会
                if result.get("opportunities"):
                    st.subheader("💡 機会")
                    for opportunity in result["opportunities"]:
                        st.write(f"• {opportunity}")
                
                # リスク
                if result.get("risks"):
                    st.subheader("⚠️ リスク")
                    for risk in result["risks"]:
                        st.write(f"• {risk}")
                
                # 推奨事項
                if result.get("recommendations"):
                    st.subheader("🎯 推奨事項")
                    for rec in result["recommendations"]:
                        with st.expander(f"{rec['action']} (優先度: {rec['priority']})"):
                            st.write(f"**理由:** {rec['rationale']}")
                            st.write(f"**期待される結果:** {rec['expected_outcome']}")
                
                # 信頼度とデータギャップ
                col1, col2 = st.columns(2)
                
                with col1:
                    if result.get("confidence_level"):
                        st.metric("信頼度", result["confidence_level"])
                
                with col2:
                    if result.get("data_gaps"):
                        st.write("**データの不足・制限事項:**")
                        st.info(result["data_gaps"])
                
            except Exception as e:
                st.error(f"結果統合の実行中にエラーが発生しました: {e}")

def show_continuous_improvement(search_enhancer):
    """継続改善の表示"""
    st.header("🔄 検索品質の継続改善")
    st.markdown("検索結果の品質を継続的に向上させるための戦略と指標を提案します")
    
    # 現在の課題
    current_challenges = st.text_area(
        "現在の課題",
        placeholder="例: 検索結果の関連性が低い、古い情報が多い、信頼性の評価が困難...",
        help="現在直面している検索品質の課題を記述してください"
    )
    
    # 改善目標
    improvement_goals = st.text_area(
        "改善目標",
        placeholder="例: 検索精度の向上、ユーザー満足度の向上、検索速度の改善...",
        help="達成したい改善目標を記述してください"
    )
    
    # 利用可能なリソース
    available_resources = st.text_area(
        "利用可能なリソース",
        placeholder="例: 開発チーム3名、月間予算50万円、3ヶ月の開発期間...",
        help="利用可能なリソース（人・予算・時間）を記述してください"
    )
    
    if st.button("改善計画を取得", type="primary"):
        if not current_challenges or not improvement_goals or not available_resources:
            st.warning("すべての項目を入力してください")
            return
        
        with st.spinner("改善計画を取得中..."):
            try:
                result = search_enhancer.get_continuous_improvement_plan(
                    current_challenges, improvement_goals, available_resources
                )
                
                if "error" in result:
                    st.error(f"改善計画の取得に失敗しました: {result['error']}")
                    return
                
                st.success("改善計画の取得が完了しました！")
                
                # 短期的な改善策
                if result.get("short_term_improvements"):
                    st.subheader("📅 短期的な改善策")
                    for improvement in result["short_term_improvements"]:
                        with st.expander(f"{improvement['action']} ({improvement['timeline']})"):
                            st.write(f"**期待される効果:** {improvement['expected_impact']}")
                            st.write("**成功指標:**")
                            for metric in improvement.get("success_metrics", []):
                                st.write(f"• {metric}")
                
                # 長期的な戦略
                if result.get("long_term_strategy"):
                    st.subheader("🎯 長期的な戦略")
                    strategy = result["long_term_strategy"]
                    
                    if strategy.get("vision"):
                        st.write(f"**ビジョン:** {strategy['vision']}")
                    
                    if strategy.get("key_initiatives"):
                        st.write("**主要イニシアチブ:**")
                        for initiative in strategy["key_initiatives"]:
                            st.write(f"• {initiative}")
                    
                    if strategy.get("milestones"):
                        st.write("**マイルストーン:**")
                        for milestone in strategy["milestones"]:
                            st.write(f"• {milestone}")
                
                # 測定フレームワーク
                if result.get("measurement_framework"):
                    st.subheader("📊 測定フレームワーク")
                    framework = result["measurement_framework"]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**品質指標:**")
                        for metric in framework.get("quality_metrics", []):
                            st.write(f"• {metric}")
                    
                    with col2:
                        st.write("**ユーザー満足度指標:**")
                        for metric in framework.get("user_satisfaction_metrics", []):
                            st.write(f"• {metric}")
                    
                    with col3:
                        st.write("**ビジネスインパクト指標:**")
                        for metric in framework.get("business_impact_metrics", []):
                            st.write(f"• {metric}")
                
                # 実装計画
                if result.get("implementation_plan"):
                    st.subheader("🚀 実装計画")
                    st.info(result["implementation_plan"])
                
            except Exception as e:
                st.error(f"改善計画の取得中にエラーが発生しました: {e}")

def show_enhanced_search(search_enhancer, industry, purpose, num_results):
    """高度化検索の表示"""
    st.header("🚀 高度化された検索")
    st.markdown("LLMの知識を活用した包括的な検索機能を実行します")

    query = st.text_input(
        "検索クエリ",
        placeholder="例: AI技術 製造業 最新動向",
        help="検索したいキーワードやトピックを入力してください",
    )

    if st.button("高度化検索を実行", type="primary"):
        if not query:
            st.warning("検索クエリを入力してください")
            return

        with st.spinner("高度化検索を実行中..."):
            try:
                opt_result = search_enhancer.enhance_search_query(query, industry, purpose)
                if "error" in opt_result:
                    st.error(f"クエリ最適化に失敗しました: {opt_result['error']}")
                    return

                optimized_query = query
                if opt_result.get("optimized_queries"):
                    optimized_query = opt_result["optimized_queries"][0]["query"]

                search_results = search_enhancer.search_provider.search(optimized_query, num_results)
                quality = search_enhancer.assess_search_quality(query, search_results)

                st.success("高度化検索が完了しました！")

                st.subheader("🔧 クエリ最適化")
                if opt_result.get("optimized_queries"):
                    for i, opt_query in enumerate(opt_result["optimized_queries"][:3]):
                        with st.expander(f"最適化案 {i+1}: {opt_query['query']}"):
                            st.write(f"**理由:** {opt_query['reason']}")
                            st.write(f"**期待される改善:** {opt_query['expected_improvement']}")
                if opt_result.get("search_strategy"):
                    st.write(f"**検索戦略:** {opt_result['search_strategy']}")

                st.subheader("📋 検索結果")
                if search_results:
                    for item in search_results:
                        with st.container(border=True):
                            st.markdown(f"**[{item.get('title', 'タイトルなし')}]({item.get('url', '#')})**")
                            st.write(item.get('snippet', 'N/A'))
                            meta = []
                            if item.get('source'):
                                meta.append(item['source'])
                            if item.get('published_at'):
                                meta.append(item['published_at'])
                            if meta:
                                st.caption(' | '.join(meta))
                            if item.get('score'):
                                st.metric('スコア', f"{item['score']:.3f}")
                            if item.get('reasons'):
                                st.write('**理由:**')
                                for reason in item['reasons']:
                                    st.write(f"• {reason}")
                else:
                    st.info("検索結果がありません")

                if quality and quality.get('quality_scores'):
                    st.subheader("📊 品質評価")
                    for score_data in quality['quality_scores']:
                        with st.container(border=True):
                            st.markdown(f"**{score_data['url']}**")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("信頼性", f"{score_data.get('reliability_score',0):.3f}")
                            with col2:
                                st.metric("関連性", f"{score_data.get('relevance_score',0):.3f}")
                            with col3:
                                st.metric("新鮮度", f"{score_data.get('freshness_score',0):.3f}")
                            with col4:
                                st.metric("総合スコア", f"{score_data.get('overall_score',0):.3f}")
                            st.write(f"**評価根拠:** {score_data.get('reasoning','')}")
                            if score_data.get('improvement_suggestions'):
                                for suggestion in score_data['improvement_suggestions']:
                                    st.write(f"• {suggestion}")

                if st.button("高度化検索結果を保存"):
                    save_enhanced_search_result(
                        {
                            "original_query": query,
                            "optimized_query": optimized_query,
                            "query_optimization": opt_result,
                            "search_results": search_results,
                            "quality_assessment": quality,
                        },
                        industry,
                        purpose,
                    )

            except Exception as e:
                st.error(f"高度化検索の実行中にエラーが発生しました: {e}")
def save_optimization_result(original_query, result, industry, purpose):
    """最適化結果の保存"""
    try:
        storage_provider = get_storage_provider()
        
        session_data = {
            "type": "query_optimization",
            "created_at": datetime.now().isoformat(),
            "input": {
                "original_query": original_query,
                "industry": industry,
                "purpose": purpose
            },
            "output": result,
            "tags": ["クエリ最適化", "検索高度化"]
        }
        
        session_id = storage_provider.save_session(session_data)
        st.success(f"最適化結果が保存されました。セッションID: {session_id}")
        
    except Exception as e:
        st.error(f"結果の保存に失敗しました: {e}")

def save_enhanced_search_result(result, industry, purpose):
    """高度化検索結果の保存"""
    try:
        storage_provider = get_storage_provider()
        
        # 保存データの作成
        data = {
            "type": "enhanced_search",
            "timestamp": datetime.now().isoformat(),
            "industry": industry,
            "purpose": purpose,
            "result": result
        }
        
        # ファイル名の生成
        filename = f"enhanced_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 保存
        storage_provider.save_data(filename, data)
        st.success(f"検索結果を {filename} に保存しました")
        
    except Exception as e:
        st.error(f"保存に失敗しました: {e}")

def show_enhanced_search_page():
    """検索機能の高度化ページを表示"""
    main()

if __name__ == "__main__":
    main()
