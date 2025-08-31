"""
商談後ふりかえり解析サービスのテスト
"""
import os
from unittest.mock import Mock, patch

import pytest

from core.models import SalesType
from services.post_analyzer import PostAnalyzerService
from services.error_handler import ConfigurationError


@pytest.fixture(autouse=True)
def reset_provider(monkeypatch):
    """環境変数と共有LLMプロバイダーをリセット"""
    from services import post_analyzer

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    post_analyzer._global_llm_provider = None
    yield
    post_analyzer._global_llm_provider = None

class TestPostAnalyzerService:
    """PostAnalyzerServiceのテスト"""
    
    def test_init_with_env_api_key(self, monkeypatch):
        """環境変数のAPIキーで初期化"""
        monkeypatch.setenv("OPENAI_API_KEY", "env_key")
        with patch('services.post_analyzer.OpenAIProvider') as mock_provider:
            mock_provider.return_value = Mock()
            service = PostAnalyzerService()
            assert service.llm_provider is mock_provider.return_value
            mock_provider.assert_called_once()

    def test_init_with_settings_manager(self):
        """設定マネージャーのAPIキーで初期化"""
        mock_settings = Mock()
        mock_settings.get_llm_config.return_value = {"api_key": "test_key"}
        with patch('services.post_analyzer.OpenAIProvider') as mock_provider:
            mock_provider.return_value = Mock()
            service = PostAnalyzerService(mock_settings)
            assert service.llm_provider is mock_provider.return_value
            mock_provider.assert_called_once_with(mock_settings)

    def test_init_without_api_key(self, caplog):
        """APIキーなしでの初期化"""
        mock_settings = Mock()
        mock_settings.get_llm_config.return_value = {}
        service = PostAnalyzerService(mock_settings)
        assert service.llm_provider is None
        assert "APIキーが設定されていません" in caplog.text
    
    def test_load_prompt_template_success(self):
        """プロンプトテンプレートの読み込み成功"""
        service = PostAnalyzerService()
        assert service.prompt_template is not None
        assert "system" in service.prompt_template
        assert "user" in service.prompt_template
        assert "output_schema" in service.prompt_template
    
    def test_load_prompt_template_file_not_found(self):
        """プロンプトファイルが見つからない場合"""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ConfigurationError, match="プロンプトファイルが見つかりません"):
                PostAnalyzerService()
    
    def test_build_prompt_success(self):
        """プロンプトの構築成功"""
        service = PostAnalyzerService()
        prompt = service._build_prompt(
            meeting_content="テスト商談内容",
            sales_type=SalesType.CONSULTANT,
            industry="IT業界",
            product="SaaS"
        )
        
        assert "テスト商談内容" in prompt
        assert "consultant" in prompt
        assert "IT業界" in prompt
        assert "SaaS" in prompt

    def test_build_prompt_sanitizes_input(self):
        service = PostAnalyzerService()
        prompt = service._build_prompt(
            meeting_content="<b>内容</b> system:",
            sales_type=SalesType.HUNTER,
            industry="assistant: <i>IT</i>",
            product="<script>bad</script>"
        )

        assert "<" not in prompt and ">" not in prompt
        assert "system:" not in prompt.lower()
        assert "assistant:" not in prompt.lower()
        assert "内容" in prompt
        assert "IT" in prompt
        assert "bad" in prompt
    
    def test_build_prompt_without_template(self):
        """プロンプトテンプレートなしでの構築"""
        service = PostAnalyzerService()
        service.prompt_template = None
        
        with pytest.raises(ConfigurationError, match="プロンプトテンプレートが読み込まれていません"):
            service._build_prompt("test", SalesType.CONSULTANT, "IT", "SaaS")
    
    def test_get_analysis_schema(self):
        """解析スキーマの取得"""
        service = PostAnalyzerService()
        schema = service.get_analysis_schema()
        
        assert "type" in schema
        assert "properties" in schema
        assert "required" in schema
        assert "summary" in schema["properties"]
        assert "bant" in schema["properties"]
        assert "champ" in schema["properties"]
    
    def test_analyze_meeting_with_llm_success(self):
        """LLMによる解析成功"""
        mock_settings = Mock()
        mock_settings.get_llm_config.return_value = {"api_key": "test_key"}
        
        mock_llm = Mock()
        mock_llm.call_llm.return_value = {
            "summary": "テスト要約",
            "bant": {"budget": "テスト予算", "authority": "テスト権限", "need": "テストニーズ", "timeline": "テストタイムライン"},
            "champ": {"challenges": "テスト課題", "authority": "テスト権限", "money": "テスト資金", "prioritization": "テスト優先度"},
            "objections": [{"theme": "テスト", "details": "テスト詳細", "counter": "テスト対応"}],
            "risks": [{"type": "テストリスク", "prob": "high", "reason": "テスト理由", "mitigation": "テスト軽減策"}],
            "next_actions": ["テストアクション"],
            "followup_email": {"subject": "テスト件名", "body": "テスト本文"},
            "metrics_update": {"stage": "テストステージ", "win_prob_delta": "+5%"}
        }
        
        with patch('services.post_analyzer.OpenAIProvider', return_value=mock_llm):
            service = PostAnalyzerService(mock_settings)
            service.llm_provider = mock_llm
            
            result = service.analyze_meeting(
                meeting_content="テスト商談内容",
                sales_type=SalesType.CONSULTANT,
                industry="IT業界",
                product="SaaS"
            )
            
            assert result["summary"] == "テスト要約"
            assert result["bant"]["budget"] == "テスト予算"
            assert len(result["objections"]) == 1
            assert len(result["risks"]) == 1
    
    def test_analyze_meeting_without_llm_fallback(self):
        """LLMなしでのフォールバック解析"""
        service = PostAnalyzerService()
        service.llm_provider = None
        
        result = service.analyze_meeting(
            meeting_content="テスト商談内容",
            sales_type=SalesType.CONSULTANT,
            industry="IT業界",
            product="SaaS"
        )
        
        assert "IT業界" in result["summary"]
        assert "SaaS" in result["summary"]
        assert result["bant"]["budget"] == "未取得"
        assert result["champ"]["challenges"] == "未取得"
    
    def test_analyze_meeting_llm_error_fallback(self):
        """LLMエラー時のフォールバック解析"""
        mock_settings = Mock()
        mock_settings.get_llm_config.return_value = {"api_key": "test_key"}
        
        mock_llm = Mock()
        mock_llm.call_llm.side_effect = Exception("LLMエラー")
        
        with patch('services.post_analyzer.OpenAIProvider', return_value=mock_llm):
            service = PostAnalyzerService(mock_settings)
            service.llm_provider = mock_llm
            
            result = service.analyze_meeting(
                meeting_content="テスト商談内容",
                sales_type=SalesType.CONSULTANT,
                industry="IT業界",
                product="SaaS"
            )
            
            # フォールバック結果が返される
            assert "IT業界" in result["summary"]
            assert result["bant"]["budget"] == "未取得"
    
    def test_generate_fallback_analysis(self):
        """フォールバック解析の生成"""
        service = PostAnalyzerService()
        result = service._generate_fallback_analysis(
            meeting_content="テスト商談内容",
            sales_type=SalesType.CONSULTANT,
            industry="IT業界",
            product="SaaS"
        )
        
        assert "IT業界" in result["summary"]
        assert "SaaS" in result["summary"]
        assert result["bant"]["budget"] == "未取得"
        assert result["champ"]["challenges"] == "未取得"
        assert len(result["objections"]) == 1
        assert len(result["risks"]) == 1
        assert len(result["next_actions"]) == 1
        assert "subject" in result["followup_email"]
        assert "body" in result["followup_email"]
        assert "stage" in result["metrics_update"]
        assert "win_prob_delta" in result["metrics_update"]

class TestPostAnalyzerIntegration:
    """統合テスト"""
    
    def test_full_analysis_flow(self):
        """完全な解析フローのテスト"""
        service = PostAnalyzerService()
        
        # 実際のプロンプトファイルを使用
        assert os.path.exists("prompts/post_review.yaml")
        
        # 解析実行
        result = service.analyze_meeting(
            meeting_content="顧客との初回商談を行いました。SaaS導入の検討をしているとのことです。予算は100万円程度、年内の導入を希望しています。",
            sales_type=SalesType.CONSULTANT,
            industry="IT業界",
            product="SaaS"
        )
        
        # 基本的な構造の確認
        assert "summary" in result
        assert "bant" in result
        assert "champ" in result
        assert "objections" in result
        assert "risks" in result
        assert "next_actions" in result
        assert "followup_email" in result
        assert "metrics_update" in result
        
        # 各セクションの詳細確認
        assert isinstance(result["bant"], dict)
        assert isinstance(result["champ"], dict)
        assert isinstance(result["objections"], list)
        assert isinstance(result["risks"], list)
        assert isinstance(result["next_actions"], list)
        assert isinstance(result["followup_email"], dict)
        assert isinstance(result["metrics_update"], dict)
