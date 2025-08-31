"""商談後ふりかえり解析サービス"""

import os
import yaml
from typing import Dict, Any

from core.models import SalesType
from providers.llm_openai import EnhancedOpenAIProvider
from services.error_handler import ServiceError, ConfigurationError
from services.logger import Logger
from services.utils import escape_braces, sanitize_for_prompt

logger = Logger("PostAnalyzerService")


class PostAnalyzerService:
    """商談後ふりかえり解析サービス"""

    def __init__(self) -> None:
        """初期化"""
        self.llm_provider = None
        self.prompt_template = None

        # プロンプトテンプレートの読み込み
        self._load_prompt_template()

        # LLMプロバイダーの取得
        try:
            from services.di_container import ServiceLocator

            self.llm_provider = ServiceLocator.get_service(EnhancedOpenAIProvider)
        except Exception as e:  # pragma: no cover - initialization failure
            logger.warning(f"LLMプロバイダーの取得に失敗: {e}")
    
    def _load_prompt_template(self):
        """プロンプトテンプレートを読み込み"""
        try:
            prompt_file = os.path.join("prompts", "post_review.yaml")
            if not os.path.exists(prompt_file):
                raise ConfigurationError(f"プロンプトファイルが見つかりません: {prompt_file}")
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
            
            self.prompt_template = prompt_data
            logger.info("プロンプトテンプレートを読み込みました")
            
        except Exception as e:
            logger.error(f"プロンプトテンプレートの読み込みに失敗: {e}")
            raise ConfigurationError(f"プロンプトテンプレートの読み込みに失敗: {e}")
    
    def analyze_meeting(self, 
                        meeting_content: str,
                        sales_type: SalesType,
                        industry: str,
                        product: str) -> Dict[str, Any]:
        """
        商談内容を分析
        
        Args:
            meeting_content: 商談の議事録やメモ
            sales_type: 営業タイプ
            industry: 業界
            product: 商品・サービス
            
        Returns:
            解析結果の辞書
        """
        if not self.llm_provider:
            logger.error("LLMプロバイダーが利用できません")
            raise ServiceError("LLMプロバイダーが利用できません", "dependency_missing")
        
        try:
            # プロンプトの構築
            prompt = self._build_prompt(meeting_content, sales_type, industry, product)
            
            # LLMによる解析
            logger.info("商談内容の解析を開始")
            response = self.llm_provider.call_llm(
                prompt=prompt,
                mode="deep",  # 深い分析のためdeepモード
                json_schema=self._get_analysis_schema()
            )
            
            logger.info("商談内容の解析が完了しました")
            return response
            
        except Exception as e:
            logger.error(f"LLMによる解析に失敗: {e}")
            logger.info("フォールバック解析を実行します")
            return self._generate_fallback_analysis(
                meeting_content, sales_type, industry, product
            )
    
    def _build_prompt(self, meeting_content: str, sales_type: SalesType, 
                      industry: str, product: str) -> str:
        """プロンプトを構築"""
        if not self.prompt_template:
            raise ConfigurationError("プロンプトテンプレートが読み込まれていません")
        
        # テンプレートの置換
        meeting_content_clean = escape_braces(sanitize_for_prompt(meeting_content))
        sales_type_clean = escape_braces(sanitize_for_prompt(sales_type.value))
        industry_clean = escape_braces(sanitize_for_prompt(industry))
        product_clean = escape_braces(sanitize_for_prompt(product))

        prompt = self.prompt_template['system'] + "\n\n"
        prompt += self.prompt_template['user'].format(
            meeting_content=meeting_content_clean,
            sales_type=sales_type_clean,
            industry=industry_clean,
            product=product_clean
        )

        return prompt
    
    def _get_analysis_schema(self) -> Dict[str, Any]:
        """解析結果のJSONスキーマを取得"""
        if not self.prompt_template:
            raise ConfigurationError("プロンプトテンプレートが読み込まれていません")
        
        # YAMLからスキーマを抽出（簡略化）
        schema_text = self.prompt_template.get('output_schema', '{}')
        
        # 基本的なスキーマ構造を返す
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "bant": {
                    "type": "object",
                    "properties": {
                        "budget": {"type": "string"},
                        "authority": {"type": "string"},
                        "need": {"type": "string"},
                        "timeline": {"type": "string"}
                    },
                    "required": ["budget", "authority", "need", "timeline"]
                },
                "champ": {
                    "type": "object",
                    "properties": {
                        "challenges": {"type": "string"},
                        "authority": {"type": "string"},
                        "money": {"type": "string"},
                        "prioritization": {"type": "string"}
                    },
                    "required": ["challenges", "authority", "money", "prioritization"]
                },
                "objections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string"},
                            "details": {"type": "string"},
                            "counter": {"type": "string"}
                        },
                        "required": ["theme", "details", "counter"]
                    }
                },
                "risks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "prob": {"type": "string"},
                            "reason": {"type": "string"},
                            "mitigation": {"type": "string"}
                        },
                        "required": ["type", "prob", "reason", "mitigation"]
                    }
                },
                "next_actions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "followup_email": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["subject", "body"]
                },
                "metrics_update": {
                    "type": "object",
                    "properties": {
                        "stage": {"type": "string"},
                        "win_prob_delta": {"type": "string"}
                    },
                    "required": ["stage", "win_prob_delta"]
                }
            },
            "required": [
                "summary", "bant", "champ", "objections", "risks", 
                "next_actions", "followup_email", "metrics_update"
            ]
        }
    
    def _generate_fallback_analysis(self, meeting_content: str, 
                                   sales_type: SalesType, industry: str, 
                                   product: str) -> Dict[str, Any]:
        """フォールバック解析（LLMが利用できない場合）"""
        logger.info("フォールバック解析を実行中")
        
        # 基本的な解析結果を生成
        return {
            "summary": f"{industry}業界の{product}に関する商談の振り返り分析",
            "bant": {
                "budget": "未取得",
                "authority": "未取得",
                "need": "未取得",
                "timeline": "未取得"
            },
            "champ": {
                "challenges": "未取得",
                "authority": "未取得",
                "money": "未取得",
                "prioritization": "未取得"
            },
            "objections": [
                {
                    "theme": "未取得",
                    "details": "未取得",
                    "counter": "未取得"
                }
            ],
            "risks": [
                {
                    "type": "未取得",
                    "prob": "未取得",
                    "reason": "未取得",
                    "mitigation": "未取得"
                }
            ],
            "next_actions": [
                "商談内容を詳細に記録し、再度分析を実行してください"
            ],
            "followup_email": {
                "subject": "商談の振り返りについて",
                "body": "商談内容の詳細を確認させていただき、改めてご連絡いたします。"
            },
            "metrics_update": {
                "stage": "未取得",
                "win_prob_delta": "0%"
            }
        }
    
    def get_analysis_schema(self) -> Dict[str, Any]:
        """解析結果のスキーマを取得（外部からの利用用）"""
        return self._get_analysis_schema()

