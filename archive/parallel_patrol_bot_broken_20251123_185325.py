import os
import json
import asyncio
import random
import string
from datetime import datetime
from playwright.async_api import async_playwright
from config import config, PROJECT_ROOT
from src.utils.logger import setup_logger

# Logger setup
logger = setup_logger("bot")

# Configuration
BASE_URL = "https://drrrkari.com"
LOGIN_URL = f"{BASE_URL}/"
LOUNGE_URL = f"{BASE_URL}/lounge/"

# Retry limit for room search
MAX_SEARCH_RETRIES = 10

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

# Available icons
AVAILABLE_ICONS = [
    "girl", "moza", "tanaka", "kanra", "usa", "gg", "orange", "zaika", "setton", "zawa",
    "bakyura", "mika", "numabuto", "numabuto_B", 
    "muffler_girl", "muffler_moza", "muffler_tanaka", "muffler_kanra", "muffler_usa", 
    "muffler_gg", "muffler_orange", "muffler_zaika", "muffler_setton", "muffler_zawa", 
    "muffler_bakyura", "muffler_mika"
]

# SNS-style natural names
SNS_NAMES = [
    "ゆうき", "あおい", "はるか", "りょう", "さくら", "まな", "ゆい", "そら",
    "ひなた", "りく", "めい", "あかり", "そうた", "はると", "ゆうま", "ゆうと",
    "れん", "かい", "こはる", "ひまり", "さな", "ももか", "りお",
    "まゆ", "のん", "りん", "えみ", "なつ", "みお", "あい", "ゆき", "さき",
    "ちひろ", "かえで", "まい", "なな", "ゆな", "あやか", "ゆうこ", "れいな",
    "Rui", "Kai", "Ren", "Mio", "Rio", "Leo", "Sora", "Luna",
    "Haru", "Yuki", "Nana", "Rin", "Mei", "Aoi", "Rei", "Saki",
    "ゆうちゃん", "りーちゃん", "あおくん", "まなみん", "そらさん", "めいめい",
    "ゆいぴ", "はるぴ", "まゆゆ", "りんりん", "なっちゃん", "さっちゃん"
]

def generate_random_name():
    """Generate natural SNS-style name without numbers"""
    # Simple random choice from the list
    return random.choice(SNS_NAMES)

def sanitize_filename(name):
    """Sanitize room name for filename"""
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

class RoomMonitor:
    def __init__(self, browser, room_id, room_name, bot_name, bot_icon, parent_bot):
        self.browser = browser
        self.room_id = room_id
        self.room_name = room_name
        self.bot_name = bot_name
        self.bot_icon = bot_icon
        self.parent_bot = parent_bot
        self.context = None
        self.page = None
        
        if room_id and room_name:
            safe_room_name = sanitize_filename(room_name)
            self.log_file = config.LOG_DIR / f"room_{room_id}_{safe_room_name}.json"
        else:
            self.log_file = None
            
        self.running = True
        self.in_room = False
        self.blacklist = set()
        self.last_activity = datetime.now()
        self.activity_timeout = 300
        # Bot status tracking
        self.current_status = "Searching"
        # Retry counter for room search
        self.search_retry_count = 0
        
    async def _handle_response(self, response):
        try:
            if "ajax.php" in response.url:
                try:
                    data = await response.json()
                    # logger.debug(f"[{self.bot_name}] Received ajax response")
                    await self._save_data(data)
                except Exception as e:
                    logger.error(f"[{self.bot_name}] Error processing ajax response: {e}")
        except:
            pass
                
    async def _save_data(self, data):
        """Save only new messages incrementally to Google Drive or local fallback"""
        try:
            self.last_activity = datetime.now()
            
            # Try Google Drive first, fallback to local
            drive_dir = get_drive_log_dir()
            if drive_dir:
                save_dir = drive_dir
            else:
                # Fallback to local LOG_DIR
                save_dir = config.LOG_DIR
                if not save_dir.exists():
                    save_dir.mkdir(parents=True)
            
            safe_room_name = sanitize_filename(self.room_name)
            drive_log_file = os.path.join(save_dir, f"room_{self.room_id}_{safe_room_name}.json")
            
            # Load existing messages to get known message IDs
            existing_msg_ids = set()
            all_messages = []
            
            if os.path.exists(drive_log_file):
                try:
                    with open(drive_log_file, "r", encoding="utf-8") as f:
                        file_data = json.load(f)
                        if isinstance(file_data, dict) and 'messages' in file_data:
                            all_messages = file_data['messages']
                            for msg in all_messages:
                                if 'id' in msg:
                                    existing_msg_ids.add(msg['id'])
                except Exception as e:
                    logger.error(f"[{self.bot_name}] Error loading existing file: {e}")
            
            # Extract hostip
            hostip = data.get('hostip', '')
            
            # Extract talks from current data
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
                
                # Determine encip (use hostip if empty and available)
                encip = talk_data.get('encip', user_info.get('encip', ''))
                if not encip and hostip:
                    # If encip is empty, it might be the host
                    # We can't be 100% sure without more logic, but user requested using hostip
                    # Let's store it.
                    encip = hostip

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
                    'room_id': self.room_id,
                    'room_name': self.room_name,
                    'hostip': hostip,
                    'last_updated': datetime.now().isoformat(),
                    'total_messages': len(all_messages),
                    'messages': all_messages
                }
                
                try:
                    with open(drive_log_file, "w", encoding="utf-8") as f:
                        json.dump(file_content, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"[{self.bot_name}] +{len(new_messages)} new messages (total: {len(all_messages)})")
            self.page.on("response", self._handle_response)
            
            logger.info(f"[{self.bot_name}] Starting...")
            
            await self.page.goto(LOGIN_URL)
            await asyncio.sleep(2)
            
            try:
                icon_selector = f"img[src*='icon_{self.bot_icon}.png']"
                icon_img = await self.page.query_selector(icon_selector)
                if icon_img:
                    await icon_img.click()
                    await asyncio.sleep(0.5)
                else:
                    default_icon = await self.page.query_selector("img[src*='icon_girl.png']")
                    if default_icon:
                        await default_icon.click()
                        await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"[{self.bot_name}] Icon selection error: {e}")
            
            await self.page.fill("input[name='name']", self.bot_name)
            await self.page.click("a.bb.cc")
            await asyncio.sleep(2)
            
            # Main monitoring loop
            while self.running:
                try:
                    if not self.in_room:
                        if await self._find_and_enter_unmanned_room():
                            self.in_room = True
                            self.current_status = "In Room"
                            self.search_retry_count = 0
                        else:
                            logger.info(f"[{self.bot_name}] No available rooms found")
                            self.search_retry_count += 1
                            if self.search_retry_count >= MAX_SEARCH_RETRIES:
                                logger.warning(f"[{self.bot_name}] Max retries reached, marking as failed")
                                self.current_status = "Failed"
                                self.running = False
                                break
                            await asyncio.sleep(5)
                    else:
                        # Check if still in room
                        if "/room/" not in self.page.url:
                            logger.info(f"[{self.bot_name}] Disconnected from room")
                            self.in_room = False
                            self.room_id = None
                            self.room_name = None
                            self.current_status = "Searching"
                            continue
                        
                        # Check for inactivity
                        if (datetime.now() - self.last_activity).total_seconds() > self.activity_timeout:
                            logger.info(f"[{self.bot_name}] Inactive for too long, leaving...")
                            await self.page.click("input[name='logout']")
                            self.in_room = False
                            self.current_status = "Searching"
                            continue
                        
                        # Just wait - messages are captured via response handler
                        await asyncio.sleep(10)
                        
                except Exception as e:
                    logger.error(f"[{self.bot_name}] Loop error: {e}")
                    await asyncio.sleep(5)
                    try:
                        await self.page.reload()
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"[{self.bot_name}] Fatal error: {e}")
        finally:
            if self.context:
                await self.context.close()

