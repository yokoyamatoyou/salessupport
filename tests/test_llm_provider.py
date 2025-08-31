import pytest
from unittest.mock import Mock, patch, MagicMock
from openai import RateLimitError, BadRequestError, AuthenticationError, APIError
from providers.llm_openai import OpenAIProvider, LLMError
from services.usage_meter import UsageMeter

class TestOpenAIProvider:
    """OpenAIプロバイダーのテスト"""
    
    def test_init_without_api_key(self):
        """APIキーなしでの初期化テスト"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEYが設定されていません"):
                OpenAIProvider()
    
    def test_init_with_api_key(self):
        """APIキーありでの初期化テスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                provider = OpenAIProvider()
                assert provider.client is not None
                mock_openai.assert_called_once_with(api_key='test-key')
    
    def test_call_llm_speed_mode(self):
        """speedモードでのLLM呼び出しテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                # モックレスポンスの設定
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "プレーンテキストレスポンス"
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response
                
                provider = OpenAIProvider()
                result = provider.call_llm("テストプロンプト", "speed")
                
                # 呼び出しパラメータの検証
                mock_client.chat.completions.create.assert_called_once()
                call_args = mock_client.chat.completions.create.call_args[1]
                assert call_args["temperature"] == 0.3
                assert call_args["max_tokens"] == 1200
                assert "top_p" in call_args
                assert call_args["model"] == "gpt-4o-mini"
                
                # 結果の検証（JSONスキーマなしの場合はcontentキーで返される）
                assert result == {"content": "プレーンテキストレスポンス"}
    
    def test_call_llm_deep_mode(self):
        """deepモードでのLLM呼び出しテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "プレーンテキストレスポンス"
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response
                
                provider = OpenAIProvider()
                result = provider.call_llm("分析プロンプト", "deep")
                
                call_args = mock_client.chat.completions.create.call_args[1]
                assert call_args["temperature"] == 0.2
                assert call_args["max_tokens"] == 2000
                assert "top_p" not in call_args

                assert result == {"content": "プレーンテキストレスポンス"}

    def test_call_llm_uses_env_model(self):
        """環境変数のモデル名が使用されることを確認"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'gpt-env'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client

                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "レスポンス"
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response

                provider = OpenAIProvider()
                provider.call_llm("prompt", "speed")

                call_args = mock_client.chat.completions.create.call_args[1]
                assert call_args["model"] == "gpt-env"

    def test_call_llm_uses_settings_model(self):
        """設定のモデル名が使用されることを確認"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}, clear=True):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client

                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "レスポンス"
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response

                fake_settings = type('S', (), {"openai_model": "gpt-settings", "temperature": 0.3, "max_tokens": 1000})()
                settings_manager = Mock()
                settings_manager.load_settings.return_value = fake_settings

                provider = OpenAIProvider(settings_manager=settings_manager)
                provider.call_llm("prompt", "speed")

                call_args = mock_client.chat.completions.create.call_args[1]
                assert call_args["model"] == "gpt-settings"
    
    def test_call_llm_with_json_schema(self):
        """JSONスキーマ指定でのLLM呼び出しテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = '{"structured": "data"}'
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response
                
                provider = OpenAIProvider()
                schema = {"type": "object", "required": ["structured"]}
                result = provider.call_llm("構造化プロンプト", "creative", schema)

                call_args = mock_client.chat.completions.create.call_args[1]
                assert call_args["response_format"] == {
                    "type": "json_schema",
                    "json_schema": schema,
                    "strict": True,
                }
                
                # JSONスキーマ指定時は直接パースされたレスポンスが返される
                assert result == {"structured": "data"}
    
    def test_call_llm_without_json_schema(self):
        """JSONスキーマなしでのLLM呼び出しテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "プレーンテキストレスポンス"
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response
                
                provider = OpenAIProvider()
                result = provider.call_llm("テキストプロンプト", "speed")
                
                call_args = mock_client.chat.completions.create.call_args[1]
                assert "response_format" not in call_args
                
                assert result == {"content": "プレーンテキストレスポンス"}
    
    def test_call_llm_invalid_json_response(self):
        """無効なJSONレスポンスのテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "無効なJSON"
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response
                
                provider = OpenAIProvider()
                schema = {"type": "object"}
                
                with pytest.raises(ValueError, match="LLMの応答をJSONとしてパースできませんでした"):
                    provider.call_llm("プロンプト", "speed", schema)
    
    def test_call_llm_schema_validation_failure(self):
        """スキーマ検証失敗のテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = '{"field1": "value1"}'  # requiredフィールドが不足
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response
                
                provider = OpenAIProvider()
                schema = {"type": "object", "required": ["field1", "field2"]}

                with pytest.raises(ValueError, match="LLMの応答が期待されるスキーマに従っていません"):
                    provider.call_llm("プロンプト", "speed", schema)

                call_args = mock_client.chat.completions.create.call_args[1]
                assert call_args["response_format"] == {
                    "type": "json_schema",
                    "json_schema": schema,
                    "strict": True,
                }

    def test_call_llm_refusal_raises_error(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client

                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "拒否"
                mock_message.refusal = "refused"
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response

                provider = OpenAIProvider()
                with pytest.raises(LLMError, match="モデルがリクエストを完了できませんでした"):
                    provider.call_llm("プロンプト", "speed")

    def test_call_llm_non_stop_finish_reason(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client

                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "途中"
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "length"
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response

                provider = OpenAIProvider()
                with pytest.raises(LLMError, match="モデルがリクエストを完了できませんでした"):
                    provider.call_llm("プロンプト", "speed")

    def test_validate_schema(self):
        """スキーマ検証のテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider()
            schema = {
                "type": "object",
                "properties": {
                    "field1": {"type": "string"},
                    "field2": {"type": "integer"}
                },
                "required": ["field1", "field2"]
            }
            response = {"field1": "value1", "field2": 123}
            assert provider.validate_schema(response, schema) is True

            # 型が不正
            response = {"field1": "value1", "field2": "not an int"}
            assert provider.validate_schema(response, schema) is False

            # 必須フィールド不足
            response = {"field1": "value1"}
            assert provider.validate_schema(response, schema) is False

            # 辞書以外のレスポンス
            response = "not a dict"
            assert provider.validate_schema(response, schema) is False
            
    
    def test_error_handling_rate_limit(self):
        """レート制限エラーのテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.side_effect = RateLimitError(
                    "rate_limit", response=MagicMock(), body=None
                )

                provider = OpenAIProvider()

                with pytest.raises(LLMError, match="APIレート制限に達しました"):
                    provider.call_llm("プロンプト", "speed")
    
    def test_error_handling_quota(self):
        """クォータ不足エラーのテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.side_effect = BadRequestError(
                    "quota", response=MagicMock(), body=None
                )

                provider = OpenAIProvider()

                with pytest.raises(LLMError, match="APIクォータが不足しています"):
                    provider.call_llm("プロンプト", "speed")
    
    def test_error_handling_invalid_api_key(self):
        """無効なAPIキーエラーのテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.side_effect = AuthenticationError(
                    "invalid", response=MagicMock(), body=None
                )

                provider = OpenAIProvider()

                with pytest.raises(LLMError, match="無効なAPIキーです"):
                    provider.call_llm("プロンプト", "speed")
    
    def test_error_handling_generic(self):
        """一般的なエラーのテスト"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                mock_client.chat.completions.create.side_effect = APIError(
                    "network error", request=MagicMock(), body=None
                )

                provider = OpenAIProvider()

                with pytest.raises(LLMError, match="LLM呼び出しでエラーが発生しました"):
                    provider.call_llm("プロンプト", "speed")

    def test_get_default_modes_clamps_low_values(self):
        """設定値が範囲外の場合にクランプされるかを検証"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI'):
                fake_settings = type('S', (), {'temperature': -1.0, 'max_tokens': 10000})()
                settings_manager = Mock()
                settings_manager.load_settings.return_value = fake_settings
                provider = OpenAIProvider(settings_manager=settings_manager)
                modes = provider.MODES
                assert modes['speed']['temperature'] == 0.0
                assert modes['deep']['temperature'] == 0.0
                assert modes['creative']['temperature'] == 0.0
                assert modes['speed']['max_tokens'] == 4000
                assert modes['deep']['max_tokens'] == 4000
                assert modes['creative']['max_tokens'] == 3200

    def test_get_default_modes_clamps_high_temperature(self):
        """温度が上限を超える場合にクランプされるかを検証"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI'):
                fake_settings = type('S', (), {'temperature': 5.0, 'max_tokens': 500})()
                settings_manager = Mock()
                settings_manager.load_settings.return_value = fake_settings
                provider = OpenAIProvider(settings_manager=settings_manager)
                modes = provider.MODES
                assert modes['speed']['temperature'] == 2.0
                assert modes['creative']['temperature'] == 2.0
                assert modes['deep']['temperature'] == pytest.approx(1.6)
                assert modes['speed']['max_tokens'] == 500

    def test_call_llm_retry_success(self):
        """リトライ後に成功するケース"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai, \
                 patch('tenacity.nap.time.sleep', return_value=None):
                mock_client = Mock()
                mock_openai.return_value = mock_client

                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "レスポンス"
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]

                mock_client.chat.completions.create.side_effect = [
                    RateLimitError("rate_limit", response=MagicMock(), body=None),
                    mock_response,
                ]

                provider = OpenAIProvider()
                result = provider.call_llm("プロンプト", "speed")

                assert result == {"content": "レスポンス"}
                assert mock_client.chat.completions.create.call_count == 2

    def test_call_llm_retry_failure(self):
        """リトライが全て失敗するケース"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai, \
                 patch('tenacity.nap.time.sleep', return_value=None):
                mock_client = Mock()
                mock_openai.return_value = mock_client

                error = RateLimitError("rate_limit", response=MagicMock(), body=None)
                mock_client.chat.completions.create.side_effect = [error, error, error]

                provider = OpenAIProvider()

                with pytest.raises(LLMError, match="APIレート制限に達しました"):
                    provider.call_llm("プロンプト", "speed")

                assert mock_client.chat.completions.create.call_count == 3

    def test_call_llm_usage_limit(self):
        """使用量メータが閾値を超えるとエラーを投げる"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'TOKEN_USAGE_LIMIT': '50'}):
            with patch('providers.llm_openai.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client

                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = "レスポンス"
                mock_message.refusal = None
                mock_choice.message = mock_message
                mock_choice.finish_reason = "stop"
                mock_response.choices = [mock_choice]
                usage = Mock()
                usage.total_tokens = 30
                mock_response.usage = usage
                mock_client.chat.completions.create.return_value = mock_response

                UsageMeter.reset()
                provider = OpenAIProvider()

                provider.call_llm("プロンプト", "speed", user_id="u1")

                with pytest.raises(LLMError, match="使用上限に達しました"):
                    provider.call_llm("プロンプト", "speed", user_id="u1")
