import requests
import re
import json
import time
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from html.parser import HTMLParser

# Configuration
BASE_URL = "https://drrrkari.com"
LOGIN_URL = f"{BASE_URL}/"
LOUNGE_URL = f"{BASE_URL}/lounge/"
ROOM_URL = f"{BASE_URL}/room/"
AJAX_URL = f"{BASE_URL}/ajax.php"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
LOG_DIR = "logs"

class RoomListParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ul_depth = 0
        self.room_ul_depth = -1
        self.current_room = {}
        self.rooms = []
        self.in_name = False
        self.in_member = False
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get("class", "")
        
        if tag == "ul":
            self.ul_depth += 1
            if "rooms" in class_name:
                self.room_ul_depth = self.ul_depth
                self.current_room = {"id": None, "name": "", "members": "", "full": False}
                if "display:none" in attrs_dict.get("style", ""):
                     self.current_room["hidden"] = True
                else:
                     self.current_room["hidden"] = False
                 
        if self.room_ul_depth != -1:
            if tag == "li" and "name" in class_name:
                self.in_name = True
            elif tag == "li" and "member" in class_name:
                self.in_member = True
            elif tag == "div" and "full" in class_name:
                self.current_room["full"] = True
            elif tag == "input" and attrs_dict.get("name") == "id":
                self.current_room["id"] = attrs_dict.get("value")

    def handle_endtag(self, tag):
        if tag == "ul":
            if self.ul_depth == self.room_ul_depth:
                # Closing the room ul
                if self.current_room.get("id") and not self.current_room.get("hidden"):
                    self.rooms.append(self.current_room)
                self.room_ul_depth = -1
            self.ul_depth -= 1
        
        if self.in_name: self.in_name = False
        if self.in_member: self.in_member = False

    def handle_data(self, data):
        if self.in_name:
            self.current_room["name"] += data.strip()
        if self.in_member:
            self.current_room["members"] += data.strip()

class PatrolBot:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Origin": BASE_URL
        })
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

    def login(self):
        print(f"[*] Accessing {LOGIN_URL}...")
        try:
            r = self.session.get(LOGIN_URL)
            r.raise_for_status()
            
            token_match = re.search(r'name="token" value="([a-f0-9]+)"', r.text)
            if not token_match:
                print("[-] Could not find CSRF token.")
                return False
            
            token = token_match.group(1)
            payload = {
                "language": "ja-JP",
                "icon": "kanra", 
                "name": "PatrolBot",
                "login": "login",
                "token": token
            }
            
            print(f"[*] Logging in...")
            r_login = self.session.post(LOGIN_URL, data=payload)
            r_login.raise_for_status()
            
            if "/lounge" in r_login.url or "lounge" in r_login.text:
                print("[+] Login successful.")
                return True
            else:
                print("[-] Login failed.")
                return False
        except Exception as e:
            print(f"[!] Login error: {e}")
            return False

    def get_rooms(self):
        print(f"[*] Fetching room list from {LOUNGE_URL}...")
        try:
            r = self.session.get(LOUNGE_URL)
            r.raise_for_status()
            
            parser = RoomListParser()
            parser.feed(r.text)
            
            print(f"[+] Found {len(parser.rooms)} visible rooms.")
            return parser.rooms
        except Exception as e:
            print(f"[!] Error fetching rooms: {e}")
            return []

    def visit_room(self, room):
        room_id = room['id']
        print(f"[*] Visiting {room['name']} (ID: {room_id}, Mem: {room['members']})...")
        
        if room.get("full"):
            print("    [!] Room is full. Skipping.")
            return

        try:
            # 1. Enter Room
            payload = {"login": "login", "id": room_id}
            self.session.headers.update({"Referer": LOUNGE_URL})
            
            r_enter = self.session.post(ROOM_URL, data=payload)
            r_enter.raise_for_status()
            
            # Check if we actually entered
            if "入室" in r_enter.text and "form" in r_enter.text:
                 print("    [!] Failed to enter room (redirected to lounge/login).")
                 return
            
            current_room_url = r_enter.url
            # 2. Fetch XML Logs via AJAX
            self.session.headers.update({"Referer": current_room_url})
            
            # print(f"    Requesting XML logs...")
            r_ajax = self.session.get(AJAX_URL, params={"fast": "1"})
            r_ajax.raise_for_status()
            
            # 3. Parse and Save
            self.save_logs(room, r_ajax.text)
            
            # 4. Logout / Leave Room
            # print(f"    Leaving room...")
            self.session.post(ROOM_URL, data={"logout": "logout"})
            
        except Exception as e:
            print(f"[!] Error visiting room {room_id}: {e}")

    def save_logs(self, room, xml_data):
        try:
            root = ET.fromstring(xml_data)
            
            data = {
                "room_id": room['id'],
                "room_name": room['name'],
                "timestamp": datetime.now().isoformat(),
                "users": [],
                "talks": []
            }
            
            users_node = root.find("users")
            if users_node is not None:
                for user in users_node:
                    data["users"].append({
                        "id": user.findtext("id"),
                        "name": user.findtext("name"),
                        "icon": user.findtext("icon")
                    })
            
            talks_node = root.find("talks")
            if talks_node is not None:
                for talk in talks_node:
                    data["talks"].append({
                        "id": talk.findtext("id"),
                        "uid": talk.findtext("uid"),
                        "name": talk.findtext("name"),
                        "message": talk.findtext("message"),
                        "time": talk.findtext("time"),
                        "icon": talk.findtext("icon")
                    })
            
            filename = f"{LOG_DIR}/room_{room['id']}_{int(time.time())}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"    [+] Saved {len(data['talks'])} messages.")
            
        except ET.ParseError:
            print(f"    [!] Failed to parse XML.")
            # print(f"    [DEBUG] Response: {xml_data[:100]}")

    def run(self):
        if self.login():
            rooms = self.get_rooms()
            # Limit to first 5 for testing
            for i, room in enumerate(rooms[:5]):
                print(f"--- Room {i+1}/{len(rooms)} ---")
                self.visit_room(room)
                time.sleep(2)

if __name__ == "__main__":
    bot = PatrolBot()
    bot.run()
