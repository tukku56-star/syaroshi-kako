import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configuration
BASE_URL = "https://drrrkari.com"
LOGIN_URL = f"{BASE_URL}/"
LOUNGE_URL = f"{BASE_URL}/lounge/"
LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class PlaywrightPatrolBot:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.captured_json = None
        
    def start(self):
        """Start Playwright browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        # Setup response interception
        self.page.on("response", self._handle_response)
        
    def _handle_response(self, response):
        """Intercept and capture ajax.php JSON responses"""
        if "ajax.php" in response.url:
            try:
                # Get JSON response
                json_data = response.json()
                self.captured_json = json_data
                print(f"    [*] Captured ajax.php JSON")
            except Exception as e:
                print(f"    [!] Failed to capture ajax.php response: {e}")
                
    def login(self, name="PatrolBot"):
        """Login to drrrkari"""
        print("[*] Accessing Login Page...")
        self.page.goto(LOGIN_URL)
        time.sleep(2)
        
        try:
            # Fill name
            self.page.fill("input[name='name']", name)
            
            # Click login button
            self.page.click("a.bb.cc")
            
            # Wait for lounge
            self.page.wait_for_url("**/lounge/**", timeout=10000)
            print("[+] Login Successful")
            return True
        except Exception as e:
            print(f"[-] Login Failed: {e}")
            return False
            
    def get_room_list(self):
        """Get list of available rooms from lounge"""
        print("[*] Scanning for rooms...")
        
        # Wait for dynamic rooms to load
        time.sleep(3)
        
        rooms = []
        room_uls = self.page.query_selector_all("ul.rooms.clearfix")
        
        for ul in room_uls:
            try:
                # Check if visible
                if not ul.is_visible():
                    continue
                    
                # Check if full
                if ul.query_selector("li.full"):
                    continue
                    
                # Get room name
                name_el = ul.query_selector("li.name")
                if not name_el:
                    continue
                room_name = name_el.inner_text().strip()
                
                # Get room ID
                id_input = ul.query_selector("input[name='id']")
                if not id_input:
                    continue
                room_id = id_input.get_attribute("value")
                
                # Get login button
                login_btn = ul.query_selector("button[name='login'], input[type='submit'][name='login']")
                if not login_btn:
                    continue
                    
                rooms.append({
                    "id": room_id,
                    "name": room_name,
                    "element": ul
                })
            except Exception as e:
                continue
                
        print(f"[+] Found {len(rooms)} accessible rooms")
        return rooms
        
    def enter_room(self, room_info):
        """Enter a room by clicking its login button"""
        print(f"--- Visiting: {room_info['name']} (ID: {room_info['id']}) ---")
        
        # Clear previous capture
        self.captured_json = None
        
        try:
            # Click login button
            login_btn = room_info['element'].query_selector("button[name='login'], input[type='submit'][name='login']")
            login_btn.click()
            
            # Wait for room to load (look for chat interface)
            self.page.wait_for_selector("#talks", timeout=10000)
            print("    [+] Entered room successfully")
            
            # Wait for ajax.php JSON response to be captured
            max_wait = 10
            for i in range(max_wait):
                if self.captured_json:
                    break
                time.sleep(1)
            
            if not self.captured_json:
                print("    [!] Warning: No ajax.php response captured yet, waiting a bit more...")
                time.sleep(3)
            
            return True
        except Exception as e:
            print(f"    [!] Failed to enter room: {e}")
            return False
            
    def leave_room(self):
        """Leave current room and return to lounge"""
        try:
            # Try clicking logout button
            logout_btn = self.page.query_selector("button[name='logout'], input[type='submit'][name='logout']")
            if logout_btn:
                logout_btn.click()
            else:
                # Fallback: navigate directly to lounge
                self.page.goto(LOUNGE_URL)
                
            # Wait for lounge
            self.page.wait_for_url("**/lounge/**", timeout=5000)
            print("    [+] Left room")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"    [!] Failed to leave room gracefully: {e}")
            # Force navigation
            self.page.goto(LOUNGE_URL)
            time.sleep(2)
            return False
            
    def save_captured_data(self, room_info):
        """Save captured ajax.php JSON to file"""
        if not self.captured_json:
            print("    [!] No ajax.php JSON captured")
            return None, 0
        
        # Determine filename
        room_id = room_info['id']
        fname = f"{LOG_DIR}/room_{room_id}.json"
        
        # Load existing data if present
        existing_data = []
        if os.path.exists(fname):
            try:
                with open(fname, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except:
                existing_data = []
                
        # Append new data
        existing_data.append(self.captured_json)
        
        # Save
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
        talks_count = len(self.captured_json.get('talks', {}))
        print(f"    [+] Saved to {fname} ({talks_count} talks)")
        return fname, 1
        
    def run(self):
        """Main patrol loop"""
        if not self.login():
            return
            
        try:
            while True:
                print("\n[*] Starting patrol cycle...")
                
                # Ensure we're on lounge
                if "/lounge" not in self.page.url:
                    self.page.goto(LOUNGE_URL)
                    time.sleep(2)
                    
                # Get room list
                rooms = self.get_room_list()
                
                if not rooms:
                    print("    No rooms found. Waiting...")
                    time.sleep(5)
                    continue
                    
                # Visit each room
                for i in range(len(rooms)):
                    print(f"\n[{i+1}/{len(rooms)}]")
                    
                    # Re-query rooms to avoid stale element references
                    current_rooms = self.get_room_list()
                    if i >= len(current_rooms):
                        print("    [!] Room list changed, skipping")
                        continue
                    
                    room = current_rooms[i]
                    
                    if self.enter_room(room):
                        # Leave room first to ensure all ajax responses are captured
                        self.leave_room()
                        # Then save the captured data
                        self.save_captured_data(room)
                    else:
                        # Failed to enter, go back to lounge
                        self.page.goto(LOUNGE_URL)
                        time.sleep(2)
                        
                print("\n[*] Completed one cycle. Restarting...")
                time.sleep(3)
                
        except KeyboardInterrupt:
            print("\n[!] Stopping...")
        finally:
            self.close()
            
    def close(self):
        """Close browser and cleanup"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

if __name__ == "__main__":
    bot = PlaywrightPatrolBot()
    bot.start()
    bot.run()
