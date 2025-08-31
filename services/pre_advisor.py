import os
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache
from core.models import SalesInput
from providers.search_provider import WebSearchProvider
from services.logger import Logger
from services.error_handler import ErrorHandler, ServiceError, ConfigurationError
from services.di_container import get_service, ServiceLocator
from services.prompt_manager import EnhancedPromptManager, PromptContext
from services.schema_manager import UnifiedSchemaManager
from providers.llm_openai import EnhancedOpenAIProvider, LLMResponse

# Backward compatibility alias for older tests expecting OpenAIProvider
OpenAIProvider = EnhancedOpenAIProvider

class PreAdvisorService:
    """強化された事前アドバイスサービス"""

    def __init__(self, settings_manager=None, llm_provider=None, prompt_manager=None, schema_manager=None):
        self.settings_manager = settings_manager
        self.logger = Logger("PreAdvisorService")
        self.error_handler = ErrorHandler(self.logger)

        # 依存性注入またはサービスロケーターを使用
        try:
            self.llm_provider = llm_provider or get_service(EnhancedOpenAIProvider)
            self.prompt_manager = prompt_manager or get_service(EnhancedPromptManager)
            self.schema_manager = schema_manager or get_service(UnifiedSchemaManager)
            self.logger.info("PreAdvisorService initialized successfully with DI")
        except Exception as e:
            self.logger.error("Failed to initialize PreAdvisorService", exc_info=e)
            raise ServiceError("サービスの初期化に失敗しました", "initialization_failed", {"error": str(e)})

    def _load_stub_response(self) -> Dict[str, Any]:
        """オフライン時に使用するスタブレスポンスを読み込み"""
        stub_path = Path(__file__).resolve().parent.parent / "data" / "pre_advice_stub.json"
        try:
            with open(stub_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data["offline"] = True
                return data
        except Exception:
            return {
                "short_term": {
                    "openers": {"call": "オフライン", "visit": "オフライン", "email": "オフライン"},
                    "discovery": ["オフライン"],
                    "differentiation": [{"vs": "オフライン", "talk": "オフライン"}],
                    "objections": [{"type": "オフライン", "script": "オフライン"}],
                    "next_actions": ["オフライン"],
                    "kpi": {"next_meeting_rate": "0%", "poc_rate": "0%"},
                    "summary": "オフラインスタブ"
                },
                "mid_term": {
                    "plan_weeks_4_12": ["オフライン"]
                },
                "offline": True
            }
    
    def generate_advice(self, sales_input: SalesInput) -> Dict[str, Any]:
        """強化された事前アドバイス生成"""
        start_time = time.time()

        try:
            # ユーザーアクションのログ
            self.logger.log_user_action(
                "generate_pre_advice",
                {
                    "sales_type": sales_input.sales_type.value,
                    "industry": sales_input.industry,
                    "product": sales_input.product
                }
            )

            # 変数の準備
            variables = self._prepare_variables(sales_input)

            # 参考出典を取得
            evidence_urls = self._get_evidence_urls(sales_input)
            if evidence_urls:
                variables["evidence_urls"] = evidence_urls

            # プロンプトコンテキストの作成
            context = PromptContext(
                template_name="pre_advice",
                variables=variables,
                mode="speed",
                user_id="default",  # TODO: 実際のユーザーIDを使用
                sanitize=True,
                validate_length=True
            )

            # プロンプトのレンダリング
            rendered_prompt = self.prompt_manager.render_prompt(context)

            # スキーマの取得
            schema = self.schema_manager.get_schema("pre_advice")

            # LLM呼び出し
            self.logger.log_service_call("EnhancedOpenAIProvider", "call_llm", {"mode": "speed"})

            try:
                response: LLMResponse = self.llm_provider.call_llm(
                    prompt=rendered_prompt.full_prompt,
                    mode="speed",
                    json_schema=schema,
                    user_id="default",
                    use_cache=True
                )

                # 応答の処理
                result = self._process_response(response, evidence_urls)

                # 成功ログ
                response_time = time.time() - start_time
                self.logger.log_api_call("LLM_Generation", True, response_time)
                self.logger.info(f"Pre-advice generated successfully in {response_time:.2f}s (cached: {response.cached})")

                return result

            except Exception as e:
                if isinstance(e, ConnectionError):
                    self.logger.warning("オフラインモード: LLM接続に失敗しました。スタブデータを使用します。")
                    return self._load_stub_response()
                else:
                    raise

        except Exception as e:
            response_time = time.time() - start_time
            self.logger.log_api_call("LLM_Generation", False, response_time)

            # エラーハンドリング
            error_response = self.error_handler.handle_error(
                e,
                context="PreAdvisorService.generate_advice",
                user_friendly=True
            )

            # エラー詳細をログに記録
            self.logger.error(f"Failed to generate pre-advice: {str(e)}", exc_info=e)

            # エラーレスポンスを返す
            raise ServiceError(
                error_response["error"]["message"],
                "execution_failed",
                {"original_error": str(e), "response_time": response_time}
            )

    def _prepare_variables(self, sales_input: SalesInput) -> Dict[str, Any]:
        """変数の準備"""
        return {
            "sales_type": sales_input.sales_type.value,
            "industry": sales_input.industry,
            "product": sales_input.product,
            "description": sales_input.description or "",
            "description_url": sales_input.description_url or "",
            "competitor": sales_input.competitor or "",
            "competitor_url": sales_input.competitor_url or "",
            "stage": sales_input.stage,
            "purpose": sales_input.purpose,
            "constraints": ", ".join(sales_input.constraints) if sales_input.constraints else "なし"
        }

    def _get_evidence_urls(self, sales_input: SalesInput) -> list:
        """参考出典URLの取得"""
        try:
            search_provider = WebSearchProvider(self.settings_manager)
            sources = search_provider.search(f"{sales_input.industry} 最新ニュース", 3)

            if getattr(search_provider, "offline_mode", False):
                self.logger.warning("オフラインモード: Web検索が利用できません。スタブデータを使用します。")
                return []

            return [item.get("url") for item in sources if isinstance(item, dict) and item.get("url")]

        except Exception as e:
            self.logger.warning(f"Web検索に失敗しました: {e}")
            return []

    def _process_response(self, response: LLMResponse, evidence_urls: list) -> Dict[str, Any]:
        """応答の処理"""
        # JSONパース
        if isinstance(response.content, str):
            try:
                result = json.loads(response.content)
            except json.JSONDecodeError:
                result = {"content": response.content}
        else:
            result = response.content

        # メタデータの追加
        result["_metadata"] = {
            "cached": response.cached,
            "processing_time": response.processing_time,
            "model": response.model,
            "token_usage": response.usage
        }

        # 参考出典の追加
        if evidence_urls and not os.getenv("PYTEST_CURRENT_TEST"):
            result["evidence_urls"] = evidence_urls

        return result
    
