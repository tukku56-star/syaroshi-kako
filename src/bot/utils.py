"""
Bot System Utilities

汎用ユーティリティ関数
"""
import os
import random
from datetime import datetime
from config import config
from src.utils.logger import setup_logger
from .constants import SNS_NAMES

logger = setup_logger("bot.utils")


def generate_random_name():
    """Generate natural SNS-style name without numbers"""
    return random.choice(SNS_NAMES)


def sanitize_filename(name):
    """Sanitize room name for use as filename"""
    if not name:
        return "unknown"
    
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    sanitized = name
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    sanitized = sanitized.replace(' ', '_')
    
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    return sanitized


def get_drive_log_dir():
    """Get today's Google Drive log directory"""
    if not config.GOOGLE_DRIVE_ENABLED:
        return None
    
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        drive_log_dir = os.path.join(config.GOOGLE_DRIVE_PATH, today, "log")
        
        if not os.path.exists(drive_log_dir):
            os.makedirs(drive_log_dir)
        
        return drive_log_dir
    except Exception as e:
        logger.error(f"Google Drive error: {e}")
        return None
