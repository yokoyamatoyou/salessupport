from typing import Optional, Dict, Any, Union
from enum import Enum
import traceback

class ErrorLevel(Enum):
    """エラーレベルの定義"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class SalesSaaSError(Exception):
    """SalesSaaSアプリケーションの基本例外クラス"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = None
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

class ValidationError(SalesSaaSError):
    """バリデーションエラー"""
    
    def __init__(self, message: str, field_name: str = None, field_value: str = None, 
                 validation_type: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "validation_error", details or {})
        self.field_name = field_name
        self.field_value = field_value
        self.validation_type = validation_type
    
    def get_field_specific_message(self) -> str:
        """フィールド固有のエラーメッセージを取得"""
        if self.field_name:
            return f"{self.field_name}: {self.message}"
        return self.message

class LLMError(SalesSaaSError):
    """LLM API呼び出しエラー"""
    pass

class ConfigurationError(SalesSaaSError):
    """設定ファイルエラー"""
    pass

class ServiceError(SalesSaaSError):
    """サービス実行エラー"""
    pass

class ErrorHandler:
    """アプリケーション全体のエラー処理サービス"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.error_messages = self._get_error_messages()
    
    def _get_error_messages(self) -> Dict[str, Dict[str, str]]:
        """エラーメッセージの定義"""
        return {
            "validation": {
                "required_field": "必須フィールドが入力されていません",
                "invalid_format": "入力形式が正しくありません",
                "xor_violation": "競合するフィールドが同時に入力されています",
                "field_too_short": "フィールドの文字数が不足しています",
                "field_too_long": "フィールドの文字数が上限を超えています",
                "invalid_character": "無効な文字が含まれています",
                "url_format": "URLの形式が正しくありません"
            },
            "llm": {
                "api_error": "AIサービスとの通信でエラーが発生しました",
                "timeout": "AIサービスの応答がタイムアウトしました",
                "invalid_response": "AIサービスからの応答が不正です",
                "rate_limit": "AIサービスの利用制限に達しました"
            },
            "configuration": {
                "file_not_found": "設定ファイルが見つかりません",
                "invalid_format": "設定ファイルの形式が正しくありません",
                "missing_required": "必須の設定項目が不足しています"
            },
            "service": {
                "initialization_failed": "サービスの初期化に失敗しました",
                "execution_failed": "サービスの実行に失敗しました",
                "dependency_missing": "必要な依存関係が不足しています"
            }
        }
    
    def handle_error(self, error: Exception, context: str = None, user_friendly: bool = True) -> Dict[str, Any]:
        """エラーの処理と適切なレスポンスの生成"""
        
        # エラーの詳細情報を収集
        error_info = self._collect_error_info(error, context)
        
        # ログ出力
        if self.logger:
            self.logger.error(
                f"Error occurred in {context or 'unknown context'}: {error_info['message']}",
                exc_info=error
            )
        
        # ユーザーフレンドリーなメッセージの生成
        if user_friendly:
            user_message = self._get_user_friendly_message(error_info)
        else:
            user_message = error_info['message']
        
        return {
            "success": False,
            "error": {
                "message": user_message,
                "code": error_info.get('code'),
                "type": error_info.get('type'),
                "details": error_info.get('details', {})
            },
            "timestamp": error_info.get('timestamp'),
            "context": context
        }
    
    def _collect_error_info(self, error: Exception, context: str = None) -> Dict[str, Any]:
        """エラー情報の収集"""
        error_info = {
            "message": str(error),
            "type": type(error).__name__,
            "timestamp": None,
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        # SalesSaaS固有のエラー情報
        if isinstance(error, SalesSaaSError):
            error_info.update({
                "code": error.error_code,
                "details": error.details
            })
        
        # エラータイプ別の詳細情報
        if isinstance(error, ValidationError):
            error_info["category"] = "validation"
        elif isinstance(error, LLMError):
            error_info["category"] = "llm"
        elif isinstance(error, ConfigurationError):
            error_info["category"] = "configuration"
        elif isinstance(error, ServiceError):
            error_info["category"] = "service"
        else:
            error_info["category"] = "unknown"
        
        return error_info
    
    def _get_user_friendly_message(self, error_info: Dict[str, Any]) -> str:
        """ユーザーフレンドリーなエラーメッセージの生成"""
        category = error_info.get("category")
        code = error_info.get("code")
        
        if category and code:
            # 定義済みメッセージの取得
            if category in self.error_messages and code in self.error_messages[category]:
                return self.error_messages[category][code]
        
        # デフォルトメッセージ
        default_messages = {
            "validation": "入力データに問題があります。内容を確認してください。",
            "llm": "AIサービスで問題が発生しました。しばらく時間をおいて再度お試しください。",
            "configuration": "アプリケーションの設定に問題があります。管理者にお問い合わせください。",
            "service": "サービスで問題が発生しました。しばらく時間をおいて再度お試しください。",
            "unknown": "予期しないエラーが発生しました。しばらく時間をおいて再度お試しください。"
        }
        
        return default_messages.get(category, default_messages["unknown"])
    
    def create_error_response(self, message: str, error_type: str = "general", 
                            details: Dict[str, Any] = None) -> Dict[str, Any]:
        """エラーレスポンスの作成"""
        return {
            "success": False,
            "error": {
                "message": message,
                "type": error_type,
                "details": details or {}
            }
        }
    
    def is_recoverable_error(self, error: Exception) -> bool:
        """エラーが回復可能かどうかの判定"""
        # 一時的なエラー（再試行可能）
        recoverable_errors = [
            "timeout",
            "rate_limit",
            "connection_error",
            "temporary_unavailable"
        ]
        
        error_str = str(error).lower()
        return any(re in error_str for re in recoverable_errors)
    
    def get_recovery_suggestion(self, error: Exception) -> Optional[str]:
        """エラー回復のための提案を取得"""
        if self.is_recoverable_error(error):
            return "しばらく時間をおいて再度お試しください。"
        return None
