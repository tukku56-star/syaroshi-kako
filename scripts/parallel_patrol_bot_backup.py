import os
import json
import asyncio
import random
import string
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
BASE_URL = "https://drrrkari.com"
LOGIN_URL = f"{BASE_URL}/"
LOUNGE_URL = f"{BASE_URL}/lounge/"
LOG_DIR = "log"
MAX_MONITORS = 30

# Google Drive settings
GOOGLE_DRIVE = r"G:\マイドライブ\開発関連"
ENABLE_DRIVE_BACKUP = True

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_drive_log_dir():
    """Get today's Google Drive log directory"""
    if not ENABLE_DRIVE_BACKUP:
        return None
    
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        drive_log_dir = os.path.join(GOOGLE_DRIVE, today, "logs")
        
        if not os.path.exists(drive_log_dir):
            os.makedirs(drive_log_dir)
        
        return drive_log_dir
    except Exception as e:
        print(f"[!] Google Drive error: {e}")
        return None

# Available icons
AVAILABLE_ICONS = [
    "default", "boy", "girl", "man", "woman", "neko", "neko2", 
    "inu", "kuma", "kitsune", "usagi", "panda", "zou", "kaeru",
    "kai", "tako", "same", "kinoko", "alien", "robot", "ghost",
    "bm", "wm", "bear", "frog", "sakana"
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
    """Generate natural SNS-style name"""
    pattern_type = random.randint(0, 4)
    
    if pattern_type == 0:
        return random.choice(SNS_NAMES)
    elif pattern_type == 1:
        base = random.choice(SNS_NAMES[:40])
        num = random.randint(0, 99)
        name = f"{base}{num:02d}" if random.random() > 0.5 else f"{base}{num}"
        return name[:10]
    elif pattern_type == 2:
        base = random.choice(SNS_NAMES[:30])
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        name = f"{base}{month:02d}{day:02d}"
        return name[:10]
    elif pattern_type == 3:
        base = random.choice(['yuki', 'mio', 'rin', 'rei', 'haru', 'sora', 'kai', 'ren', 'rui', 'aoi'])
        num = random.randint(0, 99)
        name = f"{base}_{num}"
        return name[:10]
    else:
        prefixes = ['ゆ', 'り', 'み', 'あ', 'さ', 'な', 'ま', 'は', 'か']
        middles = ['う', 'ん', 'い', 'お']
        suffixes = ['き', 'な', 'こ', 'ちゃん', 'た', 'か']
        name = random.choice(prefixes) + random.choice(middles) + random.choice(suffixes)
        return name[:10]

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
            self.log_file = f"{LOG_DIR}/room_{room_id}_{safe_room_name}.json"
        else:
            self.log_file = None
            
        self.running = True
        self.in_room = False
        self.blacklist = set()
        self.last_activity = datetime.now()
        self.activity_timeout = 300
        
    async def _handle_response(self, response):
        try:
            if "room" in response.url and "talks" in response.url:
                try:
                    data = await response.json()
                    await self._save_data(data)
                except:
                    pass
        except:
            pass
                
    async def _save_data(self, data):
        """Save only new messages incrementally to Google Drive"""
        try:
            self.last_activity = datetime.now()
            
            drive_dir = get_drive_log_dir()
            if not drive_dir:
                print(f"[{self.bot_name}] Google Drive not available")
                return
            
            safe_room_name = sanitize_filename(self.room_name)
            drive_log_file = os.path.join(drive_dir, f"room_{self.room_id}_{safe_room_name}.json")
            
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
                    print(f"[{self.bot_name}] Error loading existing file: {e}")
            
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
                
                # Create message entry
                msg_entry = {
                    'id': msg_id,
                    'uid': uid,
                    'name': talk_data.get('name', '名無し'),
                    'message': message,
                    'time': talk_data.get('time', 0),
                    'icon': talk_data.get('icon', ''),
                    'encip': talk_data.get('encip', user_info.get('encip', '')),
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
                    'last_updated': datetime.now().isoformat(),
                    'total_messages': len(all_messages),
                    'messages': all_messages
                }
                
                try:
                    with open(drive_log_file, "w", encoding="utf-8") as f:
                        json.dump(file_content, f, indent=2, ensure_ascii=False)
                    
                    print(f"[{self.bot_name}] +{len(new_messages)} new messages (total: {len(all_messages)})")
                except Exception as e:
                    print(f"[{self.bot_name}] Google Drive save error: {e}")
                    
        except Exception as e:
            print(f"[{self.bot_name}] Save error: {e}")
    
    async def _check_for_password_screen(self):
        try:
            pwd_input = await self.page.query_selector("input[type='password']")
            if pwd_input:
                return True
            if "password" in self.page.url.lower():
                return True
            return False
        except:
            return False
    
    async def _enter_room(self, room_id):
        try:
            occupied_rooms = self.parent_bot.get_occupied_rooms()
            if room_id in occupied_rooms:
                print(f"[{self.bot_name}] Room already occupied, skipping")
                return False
            
            room_uls = await self.page.query_selector_all("ul.rooms.clearfix")
            
            for ul in room_uls:
                try:
                    if not await ul.is_visible():
                        continue
                    
                    id_input = await ul.query_selector("input[name='id']")
                    if not id_input:
                        continue
                        
                    found_id = await id_input.get_attribute("value")
                    if found_id == room_id:
                        print(f"[{self.bot_name}] Found target room {room_id} for entry")
                        knock_indicator = await ul.query_selector("i.fa-hand-paper")
                        if knock_indicator:
                            print(f"[{self.bot_name}] Knock required, skipping")
                            return False
                        
                        login_btn = await ul.query_selector("button[name='login'], input[type='submit'][name='login']")
                        if login_btn and await login_btn.is_visible():
                            occupied_rooms = self.parent_bot.get_occupied_rooms()
                            if room_id in occupied_rooms:
                                print(f"[{self.bot_name}] Room occupied during entry, skipping")
                                return False
                            
                            print(f"[{self.bot_name}] Clicking login button for room {room_id}")
                            await login_btn.click()
                            await asyncio.sleep(2)
                            
                            if await self._check_for_password_screen():
                                print(f"[{self.bot_name}] Password protected, skipping")
                                await self.page.goto(LOUNGE_URL, wait_until="domcontentloaded")
                                await asyncio.sleep(2)
                                return False
                            
                            page_content = await self.page.content()
                            if "接続が切れました" in page_content:
                                print(f"[{self.bot_name}] Connection error")
                                await self.page.goto(LOUNGE_URL, wait_until="domcontentloaded")
                                await asyncio.sleep(2)
                                return False
                            
                            print(f"[{self.bot_name}] Waiting for #talks...")
                            try:
                                await self.page.wait_for_selector("#talks", timeout=10000)
                                print(f"[{self.bot_name}] Successfully entered room {room_id}")
                                return True
                            except Exception as e:
                                print(f"[{self.bot_name}] Timeout waiting for #talks: {e}")
                                return False
                        else:
                            print(f"[{self.bot_name}] Login button not found or invisible")
                except Exception as e:
                    print(f"[{self.bot_name}] Error in _enter_room loop: {e}")
                    continue
            
            print(f"[{self.bot_name}] Target room {room_id} not found in list")
            return False
        except Exception as e:
            print(f"[{self.bot_name}] Error in _enter_room: {e}")
            return False
            
            for i, ul in enumerate(room_uls):
                try:
                    if not await ul.is_visible():
                        # if i < 3: print(f"[{self.bot_name}] Room {i} invisible")
                        continue
                    
                    if await ul.query_selector("li.full") or await ul.query_selector("div.full"):
                        if i < 3: print(f"[{self.bot_name}] Room {i} full")
                        continue
                    
                    if await ul.query_selector("i.fa-hand-paper"):
                        if i < 3: print(f"[{self.bot_name}] Room {i} knock required")
                        continue
                    
                    id_input = await ul.query_selector("input[name='id']")
                    if not id_input:
                        if i < 3: print(f"[{self.bot_name}] Room {i} no ID input")
                        continue
                    
                    room_id = await id_input.get_attribute("value")
                    
                    if room_id in self.blacklist or room_id in occupied_rooms:
                        if i < 3: print(f"[{self.bot_name}] Room {i} ({room_id}) blacklisted or occupied")
                        continue
                    
                    name_el = await ul.query_selector("li.name")
                    if name_el:
                        room_name = (await name_el.inner_text()).strip()
                        available_rooms.append({"id": room_id, "name": room_name})
                        print(f"[{self.bot_name}] Found candidate: {room_name} ({room_id})")
                except Exception as e:
                    print(f"[{self.bot_name}] Error checking room {i}: {e}")
                    continue
            
            for room in available_rooms:
                occupied_rooms = self.parent_bot.get_occupied_rooms()
                if room['id'] in occupied_rooms:
                    continue
                
                if await self._enter_room(room['id']):
                    self.room_id = room['id']
                    self.room_name = room['name']
                    safe_room_name = sanitize_filename(room['name'])
                    self.log_file = f"{LOG_DIR}/room_{room['id']}_{safe_room_name}.json"
                    self.last_activity = datetime.now()
                    print(f"[{self.bot_name}] Entered: {room['name']}")
                    return True
            
            return False
        except Exception as e:
            print(f"[{self.bot_name}] Error: {e}")
            return False
    
    async def start(self):
        retry_count = 0
        max_wait = 60
        
        try:
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            self.page.on("response", self._handle_response)
            
            print(f"[{self.bot_name}] Starting...")
            
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
                print(f"[{self.bot_name}] Icon selection error: {e}")
            
            await self.page.fill("input[name='name']", self.bot_name)
            await self.page.click("a.bb.cc")
            await asyncio.sleep(2)
            
            while self.running:
                try:
                    if not self.in_room:
                        if await self._find_and_enter_unmanned_room():
                            self.in_room = True
                            retry_count = 0
                        else:
                            wait_time = min(max_wait, 5 + retry_count * 5)
                            print(f"[{self.bot_name}] No rooms found, waiting {wait_time}s...")
                            
                            # Immediate debug capture on first failure
                            if retry_count == 0:
                                try:
                                    timestamp = datetime.now().strftime("%H%M%S")
                                    await self.page.screenshot(path=f"debug_no_rooms_{self.bot_name}_{timestamp}.png")
                                    content = await self.page.content()
                                    with open(f"debug_page_{self.bot_name}_{timestamp}.html", "w", encoding="utf-8") as f:
                                        f.write(content)
                                    print(f"[{self.bot_name}] Saved debug screenshot and HTML")
                                except Exception as e:
                                    print(f"[{self.bot_name}] Debug capture failed: {e}")
                                    
                            await asyncio.sleep(wait_time)
                            retry_count += 1
                            if retry_count > 5:
                                await self.page.reload()
                    else:
                        # Check if still in room
                        if "/room/" not in self.page.url:
                            print(f"[{self.bot_name}] Disconnected from room")
                            self.in_room = False
                            self.room_id = None
                            self.room_name = None
                            continue
                        
                        # Check for inactivity
                        if (datetime.now() - self.last_activity).total_seconds() > self.activity_timeout:
                            print(f"[{self.bot_name}] Inactive for too long, leaving...")
                            await self.page.click("input[name='logout']")
                            self.in_room = False
                            continue
                        
                        await asyncio.sleep(10)
                        
                except Exception as e:
                    print(f"[{self.bot_name}] Loop error: {e}")
                    await asyncio.sleep(5)
                    try:
                        await self.page.reload()
                    except:
                        pass
                        
        except Exception as e:
            print(f"[{self.bot_name}] Fatal error: {e}")
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
            
            print("[*] Getting room list...")
            
            # Create initial monitors
            tasks = []
            for i in range(MAX_MONITORS):
                bot_name = generate_random_name()
                bot_icon = random.choice(AVAILABLE_ICONS)
                
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
            
            print(f"[*] Started {len(tasks)} monitors")
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    bot = ParallelPatrolBot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\n[*] Stopping...")
