"""
Logging configuration for the Sales SaaS application
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, Any

def setup_logging(level: str = "INFO", log_to_file: bool = True) -> None:
    """アプリケーション全体のログ設定を初期化"""

    # ログレベルの設定
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # フォーマッタの設定
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.addHandler(console_handler)

    if log_to_file:
        # ログディレクトリの作成
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # ファイルハンドラ（ローテーション）
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "sales_saas.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.WARNING)  # WARNING以上をファイルに記録
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # アプリケーションログファイル
        app_file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "application.log",
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        app_file_handler.setLevel(logging.INFO)
        app_file_handler.setFormatter(formatter)
        root_logger.addHandler(app_file_handler)

def get_logger(name: str) -> logging.Logger:
    """指定された名前のロガーを取得"""
    return logging.getLogger(name)

def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs) -> None:
    """パフォーマンスログを記録"""
    extra_data = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"PERFORMANCE: {operation} took {duration:.3f}s {extra_data}")

def log_error_with_context(logger: logging.Logger, error: Exception, context: Dict[str, Any]) -> None:
    """エラーをコンテキスト情報とともに記録"""
    context_str = " ".join(f"{k}={v}" for k, v in context.items())
    logger.error(f"ERROR: {error.__class__.__name__}: {error} | Context: {context_str}", exc_info=True)

def log_security_event(logger: logging.Logger, event: str, user_id: str = None, **details) -> None:
    """セキュリティイベントを記録"""
    details_str = " ".join(f"{k}={v}" for k, v in details.items())
    user_info = f"User: {user_id} " if user_id else ""
    logger.warning(f"SECURITY: {event} | {user_info}{details_str}")
