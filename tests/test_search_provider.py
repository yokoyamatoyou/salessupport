import random
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import pytest

from providers.search_provider import WebSearchProvider


def _make_item(url: str, days_old: int = 0):
    published = datetime.now(timezone.utc) - timedelta(days=days_old)
    return {
        "title": "AI news",
        "url": url,
        "snippet": "AI revolution",
        "source": "newsapi",
        "published_at": published.isoformat(),
    }


def test_rank_results_sorted_and_domain_diverse():
    provider = WebSearchProvider()
    items = [
        _make_item("https://www.nikkei.com/a", 0),
        _make_item("https://www.nikkei.com/b", 10),
        _make_item("https://example.com/c", 20),
    ]
    ranked = provider._rank_results(items, "AI", 2)
    assert len(ranked) == 2
    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)
    domains = [urlparse(r["url"]).netloc for r in ranked]
    assert len(set(domains)) == 2


def test_search_stub_provider_returns_stub_data():
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("SEARCH_PROVIDER", "stub")
        random.seed(0)
        provider = WebSearchProvider()
        results = provider.search("IT", num=2)
        assert len(results) == 2
        assert all(r["source"] == "stub" for r in results)


def test_missing_api_keys_fallback_to_stub():
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("SEARCH_PROVIDER", "cse")
        mp.delenv("CSE_API_KEY", raising=False)
        mp.delenv("CSE_CX", raising=False)
        mp.delenv("NEWSAPI_KEY", raising=False)
        random.seed(0)
        provider = WebSearchProvider()
        results = provider.search("IT", num=1)
        assert len(results) == 1
        assert results[0]["source"] == "stub"


def test_scoring_freshness_and_trusted_domain():
    provider = WebSearchProvider()
    fresh_trusted = _make_item("https://www.nikkei.com/fresh", 0)
    old_untrusted = _make_item("https://example.com/old", 90)
    ranked = provider._rank_results([fresh_trusted, old_untrusted], "AI", 2)
    fresh = next(r for r in ranked if "nikkei.com" in r["url"])
    old = next(r for r in ranked if "example.com" in r["url"])
    assert fresh["score"] > old["score"]
    assert fresh["detailed_scoring"]["freshness"] > old["detailed_scoring"]["freshness"]
    assert "high_trusted_domain" in fresh["reasons"]
    assert "trusted_domain" not in old["reasons"]


def test_search_none_provider_returns_message():
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("SEARCH_PROVIDER", "none")
        provider = WebSearchProvider()
        results = provider.search("unknown", num=3)
        assert len(results) == 1
        assert results[0]["snippet"] == "ヒットしませんでした。別のキーワードで再検索してください。"


def test_cse_with_fallback_uses_newsapi(mocker):
    provider = WebSearchProvider()
    mocker.patch.object(provider, "_search_cse", return_value=[])
    mocker.patch.object(
        provider,
        "_search_newsapi",
        return_value=[{"title": "n", "url": "https://e.com", "snippet": "s", "source": "newsapi", "published_at": None}],
    )
    mocker.patch.object(provider, "_rank_results", side_effect=lambda items, q, n: items[:n])
    mocker.patch.object(provider, "_get_stub_results")
    results = provider._search_cse_with_fallback("q", 1)
    assert results[0]["source"] == "newsapi"
    provider._get_stub_results.assert_not_called()


def test_newsapi_with_fallback_uses_stub(mocker):
    provider = WebSearchProvider()
    mocker.patch.object(provider, "_search_newsapi", return_value=[])
    mocker.patch.object(provider, "_search_cse", return_value=[])
    mocker.patch.object(
        provider,
        "_get_stub_results",
        return_value=[{"title": "s", "url": "https://e.com", "snippet": "s", "source": "stub", "published_at": None}],
    )
    mocker.patch.object(provider, "_rank_results", side_effect=lambda items, q, n: items[:n])
    results = provider._search_newsapi_with_fallback("q", 1)
    assert results[0]["source"] == "stub"
