# API Reference

## Overview

デュラチャログシステムのREST API仕様

Base URL: `http://localhost:5000`

---

## Endpoints

### Rooms

#### GET /api/rooms

全部屋のリストを取得

**Response:**
```json
[
  {
    "id": "493eae55a1ce4f103888e4ee1a12bf46",
    "name": "ざつだん",
    "message_count": 102,
    "last_updated": "2025-11-23T12:00:00",
    "filename": "room_493eae55a1ce4f103888e4ee1a12bf46_ざつだん.json"
  }
]
```

#### GET /api/room/\<room_id\>/messages

特定部屋の全メッセージを取得

**Parameters:**
- `room_id` (string): 部屋ID

**Response:**
```json
[
  {
    "id": "084430809e6a04638844b083158d7753",
    "uid": "e514a86cd4168dd9f9531d1990f3e24a",
    "name": "けんたろうEMI",
    "message": "おはよ🏍️",
    "time": 1763863131,
    "icon": "nyan",
    "encip": "",
    "trip": "",
    "captured_at": "2025-11-23T11:00:15.163351"
  }
]
```

---

### User Analysis

#### GET /api/user/\<uid\>/profile

ユーザープロファイルを取得

**Parameters:**
- `uid` (string): ユーザーID (MD5ハッシュ)

**Response:**
```json
{
  "uid": "2ca2aeba8a28a68120ff9d234d1ff0ae",
  "usernames": ["カメラ男"],
  "rooms": [
    {
      "id": "493eae55a1ce4f103888e4ee1a12bf46",
      "name": "ざつだん"
    }
  ],
  "message_count": 43,
  "first_seen": 1763864733,
  "last_seen": 1763867800
}
```

#### GET /api/user/\<uid\>/messages

特定ユーザーの全メッセージを取得

**Parameters:**
- `uid` (string): ユーザーID

**Response:**
```json
[
  {
    "id": "message_id",
    "uid": "user_id",
    "name": "ハンドルネーム",
    "message": "メッセージ内容",
    "time": 1763863131,
    "icon": "nyan",
    "encip": "",
    "trip": "",
    "captured_at": "2025-11-23T11:00:15",
    "room_id": "room_id",
    "room_name": "部屋名"
  }
]
```

**Note:** メッセージは時系列順（新→古）でソートされています

---

## Data Types

### Message

| Field | Type | Description |
|-------|------|-------------|
| id | string | メッセージの一意ID |
| uid | string | ユーザーID (MD5ハッシュ) |
| name | string | ハンドルネーム |
| message | string | メッセージ内容 |
| time | integer | UNIXタイムスタンプ |
| icon | string | アイコン名 |
| encip | string | 暗号化IP（通常空） |
| trip | string | トリップ |
| captured_at | string | キャプチャ日時（ISO 8601） |

### Room

| Field | Type | Description |
|-------|------|-------------|
| id | string | 部屋ID |
| name | string | 部屋名 |
| message_count | integer | メッセージ数 |
| last_updated | string | 最終更新日時 |
| filename | string | JSONファイル名 |

### User Profile

| Field | Type | Description |
|-------|------|-------------|
| uid | string | ユーザーID |
| usernames | array | 使用したハンドルネーム一覧 |
| rooms | array | 訪問した部屋一覧 |
| message_count | integer | 総メッセージ数 |
| first_seen | integer | 初回観測時刻 |
| last_seen | integer | 最終観測時刻 |

---

## Error Handling

APIがエラーを返す場合、通常は空の配列`[]`を返します。

一部のエンドポイントでは500エラーの場合：
```json
{
  "error": "error message"
}
```

---

## Examples

### cURL

```bash
# 部屋リスト取得
curl http://localhost:5000/api/rooms

# 特定部屋のメッセージ取得
curl http://localhost:5000/api/room/493eae55a1ce4f103888e4ee1a12bf46/messages

# ユーザープロファイル取得
curl http://localhost:5000/api/user/2ca2aeba8a28a68120ff9d234d1ff0ae/profile

# ユーザーメッセージ取得
curl http://localhost:5000/api/user/2ca2aeba8a28a68120ff9d234d1ff0ae/messages
```

### JavaScript (Fetch API)

```javascript
// 部屋リスト取得
const rooms = await fetch('/api/rooms').then(r => r.json());

// ユーザープロファイル取得
const uid = '2ca2aeba8a28a68120ff9d234d1ff0ae';
const profile = await fetch(`/api/user/${uid}/profile`).then(r => r.json());
```

---

## Rate Limiting

現在、レート制限は実装されていません。

---

## Websocket Events

Socket.IOを使用したリアルタイム更新

### Events

#### connect
クライアント接続時

#### log_update
ログが更新された時（5秒ごと）

```javascript
socket.on('log_update', () => {
    // 部屋リストを再読み込み
    loadRooms();
});
```
