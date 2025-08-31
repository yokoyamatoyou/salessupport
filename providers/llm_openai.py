"""
Enhanced OpenAI Provider with Security, Caching, and Latest Features
"""
import os
import json
import logging
import asyncio
from typing import Literal, Dict, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from abc import ABC, abstractmethod

from openai import (
    OpenAI,
    AsyncOpenAI,
    RateLimitError,
    BadRequestError,
    AuthenticationError,
    APIError,
)
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from jsonschema import validate as jsonschema_validate, ValidationError

from services.error_handler import LLMError
from services.usage_meter import UsageMeter
from services.security_utils import (
    PromptSecurityManager,
    TokenTracker,
    SanitizeResult,
    PromptAnalysis
)


logger = logging.getLogger(__name__)

# モデル設定
MODEL_CONFIGS = {
    "gpt-4o-mini": {
        "max_tokens": 4096,
        "supports_reasoning": False,
        "supports_structured_output": True,
    },
    "gpt-4.1-mini-2025-04-14": {
        "max_tokens": 32768,
        "context_window": 32768,
        "supports_reasoning": True,
        "supports_structured_output": True,
    },
}

# モード別設定（旧インターフェース互換）
MODE_CONFIGS = {
    "speed": {
        "temperature": 0.3,
        "top_p": 0.9,
        "reasoning_effort": "low",
        "max_tokens": 1200,
    },
    "deep": {
        "temperature": 0.2,
        "reasoning_effort": "medium",
        "max_tokens": 2000,
    },
    "creative": {
        "temperature": 0.7,
        "top_p": 0.9,
        "reasoning_effort": "low",
        "max_tokens": 800,
    },
}


@dataclass
class LLMConfig:
    """LLM設定"""
    model: str = "gpt-4.1-mini-2025-04-14"
    temperature: float = 0.3
    max_tokens: int = 2000
    reasoning_effort: str = "low"
    top_p: float = 0.9
    enable_caching: bool = True
    enable_streaming: bool = False


@dataclass
class LLMResponse:
    """LLM応答"""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    cached: bool = False
    processing_time: float = 0.0


class CacheInterface(ABC):
    """キャッシュインターフェース"""

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass


class InMemoryCache(CacheInterface):
    """インメモリキャッシュ実装"""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, str] = {}
        self.max_size = max_size

    def get(self, key: str) -> Optional[str]:
        return self.cache.get(key)

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        if len(self.cache) >= self.max_size:
            # 単純なLRU: 最初のアイテムを削除
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        self.cache[key] = value

    def exists(self, key: str) -> bool:
        return key in self.cache


