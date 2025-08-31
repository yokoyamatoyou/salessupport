import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from .utils import mask_pii

class Logger:
    """アプリケーション全体のログ管理サービス"""
    
    def __init__(self, name: str = "SalesSaaS", log_level: str = "INFO", log_dir: str = "logs"):
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir)
        
        # ログディレクトリの作成
        self.log_dir.mkdir(exist_ok=True)
        
        # ロガーの設定
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        
        # 既存のハンドラーをクリア（重複を防ぐ）
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # コンソールハンドラー
        self._setup_console_handler()
        
        # ファイルハンドラー
        self._setup_file_handler()
        
        # フォーマッター
        self._setup_formatter()
    
    def _setup_console_handler(self):
        """コンソール出力用ハンドラーの設定"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """ファイル出力用ハンドラーの設定"""
        # 日付別のログファイル
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"{self.name}_{today}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.log_level)
        self.logger.addHandler(file_handler)
    
    def _setup_formatter(self):
        """ログフォーマッターの設定"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
    
    def info(self, message: str):
        """情報ログ"""
        self.logger.info(mask_pii(message))

    def warning(self, message: str):
        """警告ログ"""
        self.logger.warning(mask_pii(message))

    def error(self, message: str, exc_info: Optional[Exception] = None):
        """エラーログ"""
        if exc_info:
            self.logger.error(mask_pii(message), exc_info=exc_info)
        else:
            self.logger.error(mask_pii(message))

    def debug(self, message: str):
        """デバッグログ"""
        self.logger.debug(mask_pii(message))

    def critical(self, message: str, exc_info: Optional[Exception] = None):
        """重大エラーログ"""
        if exc_info:
            self.logger.critical(mask_pii(message), exc_info=exc_info)
        else:
            self.logger.critical(mask_pii(message))
    
    def log_user_action(self, user_action: str, details: dict = None):
        """ユーザーアクションのログ"""
        message = f"USER_ACTION: {user_action}"
        if details:
            message += f" - Details: {details}"
        self.info(message)
    
    def log_service_call(self, service_name: str, method: str, params: dict = None):
        """サービス呼び出しのログ"""
        message = f"SERVICE_CALL: {service_name}.{method}"
        if params:
            message += f" - Params: {params}"
        self.info(message)
    
    def log_api_call(self, api_name: str, success: bool, response_time: float = None):
        """API呼び出しのログ"""
        status = "SUCCESS" if success else "FAILED"
        message = f"API_CALL: {api_name} - {status}"
        if response_time:
            message += f" - Response time: {response_time:.2f}s"
        
        if success:
            self.info(message)
        else:
            self.warning(message)
