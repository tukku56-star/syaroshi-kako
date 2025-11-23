import os
import json
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
BASE_URL = "https://drrrkari.com"
LOGIN_URL = f"{BASE_URL}/"
LOUNGE_URL = f"{BASE_URL}/lounge/"
LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class SeleniumPatrolBot:
    def __init__(self):
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") # Run visible for now to debug
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1280,800")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def login(self):
        print("[*] Accessing Login Page...")
        self.driver.get(LOGIN_URL)
        
        try:
            # Wait for name input
            name_input = self.wait.until(EC.presence_of_element_located((By.NAME, "name")))
            name_input.clear()
            name_input.send_keys("PatrolBot")
            
            # Select icon (optional, default is usually selected)
            # icon = self.driver.find_element(By.CSS_SELECTOR, "img[alt='kanra']")
            # icon.click()
            
            # Submit
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "a.bb.cc") # The "Chat Start" button
            submit_btn.click()
            
            # Wait for Lounge
            self.wait.until(EC.url_contains("/lounge"))
            print("[+] Login Successful")
            return True
        except Exception as e:
            print(f"[-] Login Failed: {e}")
            return False

    def get_room_buttons(self):
        # Wait for dynamic rooms to load. 
        end_time = time.time() + 10
        while time.time() < end_time:
            room_uls = self.driver.find_elements(By.CSS_SELECTOR, "ul.rooms")
            visible_count = sum(1 for ul in room_uls if ul.is_displayed())
            if visible_count > 2:
                break
            time.sleep(0.5)
            
        rooms = []
        room_uls = self.driver.find_elements(By.CSS_SELECTOR, "ul.rooms")
        
        for ul in room_uls:
            if not ul.is_displayed():
                continue
                
            try:
                # Check if full
                if ul.find_elements(By.CLASS_NAME, "full"):
                    continue
                    
                # Get Room Name
                name_el = ul.find_element(By.CLASS_NAME, "name")
                room_name = name_el.text
                
                # Get Room ID (hidden input)
                # Structure: <li> <form> <input name="id" value="..."> ... </form> </li>
                # The button is inside the form.
                # We can find the input relative to the ul or the form.
                room_id = "unknown"
                try:
                    id_input = ul.find_element(By.CSS_SELECTOR, "input[name='id']")
                    room_id = id_input.get_attribute("value")
                except:
                    pass
                
                # Get Button
                btn = ul.find_element(By.NAME, "login")
                rooms.append({
                    "id": room_id,
                    "name": room_name,
                    "element": btn
                })
            except NoSuchElementException:
                continue
                
        return rooms

    def scrape_room(self, room_info):
        data = {
            "room_id": room_info['id'],
            "room_name": room_info['name'],
            "last_updated": datetime.now().isoformat(),
            "users": [],
            "talks": []
        }
        
        try:
            # Wait for chat to load
            self.wait.until(EC.presence_of_element_located((By.ID, "talks")))
            
            # Scrape Users
            user_list = self.driver.find_element(By.ID, "user_list")
            users = user_list.find_elements(By.TAG_NAME, "li")
            for u in users:
                try:
                    uid = u.get_attribute("id")
                    uname = u.find_element(By.CLASS_NAME, "name").text
                    data["users"].append({"id": uid, "name": uname})
                except:
                    pass

            # Scrape Talks
            talks_div = self.driver.find_element(By.ID, "talks")
            talks = talks_div.find_elements(By.CSS_SELECTOR, "div.talk")
            
            for t in talks:
                try:
                    tid = t.get_attribute("id")
                    classes = t.get_attribute("class")
                    
                    msg_body = ""
                    bodies = t.find_elements(By.CLASS_NAME, "body")
                    if bodies:
                        msg_body = bodies[0].text
                        
                    sender = "System"
                    if "system" not in classes:
                        names = t.find_elements(By.CLASS_NAME, "name")
                        if names:
                            sender = names[0].text
                            
                    data["talks"].append({
                        "id": tid,
                        "type": classes,
                        "sender": sender,
                        "message": msg_body,
                        "scraped_at": datetime.now().isoformat()
                    })
                except:
                    pass
            
            return data
            
        except Exception as e:
            print(f"    [!] Error scraping room: {e}")
            return None

    def save_or_update_log(self, room_info, new_data):
        # Filename based on Room ID if available, else Name
        rid = room_info['id']
        rname = room_info['name']
        
        safe_name = "".join([c for c in rname if c.isalnum()])
        if rid and rid != "unknown":
            fname = f"{LOG_DIR}/room_{rid}.json"
        else:
            fname = f"{LOG_DIR}/{safe_name}.json"
            
        existing_data = {}
        if os.path.exists(fname):
            try:
                with open(fname, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except:
                pass
        
        # Merge Data
        # 1. Update Metadata
        existing_data["room_id"] = rid
        existing_data["room_name"] = rname
        existing_data["last_updated"] = new_data["last_updated"]
        existing_data["users"] = new_data["users"] # Overwrite users with current state
        
        # 2. Merge Talks (deduplicate by ID)
        if "talks" not in existing_data:
            existing_data["talks"] = []
            
        existing_ids = {t["id"] for t in existing_data["talks"] if "id" in t}
        
        new_count = 0
        for talk in new_data["talks"]:
            if talk["id"] not in existing_ids:
                existing_data["talks"].append(talk)
                existing_ids.add(talk["id"])
                new_count += 1
                
        # Save
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
        return new_count, fname

    def run(self):
        if not self.login():
            return

        while True:
            print("\n[*] Scanning for rooms...")
            if "/lounge" not in self.driver.current_url:
                self.driver.get(LOUNGE_URL)
            
            rooms = self.get_room_buttons()
            print(f"[+] Found {len(rooms)} accessible rooms.")
            
            if not rooms:
                print("    No rooms found. Waiting...")
                time.sleep(5)
                continue
                
            count = len(rooms)
            for i in range(count):
                try:
                    current_rooms = self.get_room_buttons()
                    if i >= len(current_rooms):
                        break
                        
                    target = current_rooms[i]
                    r_name = target['name']
                    
                    print(f"--- Visiting {i+1}/{count}: {r_name} (ID: {target['id']}) ---")
                    
                    target['element'].click()
                    
                    try:
                        self.wait.until(EC.presence_of_element_located((By.ID, "talks")))
                    except TimeoutException:
                        print("    [!] Timed out entering room. Going back.")
                        self.driver.get(LOUNGE_URL)
                        continue
                        
                    data = self.scrape_room(target)
                    if data:
                        added_count, fname = self.save_or_update_log(target, data)
                        print(f"    [+] Updated {fname} (+{added_count} new messages).")
                    
                    try:
                        logout_btn = self.driver.find_element(By.NAME, "logout")
                        logout_btn.click()
                    except:
                        self.driver.get(LOUNGE_URL)
                        
                    self.wait.until(EC.url_contains("/lounge"))
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"    [!] Error in loop: {e}")
                    self.driver.get(LOUNGE_URL)
            
            print("[*] Completed one cycle. Restarting...")
            time.sleep(3)

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    bot = SeleniumPatrolBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n[!] Stopping...")
    finally:
        bot.close()