class EnhancedOpenAIProvider:
    """強化されたOpenAIプロバイダー"""

    def __init__(self, config: Optional[LLMConfig] = None, cache: Optional[CacheInterface] = None):
        self.config = config or LLMConfig()
        self.cache = cache or InMemoryCache()
        self.security_manager = PromptSecurityManager()
        self.token_tracker = TokenTracker()
        self.client = self._create_client()
        self.async_client = self._create_async_client()

    def _create_client(self) -> OpenAI:
        """OpenAIクライアントを作成"""
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError("OPENAI_API_KEYが設定されていません")

        return OpenAI(api_key=api_key)

    def _create_async_client(self) -> AsyncOpenAI:
        """非同期OpenAIクライアントを作成"""
        api_key = self._get_api_key()
        if not api_key:
            return None

        return AsyncOpenAI(api_key=api_key)

    def _get_api_key(self) -> Optional[str]:
        """APIキーを取得（環境変数またはSecret Manager）"""
        api_key = os.getenv("OPENAI_API_KEY")

        # Secret Managerからの取得
        if not api_key:
            secret_name = os.getenv("OPENAI_API_SECRET_NAME")
            project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")

            if secret_name and project_id:
                try:
                    from google.cloud import secretmanager
                    client = secretmanager.SecretManagerServiceClient()
                    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
                    response = client.access_secret_version(name=secret_path)
                    api_key = response.payload.data.decode("UTF-8")
                except Exception as e:
                    logger.warning(f"Secret ManagerからのAPIキー取得に失敗: {e}")
                    api_key = None

        return api_key
    
    def get_mode_config(self, mode: str) -> Dict[str, Any]:
        """指定されたモードの設定を取得"""
        if mode not in MODE_CONFIGS:
            raise ValueError(f"Unknown mode: {mode}")

        base_config = MODE_CONFIGS[mode].copy()
        model_config = MODEL_CONFIGS.get(self.config.model, {})

        # モデルの最大トークン数で制限
        max_tokens = model_config.get("max_tokens", 32768)
        base_config["max_tokens"] = min(base_config["max_tokens"], max_tokens)

        return base_config
    
    def call_llm(
        self,
        prompt: str,
        mode: str,
        json_schema: Optional[Dict[str, Any]] = None,
        user_id: str = "default",
        use_cache: bool = True
    ) -> LLMResponse:
        """
        強化されたLLM呼び出し

        Args:
            prompt: プロンプトテキスト
            mode: モード ("speed", "deep", "creative")
            json_schema: JSONスキーマ（オプション）
            user_id: ユーザーID
            use_cache: キャッシュを使用するか

        Returns:
            LLMResponse: 応答オブジェクト
        """
        import time
        start_time = time.time()

        # 1. セキュリティチェックとサニタイズ
        sanitize_result = self.security_manager.sanitize_input(prompt)
        if not sanitize_result.is_safe:
            logger.warning(f"Unsafe prompt detected: {sanitize_result.warnings}")
            # 警告はあるが処理は継続（ログに記録）

        # 2. プロンプト長検証
        if not self.security_manager.validate_prompt_length(sanitize_result.text):
            raise LLMError("プロンプトが長すぎます", error_code="prompt_too_long")

        # 3. 使用量チェック
        if UsageMeter.get_tokens(user_id) >= UsageMeter.get_limit(user_id):
            raise LLMError("使用上限に達しました", error_code="rate_limit")

        # 4. キャッシュチェック
        cache_key = None
        if use_cache and self.config.enable_caching:
            cache_key = self.security_manager.generate_prompt_hash(
                sanitize_result.text, mode, json_schema
            )
            cached_response = self.cache.get(cache_key)
            if cached_response:
                try:
                    cached_data = json.loads(cached_response)
                    processing_time = time.time() - start_time
                    return LLMResponse(
                        content=cached_data["content"],
                        usage=cached_data["usage"],
                        model=cached_data["model"],
                        finish_reason=cached_data["finish_reason"],
                        cached=True,
                        processing_time=processing_time
                    )
                except (json.JSONDecodeError, KeyError):
                    logger.warning("Invalid cache data, proceeding with API call")

        # 5. LLM呼び出し
        try:
            response = self._call_openai_api(
                sanitize_result.text, mode, json_schema, user_id
            )

            processing_time = time.time() - start_time

            # 6. キャッシュ保存
            if cache_key and self.config.enable_caching:
                cache_data = {
                    "content": response.content,
                    "usage": response.usage,
                    "model": response.model,
                    "finish_reason": response.finish_reason
                }
                self.cache.set(cache_key, json.dumps(cache_data))

            response.processing_time = processing_time
            return response

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"LLM call failed after {processing_time:.2f}s", exc_info=e)
            raise

    def _call_openai_api(
        self,
        prompt: str,
        mode: str,
        json_schema: Optional[Dict[str, Any]],
        user_id: str
    ) -> LLMResponse:
        """OpenAI APIを呼び出し"""
        mode_config = self.get_mode_config(mode)
        model_config = MODEL_CONFIGS.get(self.config.model, {})

        # システムメッセージ
        system_message = "あなたは日本のトップ営業コーチです。"
        if json_schema:
            system_message += "指定されたJSONスキーマに厳密に従って回答してください。"

        # リクエスト構築
        request_params = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": mode_config["temperature"],
            "max_tokens": mode_config["max_tokens"],
        }
        if "top_p" in mode_config:
            request_params["top_p"] = mode_config["top_p"]

        # Reasoning effort（対応モデルの場合）
        if model_config.get("supports_reasoning"):
            request_params["reasoning_effort"] = mode_config["reasoning_effort"]

        # Structured output（対応モデルの場合）
        if json_schema and model_config.get("supports_structured_output", True):
            request_params["response_format"] = {
                "type": "json_schema",
                "json_schema": json_schema,
                "strict": True,
            }

        # API呼び出し（リトライ付き）
        try:
            response = self._execute_with_retry(request_params, user_id)
        except RateLimitError as e:
            raise LLMError("APIレート制限に達しました。しばらく待ってから再試行してください。") from e
        except APIError as e:
            raise LLMError(f"LLM呼び出しでエラーが発生しました: {e}") from e

        # 応答処理
        choice = response.choices[0]
        finish_reason = getattr(choice, "finish_reason", "stop")
        refusal = getattr(getattr(choice, "message", None), "refusal", None)

        if finish_reason != "stop" or refusal:
            logger.error(f"LLM call not completed: finish_reason={finish_reason}, refusal={refusal}")
            raise LLMError("モデルがリクエストを完了できませんでした")

        content = choice.message.content or ""

        # JSONスキーマがある場合はパースと検証
        if json_schema:
            try:
                parsed_response = json.loads(content)
                if not self._validate_schema(parsed_response, json_schema):
                    raise ValueError("LLMの応答が期待されるスキーマに従っていません")
                content = json.dumps(parsed_response, ensure_ascii=False)
            except json.JSONDecodeError as e:
                raise ValueError(f"LLMの応答をJSONとしてパースできませんでした: {e}")

        # トークン使用量追跡
        token_usage = self.token_tracker.track_usage(response, user_id)

        # 使用量チェック
        total_tokens = UsageMeter.add_tokens(user_id, token_usage["total_tokens"])
        if total_tokens > UsageMeter.get_limit(user_id):
            raise LLMError("使用上限に達しました", error_code="rate_limit")

        return LLMResponse(
            content=content,
            usage=token_usage,
            model=self.config.model,
            finish_reason=finish_reason,
            cached=False
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=8),
        retry=retry_if_exception_type((RateLimitError, APIError)),
        reraise=True,
    )
    def _execute_with_retry(self, request_params: Dict[str, Any], user_id: str):
        """Call OpenAI with retry for rate limit and transient errors."""
        try:
            return self.client.chat.completions.create(**request_params)
        except RateLimitError as e:
            logger.error("Rate limit exceeded", exc_info=e)
            raise
        except BadRequestError as e:
            logger.error("Bad request", exc_info=e)
            raise LLMError("APIクォータが不足しています") from e
        except AuthenticationError as e:
            logger.error("Invalid API key", exc_info=e)
            raise LLMError("無効なAPIキーです") from e
        except APIError as e:
            logger.error("OpenAI API error", exc_info=e)
            raise

    def _validate_schema(self, response: Dict[str, Any], expected_schema: Dict[str, Any]) -> bool:
        """スキーマ検証"""
        try:
            jsonschema_validate(instance=response, schema=expected_schema)
            return True
        except (ValidationError, Exception):
            return False

    async def call_llm_stream(
        self,
        prompt: str,
        mode: str,
        json_schema: Optional[Dict[str, Any]] = None,
        user_id: str = "default"
    ) -> AsyncGenerator[str, None]:
        """
        ストリーミング応答

        Args:
            prompt: プロンプト
            mode: モード
            json_schema: JSONスキーマ
            user_id: ユーザーID

        Yields:
            ストリーミングチャンク
        """
        if not self.async_client:
            raise LLMError("非同期クライアントが利用できません")

        # セキュリティチェック
        sanitize_result = self.security_manager.sanitize_input(prompt)
        if not sanitize_result.is_safe:
            logger.warning(f"Unsafe prompt detected in stream: {sanitize_result.warnings}")

        mode_config = self.get_mode_config(mode)

        request_params = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "あなたは日本のトップ営業コーチです。"},
                {"role": "user", "content": sanitize_result.text}
            ],
            "temperature": mode_config["temperature"],
            "max_tokens": mode_config["max_tokens"],
            "stream": True
        }

        try:
            async for chunk in await self.async_client.chat.completions.create(**request_params):
                if chunk.choices:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
        except Exception as e:
            logger.error("Streaming error", exc_info=e)
            raise LLMError(f"ストリーミングでエラーが発生しました: {e}") from e


