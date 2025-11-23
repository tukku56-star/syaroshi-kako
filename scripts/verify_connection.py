import requests
import sys
import re

# Configuration
BASE_URL = "https://drrrkari.com"
LOGIN_URL = f"{BASE_URL}/"
LOUNGE_URL = f"{BASE_URL}/lounge/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def verify_login():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    print(f"[*] Accessing {LOGIN_URL}...")
    try:
        # 1. Get the login page to establish session/cookies and get token
        r = session.get(LOGIN_URL)
        r.raise_for_status()
        
        # Extract token
        token_match = re.search(r'name="token" value="([a-f0-9]+)"', r.text)
        if not token_match:
            print("[-] Could not find CSRF token in login page.")
            return
        
        token = token_match.group(1)
        print(f"[*] Found CSRF token: {token}")
        
        payload = {
            "language": "ja-JP",
            "icon": "kanra", 
            "name": "AntigravityBot",
            "login": "login",
            "token": token
        }

        print(f"[*] Attempting login with payload: {payload}")
        r_login = session.post(LOGIN_URL, data=payload)
        r_login.raise_for_status()

        # Check if we are redirected to lounge
        if "/lounge" in r_login.url or "lounge" in r_login.text:
            print("[+] Login successful! Redirected to Lounge.")
        else:
            print("[-] Login might have failed. Current URL:", r_login.url)
            # If failed, maybe print title
            title_match = re.search(r'<title>(.*?)</title>', r_login.text)
            if title_match:
                print("Page Title:", title_match.group(1))

        # 2. Fetch Lounge to see room list
        print(f"[*] Fetching {LOUNGE_URL}...")
        r_lounge = session.get(LOUNGE_URL)
        r_lounge.raise_for_status()

        print("[*] Lounge HTML Snippet (saving full to 'lounge_dump.html'):")
        print(r_lounge.text[:1000]) 
        
        with open("lounge_dump.html", "w", encoding="utf-8") as f:
            f.write(r_lounge.text)
        print("[+] Saved lounge HTML to 'lounge_dump.html'")

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    verify_login()
