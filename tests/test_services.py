import json
import pytest
from unittest.mock import Mock, patch
from core.models import SalesInput, SalesType
from services.pre_advisor import PreAdvisorService
from services.post_analyzer import PostAnalyzerService
from services.search_enhancer import SearchEnhancerService
from services.error_handler import ServiceError

def test_pre_advisor_service():
    """事前アドバイスサービスのテスト"""
    with patch('services.settings_manager.SettingsManager') as mock_settings_manager, \
         patch('services.pre_advisor.OpenAIProvider') as mock_provider:
        mock_settings = Mock()
        mock_settings.load_settings.return_value.temperature = 0.7
        mock_settings.load_settings.return_value.max_tokens = 1000
        mock_settings_manager.return_value = mock_settings
        
        mock_llm = Mock()
        mock_llm.call_llm.return_value = {
            "short_term": {
                "openers": {"call": "テスト", "visit": "テスト", "email": "テスト"},
                "discovery": ["質問1"],
                "differentiation": [{"vs": "競合", "talk": "差別化"}],
                "objections": [{"type": "価格", "script": "対応"}],
                "next_actions": ["アクション1"],
                "kpi": {"next_meeting_rate": "50%", "poc_rate": "20%"},
                "summary": "テストサマリー"
            },
            "mid_term": {"plan_weeks_4_12": ["計画1"]}
        }
        mock_provider.return_value = mock_llm
        
        service = PreAdvisorService()
        input_data = SalesInput(
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS",
            description="テスト商品",
            stage="初期",
            purpose="売上向上"
        )
        
        result = service.generate_advice(input_data)
        assert "short_term" in result
        assert "mid_term" in result

def test_post_analyzer_service():
    """商談後ふりかえり解析サービスのテスト"""
    with patch('services.settings_manager.SettingsManager') as mock_settings_manager, \
         patch('services.post_analyzer.OpenAIProvider') as mock_provider:
        mock_settings = Mock()
        mock_settings.load_settings.return_value.temperature = 0.7
        mock_settings.load_settings.return_value.max_tokens = 1000
        mock_settings_manager.return_value = mock_settings
        
        mock_llm = Mock()
        mock_llm.call_llm.return_value = {
            "summary": "テスト要約",
            "bant": {"budget": "100万", "authority": "あり", "need": "あり", "timeline": "3ヶ月"},
            "champ": {"challenges": "課題", "authority": "権限者", "money": "予算", "prioritization": "高"},
            "objections": [{"theme": "価格", "details": "詳細", "counter": "対応"}],
            "risks": [{"type": "停滞", "prob": "medium", "reason": "理由", "mitigation": "対策"}],
            "next_actions": ["アクション1"],
            "followup_email": {"subject": "件名", "body": "本文"},
            "metrics_update": {"stage": "次のステージ", "win_prob_delta": "+10%"}
        }
        mock_provider.return_value = mock_llm
        
        service = PostAnalyzerService()
        
        result = service.analyze_meeting(
            meeting_content="テスト議事録",
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS"
        )
        assert "summary" in result
        assert "bant" in result
        assert "next_actions" in result


def test_search_enhancer_calls_llm():
    """検索高度化サービスがLLMを呼び出すことを確認"""
    with patch('services.search_enhancer.OpenAIProvider') as mock_provider:
        mock_llm = Mock()
        mock_llm.call_llm.return_value = {"optimized_queries": [], "search_strategy": ""}
        mock_provider.return_value = mock_llm

        service = SearchEnhancerService()
        result = service.enhance_search_query("テスト", industry="IT")

        assert "optimized_queries" in result
        mock_llm.call_llm.assert_called_once()
        args, kwargs = mock_llm.call_llm.call_args
        assert args[1] == "speed"
        assert "json_schema" in kwargs


def test_search_enhancer_without_api_key():
    """APIキーがなくてもフォールバックが動作することを確認"""
    with patch('services.search_enhancer.OpenAIProvider', side_effect=ValueError("OPENAI_API_KEYが設定されていません")):
        service = SearchEnhancerService()
        result = service.enhance_search_query("テスト", industry="IT")
        assert "optimized_queries" in result


def test_pre_advisor_service_invalid_schema():
    """スキーマ不正時にServiceErrorが発生することを確認"""
    with patch('services.settings_manager.SettingsManager') as mock_settings_manager, \
         patch('services.pre_advisor.OpenAIProvider') as mock_provider:
        mock_settings = Mock()
        mock_settings.load_settings.return_value.temperature = 0.7
        mock_settings.load_settings.return_value.max_tokens = 1000
        mock_settings_manager.return_value = mock_settings

        mock_llm = Mock()
        mock_llm.call_llm.side_effect = ValueError("LLMの応答が期待されるスキーマに従っていません")
        mock_provider.return_value = mock_llm

        service = PreAdvisorService()
        input_data = SalesInput(
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS",
            description="テスト商品",
            stage="初期",
            purpose="売上向上",
        )

        with pytest.raises(ServiceError):
            service.generate_advice(input_data)
