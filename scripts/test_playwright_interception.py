import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# Quick test to verify ajax.php interception
def test_interception():
    captured = []
    
    def handle_response(response):
        if "ajax.php" in response.url:
            try:
                data = response.json()
                captured.append(data)
                print(f"[*] Captured ajax.php: {response.url}")
                print(f"    Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            except:
                print(f"[!] Failed to parse: {response.url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.on("response", handle_response)
        
        # Login
        page.goto("https://drrrkari.com/")
        time.sleep(2)
        page.fill("input[name='name']", "TestBot")
        page.click("a.bb.cc")
        page.wait_for_url("**/lounge/**", timeout=10000)
        print("[+] Logged in")
        
        # Enter first available room
        rooms = page.query_selector_all("ul.rooms.clearfix")
        for ul in rooms:
            if ul.is_visible() and not ul.query_selector("li.full"):
                btn = ul.query_selector("button[name='login'], input[type='submit'][name='login']")
                if btn:
                    btn.click()
                    break
        
        # Wait for room and ajax responses
        page.wait_for_selector("#talks", timeout=10000)
        print("[+] Entered room, waiting for ajax.php...")
        time.sleep(10)
        
        print(f"\n[*] Captured {len(captured)} responses")
        if captured:
            print("\nSample data structure:")
            print(json.dumps(captured[0], indent=2, ensure_ascii=False)[:500])
        
        browser.close()

if __name__ == "__main__":
    test_interception()
