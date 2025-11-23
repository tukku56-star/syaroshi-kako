# デュラチャログシステム - 再現用プロンプト

## 使用方法
このプロンプトを新しい会話で使用することで、現在のシステムとほぼ同じ機能を持つシステムを再構築できます。

---

# プロンプト開始

```
# デュラチャ（drrrkari.com）チャットログ収集・分析システムの構築

## プロジェクト概要

### 目的
匿名チャットサイト「drrrkari.com（デュラチャ）」のチャットログを自動収集し、リアルタイムでビューアー表示、ユーザー行動分析を行うシステムを構築してください。

### システム構成
1. **並列ログ収集BOT** (`parallel_patrol_bot.py`)
   - Playwright使用
   - 30並列モニター
   - ローカルストレージ保存

2. **リアルタイムログビューアー** (`log_viewer_clean.py`)
   - Flask + Flask-SocketIO
   - RESTful API
   - リアルタイム更新

3. **ユーザー分析機能** (`user_analysis.html`)
   - UID検索
   - プロファイル表示
   - メッセージ履歴

### 作業ディレクトリ
`c:/Users/admin/.gemini/antigravity/scratch`

---

## フェーズ1: 技術仕様の確認

### デュラチャの技術仕様

**認証なしでアクセス可能**: https://drrrkari.com

**ログイン**:
- URL: https://drrrkari.com/login.php
- アイコン選択（24種類）
- 名前入力（最大34文字）

**ラウンジ（部屋一覧）**:
- URL: https://drrrkari.com/lounge.php
- 部屋情報: 名前、作成者、現在人数/定員
- 満室でない部屋に「入室」ボタン

**チャットルーム**:
- URL: https://drrrkari.com/room.php?id=<room_id>
- ajax.php経由でメッセージ取得（1.5秒ポーリング）
- レスポンス形式: JSON（talks, usersを含む）

**データ構造**:
```json
{
  "talks": {
    "message_id": {
      "id": "unique_id",
      "uid": "user_id_hash",
      "name": "ハンドルネーム",
      "message": "メッセージ内容",
      "time": 1234567890,
      "icon": "icon_name",
      "encip": "",  // 通常空
      "trip": ""
    }
  },
  "users": {
    "user_id": {
      "id": "user_id_hash",
      "name": "ハンドルネーム",
      "icon": "icon_name"
    }
  }
}
```

**重要**: `encip`は通常空なので、ユーザー追跡には`uid`（md5(name+IP)）を使用する。

---

## フェーズ2: BOT実装

### 要件

**ファイル**: `scripts/parallel_patrol_bot.py`

**機能**:
1. Playwrightで30の並列ブラウザインスタンス起動
2. 各BOTがランダムなアイコンと名前でログイン
3. ラウンジから無人の部屋を検索して入室
4. ajax.php（`?fast=1`）を1.5秒ごとにポーリング
5. 新規メッセージをJSONファイルに保存

**保存先**:
- プライマリ: `\\Desktop-jp91uul\開発関連\dura_logs\<YYYYMMDD>\room_<room_id>_<room_name>.json`
- フォールバック: `./log/room_<room_id>_<room_name>.json`

**JSONファイル形式**:
```json
{
  "room_id": "abc123...",
  "room_name": "部屋名",
  "last_updated": "2025-11-23T12:00:00",
  "total_messages": 50,
  "messages": [
    {
      "id": "msg_id",
      "uid": "user_id",
      "name": "ハンドルネーム",
      "message": "メッセージ内容",
      "time": 1234567890,
      "icon": "icon_name",
      "encip": "",
      "trip": "",
      "captured_at": "2025-11-23T12:00:00.123456"
    }
  ]
}
```

**重要な実装ポイント**:
1. Google Drive失敗時は自動的にローカルへフォールバック
2. 重複メッセージは保存しない（`id`でチェック）
3. 部屋が満室の場合は他の部屋を探す
4. エラー時は詳細ログを出力

### 設定

```python
MAX_MONITORS = 30
LOG_DIR = "./log"
GOOGLE_DRIVE = r"\\Desktop-jp91uul\開発関連"
POLL_INTERVAL = 1.5  # 秒
```

---

## フェーズ3: ログビューアー実装

### 要件

**ファイル**: `scripts/log_viewer_clean.py`

**フレームワーク**: Flask + Flask-SocketIO

**機能**:
1. ログディレクトリを5秒ごとにスキャン
2. RESTful APIで部屋とメッセージを提供
3. Socket.IOでリアルタイム更新通知
4. ユーザー分析API

**APIエンドポイント**:

```python
# 基本
GET / - ビューアーHTML
GET /user_analysis - ユーザー分析HTML

# 部屋関連
GET /api/rooms - 全部屋のリスト
GET /api/room/<room_id>/messages - 特定部屋のメッセージ

# ユーザー分析
GET /api/user/<uid>/profile - ユーザープロファイル
  Response: {
    "uid": "...",
    "usernames": ["名前1", "名前2"],
    "rooms": [{"id": "...", "name": "..."}],
    "message_count": 100,
    "first_seen": timestamp,
    "last_seen": timestamp
  }

GET /api/user/<uid>/messages - ユーザーの全メッセージ
  Response: [
    {
      "id": "...",
      "name": "...",
      "message": "...",
      "time": timestamp,
      "room_id": "...",
      "room_name": "..."
    }
  ]
