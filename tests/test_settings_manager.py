import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from services.settings_manager import SettingsManager
from core.models import AppSettings, LLMMode, SearchProvider

class TestSettingsManager:
    """SettingsManagerのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "config" / "settings.json"
        self.settings_manager = SettingsManager(str(self.config_file))
    
    def teardown_method(self):
        """各テストメソッドの後処理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """初期化のテスト"""
        assert self.settings_manager.config_file == self.config_file
        assert self.settings_manager._settings is None
    
    def test_load_settings_new_file(self):
        """新規設定ファイルの読み込みテスト"""
        settings = self.settings_manager.load_settings()

        assert isinstance(settings, AppSettings)
        assert settings.openai_model == "gpt-4o-mini"
        assert settings.default_llm_mode == LLMMode.SPEED
        assert settings.max_tokens == 1000
        assert settings.temperature == 0.7
        assert settings.search_provider == SearchProvider.STUB
        assert settings.language == "ja"
        assert settings.theme == "light"
        assert settings.show_tutorial_on_start is True
        
        # 設定ファイルが作成されていることを確認
        assert self.config_file.exists()
    
    def test_load_settings_existing_file(self):
        """既存設定ファイルの読み込みテスト"""
        # テスト用の設定データ
        test_settings = {
            "openai_model": "gpt-test",
            "default_llm_mode": "deep",
            "max_tokens": 2000,
            "temperature": 0.5,
            "search_provider": "newsapi",
            "language": "en",
            "theme": "dark"
        }
        
        # 設定ファイルを作成
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(test_settings, f)
        
        # 設定を読み込み
        settings = self.settings_manager.load_settings()
        
        assert settings.openai_model == "gpt-test"
        assert settings.default_llm_mode == LLMMode.DEEP
        assert settings.max_tokens == 2000
        assert settings.temperature == 0.5
        assert settings.search_provider == SearchProvider.NEWSAPI
        assert settings.language == "en"
        assert settings.theme == "dark"
        assert settings.show_tutorial_on_start is True
    
    def test_load_settings_invalid_file(self):
        """無効な設定ファイルの読み込みテスト"""
        # 無効なJSONファイルを作成
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        # デフォルト設定が読み込まれることを確認
        settings = self.settings_manager.load_settings()
        assert settings.default_llm_mode == LLMMode.SPEED
    
    def test_save_settings(self):
        """設定の保存テスト"""
        settings = AppSettings(
            default_llm_mode=LLMMode.CREATIVE,
            max_tokens=1500,
            temperature=0.9
        )
        
        result = self.settings_manager.save_settings(settings)
        assert result is True
        
        # 設定ファイルが作成されていることを確認
        assert self.config_file.exists()
        
        # 保存された内容を確認
        with open(self.config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert saved_data["openai_model"] == "gpt-4o-mini"
        assert saved_data["default_llm_mode"] == "creative"
        assert saved_data["max_tokens"] == 1500
        assert saved_data["temperature"] == 0.9
    
    def test_update_setting(self):
        """特定設定の更新テスト"""
        # 初期設定を読み込み
        self.settings_manager.load_settings()
        
        # 設定を更新
        result = self.settings_manager.update_setting("temperature", 0.8)
        assert result is True
        
        # 更新された設定を確認
        updated_settings = self.settings_manager.load_settings()
        assert updated_settings.temperature == 0.8
    
    def test_update_setting_invalid_key(self):
        """無効な設定キーの更新テスト"""
        self.settings_manager.load_settings()
        
        result = self.settings_manager.update_setting("invalid_key", "value")
        assert result is False
    
    def test_get_setting(self):
        """特定設定の取得テスト"""
        self.settings_manager.load_settings()
        
        temperature = self.settings_manager.get_setting("temperature")
        assert temperature == 0.7
        
        # デフォルト値のテスト
        invalid_setting = self.settings_manager.get_setting("invalid_key", "default")
        assert invalid_setting == "default"
    
    def test_reset_to_defaults(self):
        """デフォルト設定へのリセットテスト"""
        # カスタム設定を作成
        custom_settings = AppSettings(
            default_llm_mode=LLMMode.DEEP,
            max_tokens=3000,
            temperature=0.1
        )
        self.settings_manager.save_settings(custom_settings)
        
        # リセットを実行
        result = self.settings_manager.reset_to_defaults()
        assert result is True
        
        # デフォルト設定に戻っていることを確認
        reset_settings = self.settings_manager.load_settings()
        assert reset_settings.default_llm_mode == LLMMode.SPEED
        assert reset_settings.max_tokens == 1000
        assert reset_settings.temperature == 0.7
    
    def test_export_settings(self):
        """設定のエクスポートテスト"""
        self.settings_manager.load_settings()
        
        export_path = Path(self.temp_dir) / "exported_settings.json"
        result = self.settings_manager.export_settings(str(export_path))
        
        assert result is True
        assert export_path.exists()
        
        # エクスポートされた内容を確認
        with open(export_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        assert "default_llm_mode" in exported_data
        assert "max_tokens" in exported_data
        assert "temperature" in exported_data
        assert "openai_model" in exported_data
    
    def test_import_settings(self):
        """設定のインポートテスト"""
        # インポート用の設定データ
        import_data = {
            "openai_model": "gpt-import",
            "default_llm_mode": "creative",
            "max_tokens": 2500,
            "temperature": 0.6,
            "search_provider": "cse"
        }
        
        import_path = Path(self.temp_dir) / "import_settings.json"
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(import_data, f)
        
        # インポートを実行
        result = self.settings_manager.import_settings(str(import_path))
        assert result is True
        
        # インポートされた設定を確認
        imported_settings = self.settings_manager.load_settings()
        assert imported_settings.openai_model == "gpt-import"
        assert imported_settings.default_llm_mode == LLMMode.CREATIVE
        assert imported_settings.max_tokens == 2500
        assert imported_settings.temperature == 0.6
        assert imported_settings.search_provider == SearchProvider.CSE
    
    def test_import_settings_invalid_file(self):
        """無効なファイルのインポートテスト"""
        # 存在しないファイルのインポート
        result = self.settings_manager.import_settings("nonexistent_file.json")
        assert result is False
    
    def test_get_llm_config(self):
        """LLM設定の取得テスト"""
        self.settings_manager.load_settings()
        
        llm_config = self.settings_manager.get_llm_config()

        assert "mode" in llm_config
        assert "max_tokens" in llm_config
        assert "temperature" in llm_config
        assert "model" in llm_config
        assert llm_config["mode"] == LLMMode.SPEED
        assert llm_config["max_tokens"] == 1000
        assert llm_config["temperature"] == 0.7
        assert llm_config["model"] == "gpt-4o-mini"
    
    def test_get_search_config(self):
        """検索設定の取得テスト"""
        self.settings_manager.load_settings()
        
        search_config = self.settings_manager.get_search_config()
        
        assert "provider" in search_config
        assert "limit" in search_config
        assert search_config["provider"] == SearchProvider.STUB
        assert search_config["limit"] == 5

    def test_hybrid_search_provider_persistence(self):
        """hybridプロバイダー設定の永続化テスト"""
        # 事前にhybrid設定をファイルに保存
        settings = AppSettings(search_provider=SearchProvider.HYBRID)
        self.settings_manager.save_settings(settings)

        # 設定を読み込みhybridが適用されることを確認
        loaded = self.settings_manager.load_settings()
        assert loaded.search_provider == SearchProvider.HYBRID

        # 新しいインスタンスで再読込し、設定が保持されていることを確認
        new_manager = SettingsManager(str(self.config_file))
        reloaded = new_manager.load_settings()
        assert reloaded.search_provider == SearchProvider.HYBRID

        # get_search_configでもhybridが取得されることを確認
        search_config = new_manager.get_search_config()
        assert search_config["provider"] == SearchProvider.HYBRID
    
    def test_get_ui_config(self):
        """UI設定の取得テスト"""
        self.settings_manager.load_settings()
        
        ui_config = self.settings_manager.get_ui_config()
        
        assert "language" in ui_config
        assert "theme" in ui_config
        assert "auto_save" in ui_config
        assert ui_config["language"] == "ja"
        assert ui_config["theme"] == "light"
        assert ui_config["auto_save"] is True

    def test_crm_setting(self):
        """CRM設定の永続化テスト"""
        self.settings_manager.load_settings()
        result = self.settings_manager.update_setting("crm_enabled", True)
        assert result is True
        assert self.settings_manager.get_setting("crm_enabled") is True
    
    def test_settings_persistence(self):
        """設定の永続化テスト"""
        # 初期設定を読み込み
        initial_settings = self.settings_manager.load_settings()
        
        # 設定を変更
        initial_settings.temperature = 0.5
        initial_settings.max_tokens = 1500
        
        # 保存
        self.settings_manager.save_settings(initial_settings)
        
        # 新しいインスタンスで設定を読み込み
        new_manager = SettingsManager(str(self.config_file))
        loaded_settings = new_manager.load_settings()
        
        # 設定が保持されていることを確認
        assert loaded_settings.temperature == 0.5
        assert loaded_settings.max_tokens == 1500
