import time
from unittest.mock import Mock

import pytest

from core.models import SalesType
from services.post_analyzer import PostAnalyzerService


@pytest.fixture
def mock_llm(monkeypatch):
    """ServiceLocatorから返されるLLMプロバイダーのモック"""
    mock_provider = Mock()
    monkeypatch.setattr(
        "services.di_container.ServiceLocator.get_service", lambda _: mock_provider
    )
    mock_provider.call_llm.return_value = {"summary": "テスト要約"}
    return mock_provider


def test_analyze_meeting_performance(mock_llm):
    service = PostAnalyzerService()
    start = time.perf_counter()
    service.analyze_meeting(
        meeting_content="テスト商談内容",
        sales_type=SalesType.CONSULTANT,
        industry="IT業界",
        product="SaaS",
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"analyze_meeting took {elapsed:.2f}s"
