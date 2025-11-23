import logging
import sys
from pathlib import Path
from config import config

def setup_logger(name):
    """共通ロガー設定"""
    logger = logging.getLogger(name)
    logger.setLevel(config.LOG_LEVEL)
    
    # 既存のハンドラをクリア
    if logger.handlers:
        logger.handlers.clear()
    
    # フォーマッター
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラ（オプション）
    log_file = config.LOG_DIR / f"{name}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
