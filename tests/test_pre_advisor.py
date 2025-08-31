import pytest
import os
from unittest.mock import Mock, patch, mock_open
from core.models import SalesType, SalesInput
from services.pre_advisor import PreAdvisorService
from services.error_handler import ConfigurationError, ServiceError

class TestPreAdvisorService:
    
    def test_init_loads_prompt_template(self):
        """プロンプトテンプレートの読み込みテスト"""
        mock_yaml_content = """
system: "システムメッセージ"
user: "ユーザーテンプレート"
output_format: "出力形式"
"""
        
        with patch("services.pre_advisor.Logger") as mock_logger_class:
            with patch("services.pre_advisor.ErrorHandler") as mock_error_handler_class:
                with patch("services.pre_advisor.OpenAIProvider") as mock_provider_class:
                    with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
                        with patch("yaml.safe_load") as mock_yaml_load:
                            # モックオブジェクトを作成
                            mock_logger = Mock()
                            mock_error_handler = Mock()
                            mock_provider = Mock()
                            
                            # クラスの戻り値を設定
                            mock_logger_class.return_value = mock_logger
                            mock_error_handler_class.return_value = mock_error_handler
                            mock_provider_class.return_value = mock_provider
                            
                            # YAMLの戻り値を設定
                            mock_yaml_load.return_value = {
                                "system": "システムメッセージ",
                                "user": "ユーザーテンプレート",
                                "output_format": "出力形式"
                            }
                            
                            service = PreAdvisorService()
                            assert service.prompt_template["system"] == "システムメッセージ"
    
    def test_init_file_not_found(self):
        """プロンプトファイルが見つからない場合のテスト"""
        with patch("services.pre_advisor.Logger") as mock_logger_class:
            with patch("services.pre_advisor.ErrorHandler") as mock_error_handler_class:
                with patch("services.pre_advisor.OpenAIProvider") as mock_provider_class:
                    # モックオブジェクトを作成
                    mock_logger = Mock()
                    mock_error_handler = Mock()
                    mock_provider = Mock()
                    
                    # クラスの戻り値を設定
                    mock_logger_class.return_value = mock_logger
                    mock_error_handler_class.return_value = mock_error_handler
                    mock_provider_class.return_value = mock_provider
                    
                    # ファイルが見つからないエラーを発生させる
                    with patch("builtins.open", side_effect=FileNotFoundError):
                        with pytest.raises(ConfigurationError, match="プロンプトファイル 'prompts/pre_advice.yaml' が見つかりません"):
                            PreAdvisorService()
    
    def test_build_prompt(self):
        """プロンプト構築のテスト"""
        with patch("services.pre_advisor.Logger") as mock_logger_class:
            with patch("services.pre_advisor.ErrorHandler") as mock_error_handler_class:
                with patch("services.pre_advisor.OpenAIProvider") as mock_provider_class:
                    with patch("builtins.open", mock_open(read_data="test")):
                        with patch("yaml.safe_load") as mock_yaml_load:
                            # モックオブジェクトを作成
                            mock_logger = Mock()
                            mock_error_handler = Mock()
                            mock_provider = Mock()
                            
                            # クラスの戻り値を設定
                            mock_logger_class.return_value = mock_logger
                            mock_error_handler_class.return_value = mock_error_handler
                            mock_provider_class.return_value = mock_provider
                            
                            # YAMLの戻り値を設定
                            mock_yaml_load.return_value = {
                                "user": "営業タイプ: $sales_type\n業界: $industry\n説明: $description",
                                "system": "システムメッセージ",
                                "output_format": "出力形式"
                            }

                            service = PreAdvisorService()
                            service.prompt_template = {
                                "user": "営業タイプ: $sales_type\n業界: $industry\n説明: $description",
                                "system": "システムメッセージ",
                                "output_format": "出力形式"
                            }
                            
                            sales_input = SalesInput(
                                sales_type=SalesType.HUNTER,
                                industry="IT",
                                product="SaaS",
                                description="テスト商品{詳細}",
                                description_url=None,
                                competitor="競合A",
                                competitor_url=None,
                                stage="初期接触",
                                purpose="新規顧客獲得",
                                constraints=["予算制限"]
                            )
                            
                            prompt = service._build_prompt(sales_input)
                            assert "営業タイプ: hunter" in prompt
                            assert "業界: IT" in prompt
                            assert "説明: テスト商品{詳細}" in prompt
                            assert "システムメッセージ" in prompt
                            assert "出力形式" in prompt

    def test_build_prompt_sanitizes_input(self):
        with patch("services.pre_advisor.Logger") as mock_logger_class:
            with patch("services.pre_advisor.ErrorHandler") as mock_error_handler_class:
                with patch("services.pre_advisor.OpenAIProvider") as mock_provider_class:
                    with patch("builtins.open", mock_open(read_data="test")):
                        with patch("yaml.safe_load") as mock_yaml_load:
                            mock_logger = Mock()
                            mock_error_handler = Mock()
                            mock_provider = Mock()

                            mock_logger_class.return_value = mock_logger
                            mock_error_handler_class.return_value = mock_error_handler
                            mock_provider_class.return_value = mock_provider

                            mock_yaml_load.return_value = {
                                "user": "業界: $industry\n説明: $description",
                                "system": "sys",
                                "output_format": "out",
                            }

                            service = PreAdvisorService()
                            service.prompt_template = {
                                "user": "業界: $industry\n説明: $description",
                                "system": "sys",
                                "output_format": "out",
                            }

                            sales_input = SalesInput(
                                sales_type=SalesType.HUNTER,
                                industry="<b>IT</b> system:",
                                product="SaaS",
                                description="assistant: <i>bad</i>",
                                description_url=None,
                                competitor="",
                                competitor_url=None,
                                stage="",
                                purpose="",
                                constraints=[]
                            )

                            prompt = service._build_prompt(sales_input)
                            assert "<" not in prompt and ">" not in prompt
                            assert "system:" not in prompt.lower()
                            assert "assistant:" not in prompt.lower()
                            assert "IT" in prompt
                            assert "bad" in prompt
    
    def test_generate_advice_success(self):
        """アドバイス生成成功のテスト"""
        mock_advice = {
            "short_term": {
                "openers": {"call": "テスト", "visit": "テスト", "email": "テスト"},
                "discovery": ["質問1"],
                "differentiation": [{"vs": "競合", "talk": "差別化"}],
                "objections": [{"type": "価格", "script": "対応"}],
                "next_actions": ["アクション1"],
                "kpi": {"next_meeting_rate": "50%", "poc_rate": "20%"},
                "summary": "サマリー"
            },
            "mid_term": {
                "plan_weeks_4_12": ["計画1", "計画2", "計画3"]
            }
        }
        
        with patch("services.pre_advisor.Logger") as mock_logger_class:
            with patch("services.pre_advisor.ErrorHandler") as mock_error_handler_class:
                with patch("services.pre_advisor.OpenAIProvider") as mock_provider_class:
                    with patch("builtins.open", mock_open(read_data="test")):
                        with patch("yaml.safe_load") as mock_yaml_load:
                            # モックオブジェクトを作成
                            mock_logger = Mock()
                            mock_error_handler = Mock()
                            mock_provider = Mock()
                            
                            # クラスの戻り値を設定
                            mock_logger_class.return_value = mock_logger
                            mock_error_handler_class.return_value = mock_error_handler
                            mock_provider_class.return_value = mock_provider
                            
                            # YAMLの戻り値を設定
                            mock_yaml_load.return_value = {"user": "test", "system": "test", "output_format": "test"}
                            
                            # call_llmメソッドの戻り値を設定
                            mock_provider.call_llm.return_value = mock_advice
                            
                            service = PreAdvisorService()
                            sales_input = SalesInput(
                                sales_type=SalesType.HUNTER,
                                industry="IT",
                                product="SaaS",
                                description="テスト商品",
                                description_url=None,
                                competitor="競合A",
                                competitor_url=None,
                                stage="初期接触",
                                purpose="新規顧客獲得",
                                constraints=[]
                            )
                            
                            result = service.generate_advice(sales_input)
                            assert result == mock_advice
    
    def test_generate_advice_failure(self):
        """アドバイス生成失敗のテスト"""
        with patch("services.pre_advisor.Logger") as mock_logger_class:
            with patch("services.pre_advisor.ErrorHandler") as mock_error_handler_class:
                with patch("services.pre_advisor.OpenAIProvider") as mock_provider_class:
                    with patch("builtins.open", mock_open(read_data="test")):
                        with patch("yaml.safe_load") as mock_yaml_load:
                            # モックオブジェクトを作成
                            mock_logger = Mock()
                            mock_error_handler = Mock()
                            mock_provider = Mock()
                            
                            # クラスの戻り値を設定
                            mock_logger_class.return_value = mock_logger
                            mock_error_handler_class.return_value = mock_error_handler
                            mock_provider_class.return_value = mock_provider
                            
                            # YAMLの戻り値を設定
                            mock_yaml_load.return_value = {"user": "test", "system": "test", "output_format": "test"}
                            
                            # call_llmメソッドでエラーを発生させる
                            mock_provider.call_llm.side_effect = Exception("LLMエラー")
                            
                            # ErrorHandler.handle_errorメソッドの戻り値を設定
                            mock_error_handler.handle_error.return_value = {
                                "error": {
                                    "message": "予期しないエラーが発生しました"
                                }
                            }
                            
                            service = PreAdvisorService()
                            sales_input = SalesInput(
                                sales_type=SalesType.HUNTER,
                                industry="IT",
                                product="SaaS",
                                description="テスト商品",
                                description_url=None,
                                competitor="競合A",
                                competitor_url=None,
                                stage="初期接触",
                                purpose="新規顧客獲得",
                                constraints=[]
                            )
                            
                            with pytest.raises(ServiceError, match="予期しないエラーが発生しました"):
                                service.generate_advice(sales_input)

    def test_offline_fallback(self, tmp_path):
        """LLM接続失敗時にスタブデータを返す"""
        stub_data = {
            "short_term": {
                "openers": {"call": "オフライン", "visit": "オフライン", "email": "オフライン"},
                "discovery": ["オフライン"],
                "differentiation": [{"vs": "オフライン", "talk": "オフライン"}],
                "objections": [{"type": "オフライン", "script": "オフライン"}],
                "next_actions": ["オフライン"],
                "kpi": {"next_meeting_rate": "0%", "poc_rate": "0%"},
                "summary": "オフラインスタブ"
            },
            "mid_term": {"plan_weeks_4_12": ["オフライン"]},
            "offline": True
        }

        with patch("services.pre_advisor.Logger") as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger

            with patch("services.pre_advisor.WebSearchProvider") as mock_search_class:
                mock_search = Mock()
                mock_search.search.return_value = []
                mock_search_class.return_value = mock_search

                with patch("services.pre_advisor.OpenAIProvider") as mock_provider_class:
                    mock_provider = Mock()
                    mock_provider.call_llm.side_effect = ConnectionError("network")
                    mock_provider_class.return_value = mock_provider

                    with patch("services.pre_advisor.PreAdvisorService._load_prompt_template") as mock_tpl:
                        mock_tpl.return_value = {"user": "", "system": "", "output_format": ""}
                        service = PreAdvisorService()
                        with patch.object(service, "_load_stub_response", return_value=stub_data):
                            sales_input = SalesInput(
                                sales_type=SalesType.HUNTER,
                                industry="IT",
                                product="SaaS",
                                description="", description_url=None,
                                competitor="", competitor_url=None,
                                stage="", purpose="", constraints=[]
                            )
                            result = service.generate_advice(sales_input)
                            assert result == stub_data
                            mock_logger.warning.assert_any_call("オフラインモード: LLM接続に失敗しました。スタブデータを使用します。")
