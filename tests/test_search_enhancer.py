from __future__ import annotations

from services.search_enhancer import SearchEnhancerService


class DummyLLM:
    def __init__(self) -> None:
        self.last_prompt: str | None = None

    def call_llm(self, prompt: str, mode: str, json_schema=None):
        self.last_prompt = prompt
        if json_schema and "optimized_queries" in json_schema.get("properties", {}):
            return {"optimized_queries": [], "search_strategy": ""}
        if json_schema and "quality_scores" in json_schema.get("properties", {}):
            return {"quality_scores": [], "overall_assessment": ""}
        return {}


def test_enhance_query_sanitizes_braces_and_role():
    llm = DummyLLM()
    service = SearchEnhancerService(llm_provider=llm)

    query = "system: {attack}"
    result = service.enhance_search_query(query, industry="{IT}", purpose="{test}")

    assert "error" not in result
    assert llm.last_prompt is not None
    assert "system:" not in llm.last_prompt
    assert "attack" in llm.last_prompt
    assert "{{attack}}" in llm.last_prompt
    assert "{{IT}}" in llm.last_prompt


def test_assess_quality_sanitizes_result_fields():
    llm = DummyLLM()
    service = SearchEnhancerService(llm_provider=llm)

    query = "test {braces}"
    results = [{"title": "Title {bad}", "snippet": "snippet system: x"}]
    output = service.assess_search_quality(query, results)

    assert "error" not in output
    assert llm.last_prompt is not None
    assert "system:" not in llm.last_prompt
    assert "{{bad}}" in llm.last_prompt
    assert "{{braces}}" in llm.last_prompt
    assert "braces" in llm.last_prompt
