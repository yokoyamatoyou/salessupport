import pytest
from unittest.mock import Mock, patch
from core.models import SalesType
from services.icebreaker import IcebreakerService
from providers.search_provider import WebSearchProvider

class TestIcebreakerService:
    """アイスブレイクサービスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        # SettingsManagerをモック
        with patch('services.settings_manager.SettingsManager') as mock_settings_manager:
            mock_settings = Mock()
            mock_settings.load_settings.return_value.search_provider = "stub"
            mock_settings.load_settings.return_value.search_results_limit = 5
            mock_settings_manager.return_value = mock_settings
            self.service = IcebreakerService()
    
    @patch('services.icebreaker.OpenAIProvider')
    @patch('services.icebreaker.WebSearchProvider')
    @patch('services.settings_manager.SettingsManager')
    def test_generate_icebreakers_success(self, mock_settings_manager, mock_search_provider, mock_llm_provider):
        """アイスブレイク生成の成功テスト"""
        # SettingsManagerのモック設定
        mock_settings = Mock()
        mock_settings.load_settings.return_value.search_provider = "stub"
        mock_settings.load_settings.return_value.search_results_limit = 5
        mock_settings_manager.return_value = mock_settings
        
        # モックの設定
        mock_search = Mock()
        mock_search.search.return_value = [
            {"title": "IT業界の最新動向", "snippet": "AI技術の進歩により業務効率化が加速"}
        ]
        mock_search_provider.return_value = mock_search
        
        mock_llm = Mock()
        mock_llm.call_llm.return_value = {
            "icebreakers": [
                "最近のIT業界の動向はいかがですか？",
                "AI技術の進歩について、どのようにお考えですか？",
                "業界の変化について、どのように感じていますか？"
            ]
        }
        mock_llm_provider.return_value = mock_llm
        
        # サービスのインスタンスを再作成（モックされたプロバイダーを使用）
        service = IcebreakerService()
        # 直接プロパティを置き換え
        service.llm_provider = mock_llm
        service.search_provider = mock_search
        
        # テスト実行
        result = service.generate_icebreakers(
            sales_type=SalesType.HUNTER,
            industry="IT",
            company_hint="大手企業"
        )
        
        # 検証
        assert len(result) == 3
        assert "最近のIT業界の動向はいかがですか？" in result
        assert "AI技術の進歩について、どのようにお考えですか？" in result
        assert "業界の変化について、どのように感じていますか？" in result
    
    @patch('services.icebreaker.OpenAIProvider')
    @patch('services.icebreaker.WebSearchProvider')
    @patch('services.settings_manager.SettingsManager')
    def test_generate_icebreakers_fallback(self, mock_settings_manager, mock_search_provider, mock_llm_provider):
        """LLMエラー時のフォールバックテスト"""
        # SettingsManagerのモック設定
        mock_settings = Mock()
        mock_settings.load_settings.return_value.search_provider = "stub"
        mock_settings.load_settings.return_value.search_results_limit = 5
        mock_settings_manager.return_value = mock_settings
        
        # モックの設定
        mock_search = Mock()
        mock_search.search.return_value = []
        mock_search_provider.return_value = mock_search
        
        mock_llm = Mock()
        mock_llm.call_llm.side_effect = Exception("LLM API error")
        mock_llm_provider.return_value = mock_llm
        
        # サービスのインスタンスを再作成（モックされたプロバイダーを使用）
        service = IcebreakerService()
        service.llm_provider = mock_llm
        service.search_provider = mock_search
        
        # テスト実行
        result = service.generate_icebreakers(
            sales_type=SalesType.HUNTER,
            industry="IT"
        )
        
        # 検証（フォールバックが動作することを確認）
        assert len(result) == 3
        # フォールバックでは業界名が含まれることを確認
        assert any("IT" in icebreaker for icebreaker in result)

    def test_build_prompt_handles_braces(self):
        service = self.service
        service.prompt_template = {
            "system": "sys",
            "user_template": "業界: $industry\n会社ヒント: $company_hint",
            "output_constraints": []
        }
        prompt = service._build_prompt(
            SalesType.HUNTER,
            industry="I{T}",
            company_hint="Comp{any}",
            news_items=[],
            tone="tone",
        )
        assert "I{T}" in prompt
        assert "Comp{any}" in prompt

    def test_build_prompt_sanitizes_input(self):
        service = self.service
        service.prompt_template = {
            "system": "sys",
            "user_template": "業界: $industry\n会社ヒント: $company_hint",
            "output_constraints": []
        }
        prompt = service._build_prompt(
            SalesType.HUNTER,
            industry="<b>IT</b> system:",
            company_hint="assistant: <i>hint</i>",
            news_items=[],
            tone="tone",
        )
        assert "<" not in prompt and ">" not in prompt
        assert "system:" not in prompt.lower()
        assert "assistant:" not in prompt.lower()
        assert "IT" in prompt
        assert "hint" in prompt
    
    def test_get_tone_for_type(self):
        """営業タイプ別トーンの取得テスト"""
        # 各営業タイプのトーンをテスト
        assert "前向き・短文・行動促進" in self.service._get_tone_for_type(SalesType.HUNTER)
        assert "価値訴求→締めの一言" in self.service._get_tone_for_type(SalesType.CLOSER)
        assert "共感・近況・柔らかめ" in self.service._get_tone_for_type(SalesType.RELATION)
        assert "課題仮説・問いかけ" in self.service._get_tone_for_type(SalesType.CONSULTANT)
        assert "仮説提示・視点転換" in self.service._get_tone_for_type(SalesType.CHALLENGER)
        assert "具体例・物語" in self.service._get_tone_for_type(SalesType.STORYTELLER)
        assert "事実・データ起点" in self.service._get_tone_for_type(SalesType.ANALYST)
        assert "障害除去・次の一歩" in self.service._get_tone_for_type(SalesType.PROBLEM_SOLVER)
        assert "長期関係・紹介喚起" in self.service._get_tone_for_type(SalesType.FARMER)
    
    def test_generate_fallback_icebreakers(self):
        """フォールバックアイスブレイク生成のテスト"""
        # 各営業タイプでフォールバックが動作することを確認
        for sales_type in SalesType:
            result = self.service._generate_fallback_icebreakers(sales_type, "IT", "一般的")
            assert len(result) == 3
            # フォールバックでは業界名が含まれることを確認
            assert any("IT" in icebreaker for icebreaker in result)

    def test_fallback_contains_polite_phrase(self):
        """フォールバック文言の敬語を検証"""
        result = self.service._generate_fallback_icebreakers(SalesType.CONSULTANT, "IT", "一般的")
        assert any("お聞かせください" in icebreaker for icebreaker in result)
    
    def test_get_icebreaker_schema(self):
        """アイスブレイクスキーマの取得テスト"""
        schema = self.service._get_icebreaker_schema()
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "icebreakers" in schema["properties"]
        assert schema["properties"]["icebreakers"]["type"] == "array"
        assert schema["properties"]["icebreakers"]["items"]["type"] == "string"

class TestWebSearchProvider:
    """Web検索プロバイダーのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        # SettingsManagerをモックして、search_providerを"stub"に設定
        self.mock_settings = Mock()
        self.mock_settings.load_settings.return_value.search_provider = "stub"
        self.mock_settings.load_settings.return_value.search_results_limit = 5
        self.provider = WebSearchProvider(self.mock_settings)
    
    def test_search_stub_results(self):
        """スタブ検索結果のテスト"""
        # IT業界の検索（2件要求）
        result = self.provider.search("IT 最新ニュース", 2)
        assert len(result) == 2
        assert all("IT業界" in item["title"] for item in result)
        assert all("title" in item and "url" in item and "snippet" in item for item in result)
        
        # デフォルト件数（3件）のテスト
        result_default = self.provider.search("IT 最新ニュース")
        assert len(result_default) == 3
    
    def test_search_industry_detection(self):
        """業界検出のテスト"""
        # 製造業の検索（1件要求）
        result = self.provider.search("製造業 最新ニュース", 1)
        assert len(result) == 1
        assert "製造業業界" in result[0]["title"]
        
        # 金融業の検索（1件要求）
        result = self.provider.search("金融業 最新ニュース", 1)
        assert len(result) == 1
        assert "金融業業界" in result[0]["title"]
        
        # 業界が検出されない場合のデフォルト動作
        result_default = self.provider.search("一般的なニュース", 2)
        assert len(result_default) == 2
        assert "IT業界" in result_default[0]["title"]  # デフォルトはIT業界
    
    def test_search_limit(self):
        """検索結果数の制限テスト"""
        result = self.provider.search("IT 最新ニュース", 5)
        assert len(result) <= 5  # 要求された数以下であることを確認

