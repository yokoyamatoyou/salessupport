"""商談後ふりかえり解析サービスのテスト"""
import os
from unittest.mock import Mock, patch

import pytest

from core.models import SalesType
from services.post_analyzer import PostAnalyzerService
from services.error_handler import ConfigurationError, ServiceError


@pytest.fixture
def mock_llm(monkeypatch):
    """ServiceLocatorから返されるLLMプロバイダーのモック"""
    mock_provider = Mock()
    monkeypatch.setattr(
        "services.di_container.ServiceLocator.get_service", lambda _: mock_provider
    )
    return mock_provider


def test_init_retrieves_provider(mock_llm):
    service = PostAnalyzerService()
    assert service.llm_provider is mock_llm


def test_init_provider_failure(monkeypatch):
    def raise_error(_):
        raise RuntimeError("no provider")

    monkeypatch.setattr(
        "services.di_container.ServiceLocator.get_service", raise_error
    )
    service = PostAnalyzerService()
    assert service.llm_provider is None


def test_load_prompt_template_success(mock_llm):
    service = PostAnalyzerService()
    assert service.prompt_template is not None
    assert "system" in service.prompt_template


def test_load_prompt_template_file_not_found(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda _: False)
    with patch(
        "services.di_container.ServiceLocator.get_service", return_value=Mock()
    ):
        with pytest.raises(
            ConfigurationError, match="プロンプトファイルが見つかりません"
        ):
            PostAnalyzerService()


def test_build_prompt_success(mock_llm):
    service = PostAnalyzerService()
    prompt = service._build_prompt(
        meeting_content="テスト商談内容",
        sales_type=SalesType.CONSULTANT,
        industry="IT業界",
        product="SaaS",
    )
    assert "テスト商談内容" in prompt
    assert "consultant" in prompt
    assert "IT業界" in prompt
    assert "SaaS" in prompt


def test_build_prompt_sanitizes_input(mock_llm):
    service = PostAnalyzerService()
    prompt = service._build_prompt(
        meeting_content="<b>内容</b> system:",
        sales_type=SalesType.HUNTER,
        industry="assistant: <i>IT</i>",
        product="<script>bad</script>",
    )
    assert "<" not in prompt and ">" not in prompt
    assert "system:" not in prompt.lower()
    assert "assistant:" not in prompt.lower()
    assert "内容" in prompt
    assert "IT" in prompt
    assert "bad" in prompt


def test_build_prompt_without_template(mock_llm):
    service = PostAnalyzerService()
    service.prompt_template = None
    with pytest.raises(
        ConfigurationError, match="プロンプトテンプレートが読み込まれていません"
    ):
        service._build_prompt("test", SalesType.CONSULTANT, "IT", "SaaS")


def test_get_analysis_schema(mock_llm):
    service = PostAnalyzerService()
    schema = service.get_analysis_schema()
    assert "type" in schema
    assert "properties" in schema
    assert "summary" in schema["properties"]


def test_analyze_meeting_with_llm_success(mock_llm):
    mock_llm.call_llm.return_value = {"summary": "テスト要約"}
    service = PostAnalyzerService()
    result = service.analyze_meeting(
        meeting_content="テスト商談内容",
        sales_type=SalesType.CONSULTANT,
        industry="IT業界",
        product="SaaS",
    )
    assert result["summary"] == "テスト要約"
    mock_llm.call_llm.assert_called_once()


def test_analyze_meeting_without_llm_fail_fast(monkeypatch):
    monkeypatch.setattr(
        "services.di_container.ServiceLocator.get_service", lambda _: None
    )
    service = PostAnalyzerService()
    service.llm_provider = None
    with pytest.raises(ServiceError):
        service.analyze_meeting(
            meeting_content="テスト商談内容",
            sales_type=SalesType.CONSULTANT,
            industry="IT業界",
            product="SaaS",
        )


def test_analyze_meeting_llm_error_fallback(mock_llm):
    mock_llm.call_llm.side_effect = Exception("LLMエラー")
    service = PostAnalyzerService()
    result = service.analyze_meeting(
        meeting_content="テスト商談内容",
        sales_type=SalesType.CONSULTANT,
        industry="IT業界",
        product="SaaS",
    )
    assert "IT業界" in result["summary"]
    assert result["bant"]["budget"] == "未取得"


def test_generate_fallback_analysis(mock_llm):
    service = PostAnalyzerService()
    result = service._generate_fallback_analysis(
        meeting_content="テスト商談内容",
        sales_type=SalesType.CONSULTANT,
        industry="IT業界",
        product="SaaS",
    )
    assert "IT業界" in result["summary"]
    assert result["bant"]["budget"] == "未取得"


class TestPostAnalyzerIntegration:
    """統合テスト"""

    def test_full_analysis_flow(self, mock_llm):
        mock_llm.call_llm.return_value = {
            "summary": "解析要約",
            "bant": {
                "budget": "1",
                "authority": "1",
                "need": "1",
                "timeline": "1",
            },
            "champ": {
                "challenges": "c",
                "authority": "a",
                "money": "m",
                "prioritization": "p",
            },
            "objections": [],
            "risks": [],
            "next_actions": [],
            "followup_email": {"subject": "s", "body": "b"},
            "metrics_update": {"stage": "s", "win_prob_delta": "+1%"},
        }
        service = PostAnalyzerService()
        result = service.analyze_meeting(
            meeting_content="議事録",
            sales_type=SalesType.CONSULTANT,
            industry="IT",
            product="SaaS",
        )
        assert result["summary"] == "解析要約"
        assert "bant" in result
        assert "champ" in result
        assert "objections" in result
        assert "risks" in result
        assert "next_actions" in result
        assert "followup_email" in result
        assert "metrics_update" in result