class ParallelPatrolBot:
    def __init__(self):
        self.monitors = []
        self.playwright = None
        self.browser = None
        self.occupied_rooms = set()
        
    def get_occupied_rooms(self):
        rooms = set()
        for monitor in self.monitors:
            if monitor.in_room and monitor.room_id:
                rooms.add(monitor.room_id)
        return rooms

    async def start(self):
        async with async_playwright() as p:
            self.playwright = p
            self.browser = await p.chromium.launch(headless=True)
            
            logger.info("[*] Getting room list...")
            
            # Create initial monitors
            tasks = []
            
            # Ensure unique icons
            available_icons = AVAILABLE_ICONS.copy()
            random.shuffle(available_icons)
            
            # Limit monitors to available icons if needed, though MAX_MONITORS is 20 and icons are 26
            num_monitors = min(config.MAX_MONITORS, len(available_icons))
            
            for i in range(num_monitors):
                bot_name = generate_random_name()
                bot_icon = available_icons.pop()
                
                monitor = RoomMonitor(
                    self.browser, 
                    None, 
                    None, 
                    bot_name, 
                    bot_icon,
                    self
                )
                self.monitors.append(monitor)
                tasks.append(asyncio.create_task(monitor.start()))
            
            logger.info(f"[*] Started {len(tasks)} monitors")
            
            # Main loop
            while True:
                await self.save_status()
                await asyncio.sleep(5)

    async def save_status(self):
        """Save current status of all bots"""
        print("DEBUG: Inside save_status")
        try:
            status_list = []
            for monitor in self.monitors:
                status = {
                    'name': monitor.bot_name,
                    'icon': monitor.bot_icon,
                    'status': monitor.current_status,
                    'room_name': monitor.room_name if monitor.room_name else '',
                    'room_id': monitor.room_id if monitor.room_id else '',
                    'last_activity': monitor.last_activity.isoformat() if monitor.last_activity else datetime.now().isoformat()
                }
                status_list.append(status)
            
            # Atomic write
            status_file = PROJECT_ROOT / "data" / "bot_status.json"
            temp_file = status_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(status_list, f, ensure_ascii=False, indent=2)
            
            os.replace(temp_file, status_file)
            
        except Exception as e:
            logger.error(f"Error saving status: {e}")

if __name__ == "__main__":
    bot = ParallelPatrolBot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("\n[*] Stopping...")
