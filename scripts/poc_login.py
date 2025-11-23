import requests
from bs4 import BeautifulSoup
import re

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# 1. Login
print("Logging in...")
# First, get the main page to find the token
r = s.get('https://drrrkari.com/')
soup = BeautifulSoup(r.text, 'html.parser')
token_input = soup.select_one('input[name="token"]')
token = token_input['value'] if token_input else ''
print(f"Found token: {token}")

login_data = {
    'name': 'PoCBot',
    'login': 'login',
    'icon': 'girl',
    'language': 'ja-JP',
    'token': token
}
r = s.post('https://drrrkari.com/', data=login_data)
print(f"Login Status: {r.status_code}")

# 2. Get Lounge
print("Accessing Lounge...")
r = s.get('https://drrrkari.com/lounge/')
print(f"Lounge Status: {r.status_code}")

with open("lounge_dump.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print("Saved lounge_dump.html")

soup = BeautifulSoup(r.text, 'html.parser')
rooms = soup.select('ul.rooms')
print(f"Found {len(rooms)} rooms")

target_room = None
for room in rooms:
    name = room.select_one('li.name').text.strip()
    room_id_input = room.select_one('input[name="id"]')
    if room_id_input:
        room_id = room_id_input['value']
        print(f"Room: {name} ({room_id})")
        
        # Check if full or locked
        if 'full' in room.get('class', []) or room.select_one('li.full'):
            print(" - Full")
            continue
        if room.select_one('i.fa-hand-paper'):
            print(" - Locked")
            continue
            
        target_room = room_id
        break

if target_room:
    print(f"Attempting to enter room {target_room}...")
    # 3. Enter Room
    # Based on HTML: <form action="/room/" method="post"> <input name="id" ...> <input name="login" value="login">
    enter_data = {
        'id': target_room,
        'login': 'login'
    }
    r = s.post('https://drrrkari.com/room/', data=enter_data)
    print(f"Entry Status: {r.status_code}")
    print(f"URL: {r.url}")
    
    if "/room/" in r.url:
        print("Successfully entered room!")
        
        with open("room_dump.html", "w", encoding="utf-8") as f:
            f.write(r.text)
        print("Saved room_dump.html")

        # Now try to find the ajax endpoint in the HTML
        if "ajax.php" in r.text:
            print("Found 'ajax.php' in response text!")
        
        # Try to poll messages
        # Usually it sends 'id' (room id) and maybe 'p' (polling?)
        print("Attempting to poll ajax.php...")
        ajax_data = {
            'id': target_room,
            'message': '', # Empty message for polling?
            'name': 'PoCBot'
        }
        try:
            r = s.post('https://drrrkari.com/ajax.php', data=ajax_data)
            print(f"Ajax Status: {r.status_code}")
            print(f"Ajax Response: {r.text[:500]}")
        except Exception as e:
            print(f"Ajax failed: {e}")
else:
    print("No suitable room found.")
