import asyncio
import json
import os
import random
import string
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
BASE_URL = "https://drrrkari.com"
LOGIN_URL = f"{BASE_URL}/"
LOUNGE_URL = f"{BASE_URL}/lounge/"
STAY_DURATION = 300  # 5 minutes per room
GOOGLE_DRIVE = r"G:\マイドライブ\開発関連"

def sanitize_filename(name):
    """Sanitize room name for file naming"""
    if not name:
        return "unknown"
    safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
    return safe[:50].strip()

def get_drive_log_dir():
    """Get today's log directory in Google Drive"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        log_dir = os.path.join(GOOGLE_DRIVE, today, "log")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    except Exception as e:
        print(f"Error creating log directory: {e}")
        return None

class SimplePatrolBot:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.bot_name = self.generate_bot_name()
        self.current_room_id = None
        self.current_room_name = None
        self.current_log_file = None
        self.known_message_ids = set()
        
    def generate_bot_name(self):
        """Generate a random bot name"""
        names = ["さくら", "ゆい", "あおい", "りん", "そら", "はな", "もも", "なな"]
        suffix = ''.join(random.choices(string.digits, k=4))
        return f"{random.choice(names)}{suffix}"
    
    async def _handle_response(self, response):
        """Handle AJAX responses to extract messages"""
        if "ajax.php" not in response.url:
            return
            
        try:
            text = await response.text()
            data = json.loads(text)
            
            if not isinstance(data, dict):
                return
                
            talks = data.get("talks", [])
            if not talks:
                return
            
            # Save new messages
            await self._save_messages(talks)
            
        except Exception as e:
            print(f"[{self.bot_name}] Response handler error: {e}")
    
    async def _save_messages(self, talks):
        """Save messages incrementally to Google Drive"""
        if not self.current_log_file:
            return
            
        try:
            drive_dir = get_drive_log_dir()
            if not drive_dir:
                return
            
            safe_room_name = sanitize_filename(self.current_room_name)
            log_file = os.path.join(drive_dir, f"room_{self.current_room_id}_{safe_room_name}.json")
            
            # Load existing messages
            existing_messages = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        file_data = json.load(f)
                        if isinstance(file_data, dict) and 'messages' in file_data:
                            existing_messages = file_data['messages']
                            for msg in existing_messages:
                                if 'id' in msg:
                                    self.known_message_ids.add(msg['id'])
                except Exception as e:
                    print(f"[{self.bot_name}] Error loading existing file: {e}")
            
            # Filter and add new messages
            new_messages = []
            for talk in talks:
                msg_id = talk.get('id', '')
                if msg_id and msg_id not in self.known_message_ids:
                    # Skip system messages
                    if talk.get('type') == 'me' or 'join' in talk.get('type', '') or 'leave' in talk.get('type', ''):
                        continue
                    
                    new_messages.append(talk)
                    self.known_message_ids.add(msg_id)
            
            if not new_messages:
                return
            
            # Append new messages
            all_messages = existing_messages + new_messages
            
            # Save to file
            save_data = {
                'room_id': self.current_room_id,
                'room_name': self.current_room_name,
                'last_updated': datetime.now().isoformat(),
                'messages': all_messages
            }
            
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            print(f"[{self.bot_name}] Saved {len(new_messages)} new messages to {os.path.basename(log_file)}")
            
        except Exception as e:
            print(f"[{self.bot_name}] Save error: {e}")
    
    async def login(self):
        """Log in to the site"""
        print(f"[{self.bot_name}] Logging in...")
        
        await self.page.goto(LOGIN_URL)
        await asyncio.sleep(2)
        
        # Fill name
        await self.page.fill("input[name='name']", self.bot_name)
        
        # Click login button
        await self.page.click("a.bb.cc")
        await asyncio.sleep(3)
        
        if "/lounge/" in self.page.url:
            print(f"[{self.bot_name}] Login successful")
            return True
        else:
            print(f"[{self.bot_name}] Login failed")
            return False
    
    async def get_available_rooms(self):
        """Get list of available rooms from lounge"""
        try:
            await self.page.goto(LOUNGE_URL, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            rooms = []
            room_elements = await self.page.query_selector_all("ul.rooms.clearfix")
            
            for ul in room_elements:
                try:
                    # Check if room is full or locked
                    if await ul.query_selector("li.full") or await ul.query_selector("div.full"):
                        continue
                    if await ul.query_selector("i.fa-hand-paper"):
                        continue
                    
                    # Get room ID and name
                    id_input = await ul.query_selector("input[name='id']")
                    if not id_input:
                        continue
                    
                    room_id = await id_input.get_attribute("value")
                    name_el = await ul.query_selector("li.name")
                    if name_el:
                        room_name = (await name_el.inner_text()).strip()
                        rooms.append({"id": room_id, "name": room_name})
                except:
                    continue
            
            print(f"[{self.bot_name}] Found {len(rooms)} available rooms")
            return rooms
            
        except Exception as e:
            print(f"[{self.bot_name}] Error getting rooms: {e}")
            return []
    
    async def enter_room(self, room_id, room_name):
        """Enter a specific room"""
        try:
            print(f"[{self.bot_name}] Entering room: {room_name} ({room_id})")
            
            # Go to lounge first
            await self.page.goto(LOUNGE_URL, wait_until="domcontentloaded")
            await asyncio.sleep(1)
            
            # Find and click the login button for this room
            room_elements = await self.page.query_selector_all("ul.rooms.clearfix")
            for ul in room_elements:
                id_input = await ul.query_selector("input[name='id']")
                if id_input:
                    found_id = await id_input.get_attribute("value")
                    if found_id == room_id:
                        login_btn = await ul.query_selector("button[name='login'], input[type='submit'][name='login']")
                        if login_btn:
                            await login_btn.click()
                            await asyncio.sleep(3)
                            
                            # Check if we're in the room
                            if "/room/" in self.page.url:
                                self.current_room_id = room_id
                                self.current_room_name = room_name
                                self.known_message_ids.clear()  # Reset for new room
                                print(f"[{self.bot_name}] Successfully entered room")
                                return True
            
            print(f"[{self.bot_name}] Failed to enter room")
            return False
            
        except Exception as e:
            print(f"[{self.bot_name}] Enter room error: {e}")
            return False
    
    async def leave_room(self):
        """Leave current room"""
        try:
            print(f"[{self.bot_name}] Leaving room: {self.current_room_name}")
            await self.page.goto(LOUNGE_URL, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            self.current_room_id = None
            self.current_room_name = None
            self.known_message_ids.clear()
        except Exception as e:
            print(f"[{self.bot_name}] Leave room error: {e}")
    
    async def patrol(self):
        """Main patrol loop - visit rooms sequentially"""
        try:
            async with async_playwright() as p:
                self.browser = await p.chromium.launch(headless=True)
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
                
                # Set up response handler
                self.page.on("response", self._handle_response)
                
                # Login
                if not await self.login():
                    print(f"[{self.bot_name}] Login failed, exiting")
                    return
                
                # Main patrol loop
                while True:
                    # Get available rooms
                    rooms = await self.get_available_rooms()
                    if not rooms:
                        print(f"[{self.bot_name}] No rooms available, waiting 60s...")
                        await asyncio.sleep(60)
                        continue
                    
                    # Visit each room
                    for room in rooms:
                        # Enter room
                        if await self.enter_room(room['id'], room['name']):
                            # Stay and collect messages
                            print(f"[{self.bot_name}] Staying for {STAY_DURATION}s...")
                            await asyncio.sleep(STAY_DURATION)
                            
                            # Leave room
                            await self.leave_room()
                            
                            # Short break between rooms
                            await asyncio.sleep(10)
                        else:
                            print(f"[{self.bot_name}] Skipping room {room['name']}")
                    
                    # After visiting all rooms, take a break before next cycle
                    print(f"[{self.bot_name}] Completed one cycle, taking a 5 minute break...")
                    await asyncio.sleep(300)
                    
        except Exception as e:
            print(f"[{self.bot_name}] Patrol error: {e}")
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    print("=" * 60)
    print("🤖 シンプル巡回ボット起動")
    print(f"📂 ログ保存先: {GOOGLE_DRIVE}")
    print(f"⏱️  部屋滞在時間: {STAY_DURATION}秒")
    print("=" * 60)
    
    bot = SimplePatrolBot()
    await bot.patrol()

if __name__ == "__main__":
    asyncio.run(main())