# 後方互換性のためのラッパークラス
class OpenAIProvider:
    """Compatibility wrapper exposing the original simple interface."""

    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager

        model = os.getenv("OPENAI_MODEL")
        temperature = 0.3
        max_tokens = 1200
        if settings_manager:
            settings = settings_manager.load_settings()
            temperature = getattr(settings, "temperature", temperature)
            max_tokens = getattr(settings, "max_tokens", max_tokens)
            model = model or getattr(settings, "openai_model", None)

        # Clamp values to safe ranges
        temperature = max(0.0, min(2.0, temperature))
        max_tokens = max(1, min(4000, max_tokens))

        config = LLMConfig(model=model or "gpt-4o-mini", temperature=temperature, max_tokens=max_tokens)
        self.enhanced_provider = EnhancedOpenAIProvider(config=config)

    def _get_default_modes(self):
        """Recreate the legacy MODES dictionary with clamped values."""
        t = self.enhanced_provider.config.temperature
        max_tok = self.enhanced_provider.config.max_tokens
        return {
            "speed": {"temperature": t, "top_p": 0.9, "max_tokens": max_tok},
            "deep": {"temperature": round(t * 0.8, 3), "max_tokens": max_tok},
            "creative": {"temperature": t, "max_tokens": int(max_tok * 0.8)},
        }

    @property
    def MODES(self):
        return self._get_default_modes()

    @property
    def client(self):
        return self.enhanced_provider.client

    def call_llm(
        self,
        prompt: str,
        mode: str,
        json_schema: Optional[Dict[str, Any]] = None,
        user_id: str = "default",
    ) -> Dict[str, Any]:
        """古いインターフェースとの互換性を維持"""
        try:
            response = self.enhanced_provider.call_llm(
                prompt=prompt,
                mode=mode,
                json_schema=json_schema,
                user_id=user_id,
                use_cache=False,
            )

            # JSONスキーマがある場合はパースして返す
            if json_schema and response.content:
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    pass

            # プレーンテキストの場合は古いフォーマットで返す
            return {"content": response.content}

        except Exception as e:
            # エラーの場合も古いインターフェースに合わせる
            raise e

    def validate_schema(self, response: Dict[str, Any], expected_schema: Dict[str, Any]) -> bool:
        """スキーマ検証（後方互換性）"""
        return self.enhanced_provider._validate_schema(response, expected_schema)

