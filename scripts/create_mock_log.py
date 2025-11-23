import json
import os
from datetime import datetime
import random

# Google Drive path
GOOGLE_DRIVE = r"G:\マイドライブ\開発関連"
today = datetime.now().strftime("%Y-%m-%d")
log_dir = os.path.join(GOOGLE_DRIVE, today, "logs")

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Mock room data
room_id = "mock_12345"
room_name = "開発テスト部屋"
safe_room_name = "開発テスト部屋"
filename = f"room_{room_id}_{safe_room_name}.json"
filepath = os.path.join(log_dir, filename)

# Mock messages
messages = [
    {
        "id": "msg_1",
        "uid": "user_001",
        "name": "田中",
        "message": "こんにちは！これはテストメッセージです。",
        "time": 1716360000,
        "icon": "boy",
        "encip": "192.168.x.x",
        "trip": "Trip123",
        "captured_at": datetime.now().isoformat()
    },
    {
        "id": "msg_2",
        "uid": "user_002",
        "name": "佐藤",
        "message": "お疲れ様です。ビューアーの動作確認中ですね。",
        "time": 1716360060,
        "icon": "girl",
        "encip": "10.0.x.x",
        "trip": "Trip456",
        "captured_at": datetime.now().isoformat()
    },
    {
        "id": "msg_3",
        "uid": "user_003",
        "name": "名無し",
        "message": "長いメッセージのテスト。\n改行も含まれています。\n正しく表示されますか？",
        "time": 1716360120,
        "icon": "neko",
        "encip": "172.16.x.x",
        "trip": "",
        "captured_at": datetime.now().isoformat()
    },
    {
        "id": "msg_4",
        "uid": "user_001",
        "name": "田中",
        "message": "連投テスト1",
        "time": 1716360180,
        "icon": "boy",
        "encip": "192.168.x.x",
        "trip": "Trip123",
        "captured_at": datetime.now().isoformat()
    },
    {
        "id": "msg_5",
        "uid": "user_001",
        "name": "田中",
        "message": "連投テスト2",
        "time": 1716360185,
        "icon": "boy",
        "encip": "192.168.x.x",
        "trip": "Trip123",
        "captured_at": datetime.now().isoformat()
    }
]

data = {
    "room_id": room_id,
    "room_name": room_name,
    "last_updated": datetime.now().isoformat(),
    "total_messages": len(messages),
    "messages": messages
}

print(f"Creating mock log file at: {filepath}")
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Done!")
