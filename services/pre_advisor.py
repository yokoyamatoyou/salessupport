"""Pre-advice generation service.

This module provides a lightweight implementation of the pre-advice service
used by the tests.  A previous refactor replaced the original version with a
much more complex dependency injected variant which no longer exposed the
minimal interface expected by the tests.  The rewritten module restores that
interface while keeping the implementation clear and well documented.

The service loads a prompt template from ``prompts/pre_advice.yaml`` and uses
an ``OpenAIProvider`` (a thin wrapper around the enhanced provider) to call the
LLM.  Helper methods are provided for building a sanitized prompt, handling
errors, and falling back to stub data when offline.
"""

from __future__ import annotations

from pathlib import Path
from string import Template
from typing import Any, Dict, Optional
import json
import re

import yaml

from core.models import SalesInput
from providers.llm_openai import OpenAIProvider
from providers.search_provider import WebSearchProvider  # pragma: no cover - for test compatibility
from services.error_handler import ErrorHandler, ConfigurationError, ServiceError
from services.logger import Logger


class PreAdvisorService:
    """Generate structured pre-meeting advice for a given ``SalesInput``."""

    def __init__(self, settings_manager: Optional[Any] = None, llm_provider: Optional[OpenAIProvider] = None) -> None:
        self.settings_manager = settings_manager
        self.logger = Logger("PreAdvisorService")
        self.error_handler = ErrorHandler(self.logger)

        # Allow tests to inject a mocked provider
        self.llm_provider = llm_provider or OpenAIProvider()

        # Load prompt template used to build LLM prompts
        self.prompt_template = self._load_prompt_template()

    # ------------------------------------------------------------------
    # Prompt loading and building
    def _load_prompt_template(self) -> Dict[str, Any]:
        """Load YAML prompt template.

        Raises
        ------
        ConfigurationError
            If the prompt template file cannot be found or parsed.
        """

        path = Path("prompts/pre_advice.yaml")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if not isinstance(data, dict):
                    raise ValueError("template must be a mapping")
                return data
        except FileNotFoundError as e:  # pragma: no cover - configuration issue
            raise ConfigurationError("プロンプトファイル 'prompts/pre_advice.yaml' が見つかりません") from e
        except Exception as e:  # pragma: no cover - unexpected
            raise ConfigurationError(f"プロンプトファイルの読み込みに失敗しました: {e}") from e

    def _sanitize(self, text: str) -> str:
        """Remove HTML tags and role prefixes from user supplied text."""

        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"(?i)(system|assistant|user):", "", text)
        return text

    def _build_prompt(self, sales_input: SalesInput) -> str:
        """Build the final prompt string for the LLM call."""

        user_tpl = Template(self.prompt_template.get("user", ""))
        user_part = user_tpl.safe_substitute(
            sales_type=sales_input.sales_type.value,
            industry=self._sanitize(sales_input.industry),
            product=self._sanitize(sales_input.product),
            description=self._sanitize(sales_input.description or ""),
            competitor=self._sanitize(sales_input.competitor or ""),
            stage=self._sanitize(sales_input.stage),
            purpose=self._sanitize(sales_input.purpose),
            constraints="\n".join(self._sanitize(c) for c in sales_input.constraints or []),
        )

        system_part = self.prompt_template.get("system", "")
        output_part = self.prompt_template.get("output_format", "")

        return "\n".join(part for part in [system_part, user_part, output_part] if part)

    # ------------------------------------------------------------------
    # LLM interaction
    def _load_stub_response(self) -> Dict[str, Any]:
        """Return stub data used when the LLM is unreachable."""

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
                    "summary": "オフラインスタブ",
                },
                "mid_term": {"plan_weeks_4_12": ["オフライン"]},
                "offline": True,
            }

    def generate_advice(self, sales_input: SalesInput) -> Dict[str, Any]:
        """Generate advice by calling the LLM.

        If the LLM call fails due to a connection error a stub response is
        returned.  Other errors are converted into ``ServiceError`` instances
        using ``ErrorHandler`` for consistency with the rest of the codebase.
        """

        prompt = self._build_prompt(sales_input)
        schema = self.prompt_template.get("schema")

        try:
            return self.llm_provider.call_llm(prompt, "speed", json_schema=schema)
        except ConnectionError:
            self.logger.warning("オフラインモード: LLM接続に失敗しました。スタブデータを使用します。")
            return self._load_stub_response()
        except Exception as e:  # pragma: no cover - unexpected
            error = self.error_handler.handle_error(e, context="PreAdvisorService.generate_advice")
            raise ServiceError(error["error"]["message"], "execution_failed")


# Backwards compatibility: some modules/tests import ``OpenAIProvider`` from
# ``services.pre_advisor`` expecting the original location.
OpenAIProvider = OpenAIProvider

