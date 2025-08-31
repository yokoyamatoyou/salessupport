"""
検索機能の高度化サービス
LLMの知識を活用して検索結果の品質向上とスコアリングアルゴリズムを改善
"""

import yaml
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from urllib.parse import urlparse
from string import Template
from core.models import AppSettings
from providers.llm_openai import OpenAIProvider
from providers.search_provider import WebSearchProvider
from services.error_handler import ErrorHandler
from services.logger import Logger
from services.utils import escape_braces, sanitize_for_prompt

class SearchEnhancerService:
    """検索機能の高度化サービス"""

    def __init__(self, settings_manager=None, llm_provider=None, search_provider=None):
        self.settings_manager = settings_manager
        self.logger = Logger()
        self.error_handler = ErrorHandler(self.logger)
        self.prompts = self._load_prompts()

        if llm_provider is not None:
            self.llm_provider = llm_provider
        else:
            try:
                self.llm_provider = OpenAIProvider()
            except Exception as e:
                self.logger.warning(f"OpenAIProviderの初期化に失敗: {e}")
                self.llm_provider = None

        self.search_provider = search_provider or WebSearchProvider(settings_manager)
        
    def _load_prompts(self) -> Dict[str, Any]:
        """プロンプトテンプレートを読み込み"""
        try:
            with open("prompts/search_enhancement.yaml", "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"検索高度化プロンプトの読み込みに失敗: {e}")
            return {}
    
    def enhance_search_query(self, original_query: str, industry: str = "", purpose: str = "") -> Dict[str, Any]:
        """検索クエリの最適化"""
        try:
            if not self.prompts.get("query_optimization"):
                return {"error": "プロンプトテンプレートが見つかりません"}

            prompt = self.prompts["query_optimization"]
            try:
                user_prompt = Template(prompt["user"]).safe_substitute(
                    original_query=escape_braces(sanitize_for_prompt(original_query)),
                    industry=escape_braces(sanitize_for_prompt(industry or "未指定")),
                    purpose=escape_braces(sanitize_for_prompt(purpose or "一般的な調査")),
                )
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    context="SearchEnhancerService.enhance_search_query.template",
                )
                return {"error": f"テンプレート処理に失敗: {e}"}
            full_prompt = f"{prompt['system']}\n{user_prompt}"

            if not self.llm_provider:
                return self._fallback_query_optimization(original_query, industry)

            schema = prompt.get("schema")
            return self.llm_provider.call_llm(full_prompt, "speed", json_schema=schema)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                context="SearchEnhancerService.enhance_search_query",
            )
            return {"error": f"クエリ最適化に失敗: {e}"}
    def _fallback_query_optimization(self, query: str, industry: str) -> Dict[str, Any]:
        """フォールバック用のクエリ最適化"""
        # 基本的なクエリ最適化ロジック
        optimized_queries = []
        
        # 業界別のキーワード追加
        industry_keywords = {
            "IT": ["テクノロジー", "デジタル", "AI", "クラウド"],
            "製造業": ["製造", "生産", "サプライチェーン", "DX"],
            "金融業": ["金融", "フィンテック", "投資", "ESG"],
            "医療": ["医療", "ヘルスケア", "テレメディシン", "AI診断"],
            "小売": ["小売", "EC", "顧客体験", "サステナビリティ"]
        }
        
        # 元のクエリを基本として保持
        optimized_queries.append({
            "query": query,
            "reason": "元のクエリをそのまま使用",
            "expected_improvement": "基本的な検索結果"
        })
        
        # 業界別の最適化
        if industry in industry_keywords:
            enhanced_query = f"{query} {industry_keywords[industry][0]}"
            optimized_queries.append({
                "query": enhanced_query,
                "reason": f"{industry}業界の主要キーワードを追加",
                "expected_improvement": "業界特化型の検索結果"
            })
        
        # 時事性を考慮した最適化
        time_enhanced_query = f"{query} 最新 2024 2025"
        optimized_queries.append({
            "query": time_enhanced_query,
            "reason": "時事性を考慮したキーワードを追加",
            "expected_improvement": "最新情報の検索結果"
        })
        
        return {
            "optimized_queries": optimized_queries,
            "search_strategy": "フォールバック処理による基本的なクエリ最適化"
        }
    
    def assess_search_quality(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """検索結果の品質評価"""
        try:
            if not self.prompts.get("quality_assessment"):
                return {"error": "プロンプトテンプレートが見つかりません"}

            prompt = self.prompts["quality_assessment"]

            sanitized_query = escape_braces(sanitize_for_prompt(query))
            sanitized_results: List[Dict[str, Any]] = []
            for r in search_results:
                sanitized_r = {
                    k: escape_braces(sanitize_for_prompt(v)) if isinstance(v, str) else v
                    for k, v in r.items()
                }
                sanitized_results.append(sanitized_r)

            try:
                user_prompt = Template(prompt["user"]).safe_substitute(
                    query=sanitized_query,
                    search_results=json.dumps(sanitized_results, ensure_ascii=False, indent=2),
                )
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    context="SearchEnhancerService.assess_search_quality.template",
                )
                return {"error": f"テンプレート処理に失敗: {e}"}

            full_prompt = f"{prompt['system']}\n{user_prompt}"

            if not self.llm_provider:
                return self._fallback_quality_assessment(query, search_results)

            schema = prompt.get("schema")
            return self.llm_provider.call_llm(full_prompt, "deep", json_schema=schema)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                context="SearchEnhancerService.assess_search_quality",
            )
            return {"error": f"品質評価に失敗: {e}"}
    def _fallback_quality_assessment(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """フォールバック用の品質評価"""
        quality_scores = []
        
        for result in search_results:
            score = self._calculate_fallback_score(result, query)
            quality_scores.append({
                "url": result.get("url", ""),
                "reliability_score": score["reliability"],
                "relevance_score": score["relevance"],
                "freshness_score": score["freshness"],
                "overall_score": score["overall"],
                "reasoning": score["reasoning"],
                "improvement_suggestions": score["suggestions"]
            })
        
        return {
            "quality_scores": quality_scores,
            "overall_assessment": "フォールバック処理による基本的な品質評価"
        }
    
    def _calculate_fallback_score(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """フォールバック用のスコア計算"""
        # 信頼性スコア（ドメイン、ソースに基づく）
        reliability_score = 0.5  # デフォルト
        if result.get("source") == "cse":
            reliability_score = 0.7
        elif result.get("source") == "newsapi":
            reliability_score = 0.8
        
        # ドメインの信頼性チェック
        url = result.get("url", "")
        if url:
            hostname = urlparse(url).netloc
            trusted_domains = ["www.nikkei.com", "www.bloomberg.co.jp", "www.reuters.com"]
            if any(trusted in hostname for trusted in trusted_domains):
                reliability_score = min(1.0, reliability_score + 0.2)
        
        # 関連性スコア（キーワードマッチング）
        relevance_score = 0.0
        query_keywords = [w.lower() for w in re.split(r"\s+", query) if len(w) >= 2]
        text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
        
        if query_keywords:
            matches = sum(1 for k in query_keywords if k in text)
            relevance_score = min(1.0, matches / len(query_keywords))
        
        # 新鮮度スコア
        freshness_score = 0.5  # デフォルト
        published_at = result.get("published_at")
        if published_at:
            try:
                dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                days_old = (datetime.now(timezone.utc) - dt).days
                if days_old <= 7:
                    freshness_score = 1.0
                elif days_old <= 30:
                    freshness_score = 0.8
                elif days_old <= 90:
                    freshness_score = 0.6
                else:
                    freshness_score = 0.3
            except Exception:
                pass
        
        # 総合スコア
        overall_score = (reliability_score * 0.4 + relevance_score * 0.4 + freshness_score * 0.2)
        
        # 推奨事項
        suggestions = []
        if reliability_score < 0.6:
            suggestions.append("より信頼できる情報源からの情報を確認")
        if relevance_score < 0.5:
            suggestions.append("検索クエリの見直しを検討")
        if freshness_score < 0.5:
            suggestions.append("より新しい情報源の確認を推奨")
        
        return {
            "reliability": round(reliability_score, 3),
            "relevance": round(relevance_score, 3),
            "freshness": round(freshness_score, 3),
            "overall": round(overall_score, 3),
            "reasoning": f"信頼性: {reliability_score:.1f}, 関連性: {relevance_score:.1f}, 新鮮度: {freshness_score:.1f}",
            "suggestions": suggestions
        }
    
    def get_industry_search_strategy(self, industry: str, purpose: str, time_period: str = "60日") -> Dict[str, Any]:
        """業界別検索戦略の取得"""
        try:
            if not self.prompts.get("industry_search_strategy"):
                return {"error": "プロンプトテンプレートが見つかりません"}

            prompt = self.prompts["industry_search_strategy"]
            try:
                user_prompt = Template(prompt["user"]).safe_substitute(
                    industry=escape_braces(sanitize_for_prompt(industry)),
                    purpose=escape_braces(sanitize_for_prompt(purpose)),
                    time_period=escape_braces(sanitize_for_prompt(time_period)),
                )
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    context="SearchEnhancerService.get_industry_search_strategy.template",
                )
                return {"error": f"テンプレート処理に失敗: {e}"}
            full_prompt = f"{prompt['system']}\n{user_prompt}"

            if not self.llm_provider:
                return self._fallback_industry_strategy(industry, purpose)

            response = self.llm_provider.call_llm(full_prompt, "speed")
            content = response.get("content", "")

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return self._fallback_industry_strategy(industry, purpose)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                context="SearchEnhancerService.get_industry_search_strategy",
            )
            return {"error": f"業界戦略の取得に失敗: {e}"}
    
    def _fallback_industry_strategy(self, industry: str, purpose: str) -> Dict[str, Any]:
        """フォールバック用の業界戦略"""
        # 業界別の基本戦略
        strategies = {
            "IT": {
                "trusted_sources": ["TechCrunch", "Wired", "MIT Technology Review"],
                "keyword_strategy": {
                    "primary_keywords": ["AI", "クラウド", "DX", "デジタル変革"],
                    "secondary_keywords": ["テクノロジー", "イノベーション", "スタートアップ"],
                    "exclude_keywords": ["古い", "廃止"]
                },
                "time_considerations": "IT業界は変化が早いため、3ヶ月以内の情報を重視",
                "search_approach": "最新技術動向と実用例を組み合わせた検索",
                "quality_indicators": ["技術的詳細", "実用例", "専門家の見解"]
            },
            "製造業": {
                "trusted_sources": ["日経ものづくり", "日経ビジネス", "Bloomberg"],
                "keyword_strategy": {
                    "primary_keywords": ["製造", "生産性", "サプライチェーン", "DX"],
                    "secondary_keywords": ["自動化", "IoT", "品質管理"],
                    "exclude_keywords": ["古い", "非効率"]
                },
                "time_considerations": "製造業の変化は比較的緩やか、6ヶ月以内の情報で十分",
                "search_approach": "実用的な導入事例と効果測定を重視",
                "quality_indicators": ["具体的な数値", "導入事例", "ROI"]
            }
        }
        
        return strategies.get(industry, {
            "trusted_sources": ["一般的なビジネスメディア"],
            "keyword_strategy": {
                "primary_keywords": [industry, "業界動向", "トレンド"],
                "secondary_keywords": ["最新", "分析", "予測"],
                "exclude_keywords": ["古い", "廃止"]
            },
            "time_considerations": "業界特性に応じて3-6ヶ月以内の情報を重視",
            "search_approach": "業界の特性を考慮した包括的な検索",
            "quality_indicators": ["信頼性", "関連性", "時効性"]
        })
    
    def integrate_search_results(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """検索結果の統合と要約"""
        try:
            if not self.prompts.get("result_integration"):
                return {"error": "プロンプトテンプレートが見つかりません"}

            prompt = self.prompts["result_integration"]

            sanitized_query = escape_braces(sanitize_for_prompt(query))
            sanitized_results: List[Dict[str, Any]] = []
            for r in search_results:
                sanitized_r = {
                    k: escape_braces(sanitize_for_prompt(v)) if isinstance(v, str) else v
                    for k, v in r.items()
                }
                sanitized_results.append(sanitized_r)

            try:
                user_prompt = Template(prompt["user"]).safe_substitute(
                    query=sanitized_query,
                    search_results=json.dumps(sanitized_results, ensure_ascii=False, indent=2),
                )
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    context="SearchEnhancerService.integrate_search_results.template",
                )
                return {"error": f"テンプレート処理に失敗: {e}"}

            full_prompt = f"{prompt['system']}\n{user_prompt}"

            if not self.llm_provider:
                return self._fallback_result_integration(query, search_results)

            response = self.llm_provider.call_llm(full_prompt, "deep")
            content = response.get("content", "")

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return self._fallback_result_integration(query, search_results)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                context="SearchEnhancerService.integrate_search_results",
            )
            return {"error": f"結果統合に失敗: {e}"}
    
    def _fallback_result_integration(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """フォールバック用の結果統合"""
        # 基本的な結果統合ロジック
        all_text = " ".join([
            f"{r.get('title', '')} {r.get('snippet', '')}"
            for r in search_results
        ]).lower()
        
        # キーワードの出現頻度を分析
        keywords = [w for w in re.split(r"\s+", query) if len(w) >= 2]
        keyword_frequency = {}
        for keyword in keywords:
            keyword_frequency[keyword] = all_text.count(keyword.lower())
        
        # 主要洞察の抽出
        key_insights = []
        for keyword, freq in sorted(keyword_frequency.items(), key=lambda x: x[1], reverse=True):
            if freq > 0:
                key_insights.append(f"'{keyword}'に関する情報が{freq}回言及されている")
        
        # トレンドの抽出
        trends = []
        if any("最新" in r.get("title", "") or "新" in r.get("title", "") for r in search_results):
            trends.append("最新技術・トレンドへの関心が高い")
        
        if any("AI" in r.get("title", "") or "人工知能" in r.get("title", "") for r in search_results):
            trends.append("AI技術への注目が継続")
        
        # 機会とリスクの抽出
        opportunities = []
        risks = []
        
        if any("成長" in r.get("title", "") or "拡大" in r.get("title", "") for r in search_results):
            opportunities.append("市場の成長機会が確認できる")
        
        if any("課題" in r.get("title", "") or "問題" in r.get("title", "") for r in search_results):
            risks.append("業界の課題が明らかになっている")
        
        return {
            "key_insights": key_insights[:3],
            "trends": trends[:2],
            "opportunities": opportunities[:2],
            "risks": risks[:2],
            "recommendations": [
                {
                    "action": "検索結果の詳細分析",
                    "priority": "中",
                    "rationale": "基本的な統合分析が完了",
                    "expected_outcome": "より深い洞察の獲得"
                }
            ],
            "confidence_level": "中",
            "data_gaps": "LLMによる詳細分析が必要"
        }
    
    def enhanced_search(self, query: str, industry: str = "", purpose: str = "", num_results: int = 5) -> Dict[str, Any]:
        """高度化された検索の実行"""
        try:
            # 1. クエリ最適化
            query_optimization = self.enhance_search_query(query, industry, purpose)
            
            # 2. 最適化されたクエリで検索実行
            optimized_query = query
            if query_optimization.get("optimized_queries"):
                # 最初の最適化クエリを使用
                optimized_query = query_optimization["optimized_queries"][0]["query"]
            
            search_results = self.search_provider.search(optimized_query, num_results)
            
            # 3. 品質評価
            quality_assessment = self.assess_search_quality(query, search_results)
            
            # 4. 結果統合
            result_integration = self.integrate_search_results(query, search_results)
            
            # 5. 業界戦略の取得
            industry_strategy = self.get_industry_search_strategy(industry, purpose)
            
            return {
                "original_query": query,
                "optimized_query": optimized_query,
                "query_optimization": query_optimization,
                "search_results": search_results,
                "quality_assessment": quality_assessment,
                "result_integration": result_integration,
                "industry_strategy": industry_strategy,
                "enhancement_metadata": {
                    "enhanced_at": datetime.now(timezone.utc).isoformat(),
                    "enhancement_version": "1.0",
                    "llm_used": "gpt-4" if self.llm_provider else "none"
                }
            }
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                context="SearchEnhancerService.enhanced_search",
            )
            return {"error": f"高度化検索に失敗: {e}"}
    
    def get_continuous_improvement_plan(self, current_challenges: str, improvement_goals: str, available_resources: str) -> Dict[str, Any]:
        """検索品質の継続改善計画の取得"""
        try:
            if not self.prompts.get("continuous_improvement"):
                return {"error": "プロンプトテンプレートが見つかりません"}

            prompt = self.prompts["continuous_improvement"]
            try:
                user_prompt = Template(prompt["user"]).safe_substitute(
                    current_challenges=escape_braces(sanitize_for_prompt(current_challenges)),
                    improvement_goals=escape_braces(sanitize_for_prompt(improvement_goals)),
                    available_resources=escape_braces(sanitize_for_prompt(available_resources)),
                )
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    context="SearchEnhancerService.get_continuous_improvement_plan.template",
                )
                return {"error": f"テンプレート処理に失敗: {e}"}
            full_prompt = f"{prompt['system']}\n{user_prompt}"

            if not self.llm_provider:
                return self._fallback_improvement_plan(current_challenges, improvement_goals)

            response = self.llm_provider.call_llm(full_prompt, "speed")
            content = response.get("content", "")

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return self._fallback_improvement_plan(current_challenges, improvement_goals)

        except Exception as e:
            self.error_handler.handle_error(
                e,
                context="SearchEnhancerService.get_continuous_improvement_plan",
            )
            return {"error": f"改善計画の取得に失敗: {e}"}
    
    def _fallback_improvement_plan(self, current_challenges: str, improvement_goals: str) -> Dict[str, Any]:
        """フォールバック用の改善計画"""
        return {
            "short_term_improvements": [
                {
                    "action": "検索結果の品質指標の測定",
                    "timeline": "1-2週間",
                    "expected_impact": "現在の品質レベルを把握",
                    "success_metrics": ["品質スコアの測定", "ユーザー満足度の調査"]
                }
            ],
            "long_term_strategy": {
                "vision": "継続的な検索品質の向上",
                "key_initiatives": ["LLM活用の拡大", "ユーザーフィードバックの収集"],
                "milestones": ["3ヶ月後の品質向上", "6ヶ月後の自動化"]
            },
            "measurement_framework": {
                "quality_metrics": ["検索精度", "結果の関連性", "情報の新鮮度"],
                "user_satisfaction_metrics": ["ユーザー評価", "再検索率"],
                "business_impact_metrics": ["検索成功率", "ユーザーエンゲージメント"]
            },
            "implementation_plan": "段階的な改善の実施"
        }
