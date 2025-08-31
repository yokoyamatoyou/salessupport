import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from core.models import AppSettings, LLMMode, SearchProvider

class SettingsManager:
    """アプリケーション設定の管理"""
    
    def __init__(self, config_file: str = "config/settings.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)
        self._settings: Optional[AppSettings] = None
    
    def load_settings(self) -> AppSettings:
        """設定を読み込み"""
        if self._settings is not None:
            return self._settings
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._settings = AppSettings(**data)
            except Exception as e:
                print(f"設定ファイルの読み込みに失敗: {e}")
                self._settings = AppSettings()
        else:
            self._settings = AppSettings()
            self.save_settings()
        
        return self._settings
    
    def save_settings(self, settings: Optional[AppSettings] = None) -> bool:
        """設定を保存"""
        if settings is not None:
            self._settings = settings
        
        if self._settings is None:
            return False
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings.model_dump(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"設定ファイルの保存に失敗: {e}")
            return False
    
    def update_setting(self, key: str, value: Any) -> bool:
        """特定の設定を更新"""
        settings = self.load_settings()

        if hasattr(settings, key):
            if key == "search_provider":
                try:
                    value = SearchProvider(value)
                except Exception:
                    value = SearchProvider.STUB
            setattr(settings, key, value)
            return self.save_settings(settings)
        return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """特定の設定を取得"""
        settings = self.load_settings()
        return getattr(settings, key, default)
    
    def reset_to_defaults(self) -> bool:
        """デフォルト設定にリセット"""
        self._settings = AppSettings()
        return self.save_settings()
    
    def export_settings(self, export_path: str) -> bool:
        """設定をエクスポート"""
        try:
            settings = self.load_settings()
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(settings.model_dump(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"設定のエクスポートに失敗: {e}")
            return False
    
    def import_settings(self, import_path: str) -> bool:
        """設定をインポート"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            imported_settings = AppSettings(**data)
            return self.save_settings(imported_settings)
        except Exception as e:
            print(f"設定のインポートに失敗: {e}")
            return False
    
    def get_llm_config(self) -> Dict[str, Any]:
        """LLM設定を取得"""
        settings = self.load_settings()
        return {
            "mode": settings.default_llm_mode,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "model": settings.openai_model,
        }
    
    def get_search_config(self) -> Dict[str, Any]:
        """検索設定を取得"""
        settings = self.load_settings()
        return {
            "provider": settings.search_provider,
            "limit": settings.search_results_limit
        }
    
    def get_ui_config(self) -> Dict[str, Any]:
        """UI設定を取得"""
        settings = self.load_settings()
        return {
            "language": settings.language,
            "theme": settings.theme,
            "auto_save": settings.auto_save,
            "show_tutorial_on_start": settings.show_tutorial_on_start
        }