```

**設定**:
```python
LOG_DIR = "./log"
HOST = "0.0.0.0"
PORT = 5000
APP_SECRET = "drrrkari-log-viewer-2025"
```

**重要**: JSONファイルを開く際は必ず`encoding='utf-8'`を指定

---

## フェーズ4: フロントエンド実装

### ファイル1: `templates/viewer.html`

**機能**:
- 左サイドバー: 部屋リスト（検索可能）
- 右メインエリア: 選択した部屋のメッセージ表示
- リアルタイム更新（Socket.IO）
- 統計表示（部屋数、総メッセージ数）

**デザイン要件**:
- グラデーション背景（#667eea → #764ba2）
- カード型UI
- レスポンシブデザイン
- アニメーション（slideIn, pulse）

**技術スタック**:
- Socket.IO クライアント
- Vanilla JavaScript（jQueryは不要）
- CSS Grid / Flexbox

### ファイル2: `templates/user_analysis.html`

**機能**:
- UID検索ボックス
- 2カラムグリッド:
  - 左: プロファイルカード（統計、使用名前、訪問部屋）
  - 右: メッセージ履歴（スクロール可能）
- 「部屋リストに戻る」リンク

**重要**: APIパスは`location.origin`を使って絶対パスで指定
```javascript
fetch(location.origin + '/api/user/' + uid + '/profile')
```

---

## フェーズ5: 動作確認

### 確認項目

1. **BOT起動**:
```bash
cd c:/Users/admin/.gemini/antigravity/scratch
python scripts/parallel_patrol_bot.py
```
- 30個のブラウザが起動すること
- `./log/`ディレクトリにJSONファイルが作成されること

2. **ビューアー起動**:
```bash
python scripts/log_viewer_clean.py
```
- http://localhost:5000 でアクセス可能
- 部屋リストが表示されること
- 部屋をクリックするとメッセージが表示されること

3. **ユーザー分析**:
- http://localhost:5000/user_analysis にアクセス
- UIDを入力して検索
- プロファイルとメッセージが表示されること

---

## 成果物チェックリスト

### ファイル構成
```
scratch/
├── scripts/
│   ├── parallel_patrol_bot.py (BOT実装)
│   └── log_viewer_clean.py (ビューアー実装)
├── templates/
│   ├── viewer.html (部屋リスト・メッセージ表示)
│   └── user_analysis.html (ユーザー分析)
└── log/ (自動生成)
    └── room_*.json
```

### 機能要件
- [ ] 30並列BOTが稼働
- [ ] ログがJSON形式で保存
- [ ] Google Drive失敗時はローカル保存
- [ ] ビューアーで部屋リスト表示
- [ ] リアルタイム更新
- [ ] ユーザー分析でUID検索可能
- [ ] プロファイル表示（使用名前、訪問部屋）
- [ ] メッセージ履歴表示

### 品質要件
- [ ] エラーハンドリング（try-except）
- [ ] ログ出力（logger使用）
- [ ] UTF-8エンコーディング明示
- [ ] 重複メッセージ防止
- [ ] XSS対策（escapeHtml）

---

## 注意事項

### 避けるべき実装
❌ `encip`フィールドに依存（空の場合が多い）
❌ ハードコードされたパス（環境変数推奨）
❌ エラーの黙殺（`except: pass`）
❌ 一度に複数箇所の大規模編集

### 推奨アプローチ
✅ `uid`でユーザー追跡
✅ フォールバック戦略
✅ 段階的実装（単純→複雑）
✅ 小さなファイル（200行以下）
✅ 詳細なエラーログ

---

## トラブルシューティング

### よくある問題

**問題1**: 部屋リストが空
- 原因: LOG_DIRのパスが間違っている
- 解決: `os.path.abspath(LOG_DIR)`でパス確認

**問題2**: UnicodeDecodeError
- 原因: `encoding='utf-8'`の指定忘れ
- 解決: 全ての`open()`に`encoding='utf-8'`追加

**問題3**: ユーザー分析でAPI呼び出しエラー
- 原因: 相対パスの使用
- 解決: `location.origin`を使った絶対パス

**問題4**: Google Driveアクセスエラー
- 原因: ネットワークドライブ未接続
- 解決: フォールバックが機能すればOK（ログで確認）

---

## 期待される実行結果

### BOT実行時
```
=== BOT 1 Starting ===
✅ Logged in as: パトロール_abc123 (icon: nyan)
🔍 Searching for unmanned room...
✅ Entered room: テスト部屋
📊 Saved 5 new messages to ./log/room_abc123_テスト部屋.json
```

### ビューアー実行時
```
============================================================
🚀 Log Viewer running on http://localhost:5000
📂 Watching: C:\...\scratch\log
============================================================
🔄 Scanning logs...
✅ Found 30 rooms
```

### ブラウザ表示
- 部屋リスト: 30部屋表示
- メッセージ: リアルタイム更新
- ユーザー分析: プロファイルと履歴表示

---

## 追加の要望

以上の仕様で基本システムを構築した後、以下の拡張が可能です：

1. **設定管理**: config.py作成
2. **テストコード**: pytest導入
3. **ドキュメント**: README.md作成
4. **検索機能**: メッセージ内容検索
5. **統計ダッシュボード**: グラフ表示

必要に応じて段階的に実装してください。
```

---

## プロンプト終了

## 使用上の注意

### このプロンプトの特徴
1. **段階的構造**: フェーズ1→5で順次実装
2. **具体的仕様**: コードサンプル、API仕様を含む
3. **トラブルシューティング**: よくある問題と解決策
4. **品質基準**: チェックリストで確認

### カスタマイズポイント
- 作業ディレクトリパス
- Google Driveパス
- MAX_MONITORSの数
- デザインの詳細

### 想定される所要時間
- フェーズ1-2: 30分（BOT実装）
- フェーズ3: 20分（API実装）
- フェーズ4: 30分（フロントエンド）
- フェーズ5: 10分（動作確認）
- **合計**: 約90分

このプロンプトを使用することで、同等の機能を持つシステムを短時間で再構築できます。
