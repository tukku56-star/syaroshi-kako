"""
Status Manager

ボットステータスの管理と保存
"""
import os
import json
from datetime import datetime
from config import PROJECT_ROOT
from src.utils.logger import setup_logger

logger = setup_logger("bot.status_manager")


class StatusManager:
    """Manage bot status saving and updates"""
    
    @staticmethod
    async def save_bot_status(monitors):
        """Save current status of all bots to bot_status.json
        
        Args:
            monitors: List of RoomMonitor instances
        """
        try:
            status_list = []
            for monitor in monitors:
                status = {
                    'name': monitor.bot_name,
                    'icon': monitor.bot_icon,
                    'status': monitor.current_status,
                    'room_name': monitor.room_name if monitor.room_name else '',
                    'room_id': monitor.room_id if monitor.room_id else '',
                    'last_activity': monitor.last_activity.isoformat() if monitor.last_activity else datetime.now().isoformat()
                }
                status_list.append(status)
            
            # Atomic write to prevent corruption
            status_file = PROJECT_ROOT / "data" / "bot_status.json"
            temp_file = status_file.with_suffix('.tmp')
            
            # Ensure directory exists
            status_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(status_list, f, ensure_ascii=False, indent=2)
            
            os.replace(temp_file, status_file)
            
            logger.debug(f"Saved status for {len(monitors)} bots")
            
        except Exception as e:
            logger.error(f"Error saving status: {e}")
