"""
Message Saver

メッセージの保存とデータ処理を担当
"""
import os
import json
from datetime import datetime
from config import config
from src.utils.logger import setup_logger
from .utils import sanitize_filename, get_drive_log_dir

logger = setup_logger("bot.message_saver")


class MessageSaver:
    """Handle saving messages from AJAX responses"""
    
    @staticmethod
    async def save_ajax_data(data, room_id, room_name, bot_name):
        """Save only new messages incrementally to Google Drive or local fallback"""
        try:
            # Try Google Drive first, fallback to local
            drive_dir = get_drive_log_dir()
            if drive_dir:
                save_dir = drive_dir
            else:
                # Fallback to local LOG_DIR
                save_dir = config.LOG_DIR
                if not save_dir.exists():
                    save_dir.mkdir(parents=True)
            
            safe_room_name = sanitize_filename(room_name)
            log_file = os.path.join(save_dir, f"room_{room_id}_{safe_room_name}.json")
            
            # Load existing messages to get known message IDs
            existing_msg_ids = set()
            all_messages = []
            
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        file_data = json.load(f)
                        if isinstance(file_data, dict) and 'messages' in file_data:
                            all_messages = file_data['messages']
                            for msg in all_messages:
                                if 'id' in msg:
                                    existing_msg_ids.add(msg['id'])
                except Exception as e:
                    logger.error(f"[{bot_name}] Error loading existing file: {e}")
            
            # Extract data from AJAX response
            hostip = data.get('hostip', '')
            talks = data.get('talks', [])
            users = data.get('users', {})
            
            # Convert users dict to lookup format
            user_dict = {}
            if isinstance(users, dict):
                for user_data in users.values():
                    if isinstance(user_data, dict) and 'id' in user_data:
                        user_dict[user_data['id']] = user_data
            
            # Handle both list and dict formats for talks
            talks_list = []
            if isinstance(talks, dict):
                talks_list = list(talks.values())
            elif isinstance(talks, list):
                talks_list = talks
            
            # Extract new messages only
            new_messages = []
            for talk_data in talks_list:
                if not isinstance(talk_data, dict):
                    continue
                
                msg_id = talk_data.get('id', '')
                if not msg_id or msg_id in existing_msg_ids:
                    continue  # Skip duplicates
                
                # Filter system messages
                talk_type = talk_data.get('type', '')
                if talk_type in ['enter', 'exit', 'system']:
                    continue
                
                message = talk_data.get('message', '')
                if isinstance(message, str):
                    if any(word in message for word in ['入室しました', '退室しました', '接続が切れました']):
                        continue
                
                # Get user info
                uid = talk_data.get('uid', '')
                user_info = user_dict.get(uid, {})
                
                # Determine encip (use hostip ONLY if we are sure, but for now just trust the message/user data)
                # defaulting to hostip for everyone is incorrect as pointed out by user
                encip = talk_data.get('encip', user_info.get('encip', ''))
                
                # Create message entry
                msg_entry = {
                    'id': msg_id,
                    'uid': uid,
                    'name': talk_data.get('name', '名無し'),
                    'message': message,
                    'time': talk_data.get('time', 0),
                    'icon': talk_data.get('icon', ''),
                    'encip': encip,
                    'trip': talk_data.get('trip', user_info.get('trip', '')),
                    'captured_at': datetime.now().isoformat()
                }
                
                new_messages.append(msg_entry)
                existing_msg_ids.add(msg_id)
            
            # Only save if there are new messages
            if new_messages:
                all_messages.extend(new_messages)
                
                # Sort by time
                all_messages.sort(key=lambda x: x.get('time', 0))
                
                # Save to file
                file_content = {
                    'room_id': room_id,
                    'room_name': room_name,
                    'hostip': hostip,
                    'last_updated': datetime.now().isoformat(),
                    'total_messages': len(all_messages),
                    'messages': all_messages
                }
                
                try:
                    with open(log_file, "w", encoding="utf-8") as f:
                        json.dump(file_content, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"[{bot_name}] +{len(new_messages)} new messages (total: {len(all_messages)})")
                except Exception as e:
                    logger.error(f"[{bot_name}] Save error: {e}")
                    
        except Exception as e:
            logger.error(f"[{bot_name}] Save error: {e}")
