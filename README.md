# デュラチャログシステム

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 概要

**デュラチャログシステム**は、匿名チャットサイト [drrrkari.com](https://drrrkari.com)（通称：デュラチャ）のチャットログを自動収集・分析するシステムです。

### 主な機能

- 🤖 **30並列BOT**: Playwrightを使用した並列ログ収集
- 📊 **リアルタイムビューアー**: Flask + Socket.IOによるリアルタイム表示
- 👤 **ユーザー分析**: UIDベースの行動追跡・分析

---

## スクリーンショット

### ログビューアー
リアルタイムでチャットログを表示

### ユーザー分析
特定ユーザーの行動を追跡・分析

---

## セットアップ

### 必要要件

- Python 3.10以上
- Windows 10/11（推奨）

### インストール

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd scratch
```

2. **依存関係のインストール**
```bash
pip install -r requirements.txt
playwright install chromium
```

3. **環境設定**
```bash
copy .env.example .env
# .env を編集して設定を調整
```

---

## 使い方

### BOT起動（ログ収集）

```bash
# Windowsバッチファイルから
scripts\start_bot.bat

# または直接Python実行
python -m src.bot.parallel_patrol_bot
```

30個のブラウザインスタンスが起動し、デュラチャの部屋に入室してログを収集します。

### ビューアー起動（ログ表示）

```bash
# Windowsバッチファイルから
scripts\start_viewer.bat

# または直接Python実行
python -m src.viewer.log_viewer
```

ブラウザで以下にアクセス：
- **ログビューアー**: http://localhost:5000
- **ユーザー分析**: http://localhost:5000/user_analysis

### 全停止

```bash
scripts\stop_all.bat
```

---

## プロジェクト構造

```
scratch/
├── src/                   # ソースコード
│   ├── bot/              # BOT実装
│   ├── viewer/           # ビューアー実装
│   └── utils/            # 共通ユーティリティ
├── templates/            # HTMLテンプレート
├── data/                 # データディレクトリ
│   ├── logs/            # 収集されたログ
│   └── backups/         # バックアップ
├── docs/                 # ドキュメント
├── scripts/              # 起動スクリプト
├── config.py            # 設定管理
└── README.md            # このファイル
```

---

## 設定

### config.py

主要な設定は `config.py` で管理されます：

```python
MAX_MONITORS = 30        # 並列BOT数
POLL_INTERVAL = 1.5      # ポーリング間隔（秒）
LOG_DIR = "./data/logs"  # ログ保存先
VIEWER_PORT = 5000       # ビューアーポート
```

### 環境変数（.env）

```bash
MAX_MONITORS=30
VIEWER_PORT=5000
DEBUG=False
LOG_LEVEL=INFO
```

---

## API仕様

### エンドポイント

#### `GET /api/rooms`
全部屋のリストを取得

**Response:**
```json
[
  {
    "id": "room_id",
    "name": "部屋名",
    "message_count": 100,
    "last_updated": "2025-11-23T12:00:00"
  }
]
```

#### `GET /api/room/<room_id>/messages`
特定部屋のメッセージを取得

#### `GET /api/user/<uid>/profile`
ユーザープロファイルを取得

**Response:**
```json
{
  "uid": "user_id_hash",
  "usernames": ["名前1", "名前2"],
  "rooms": [{"id": "...", "name": "..."}],
  "message_count": 50,
  "first_seen": 1234567890,
  "last_seen": 1234567890
}
```

#### `GET /api/user/<uid>/messages`
特定ユーザーの全メッセージを取得

---

## トラブルシューティング

### 部屋リストが表示されない

**原因**: LOG_DIRのパスが間違っている

**解決**:
```python
from config import config
print(config.LOG_DIR)  # パス確認
```

### Google Driveアクセスエラー

**原因**: ネットワークドライブが接続されていない

**解決**: ローカルフォールバックが自動的に機能します（`data/logs/`に保存）

### ポート5000が使用中

**解決**: `.env`で別のポートを指定
```bash
VIEWER_PORT=8000
```

---

## 開発

### テストコード実行（将来）

```bash
pytest tests/
```

### コード整形

```bash
black src/
```

### ドキュメント生成

```bash
# 詳細は docs/ 配下を参照
```

---

## ライセンス

MIT License

---

## 貢献

プルリクエスト歓迎！

---

## 関連ドキュメント

- [技術仕様](docs/technical_spec.md)
- [開発ガイド](docs/development_guide.md)
- [API仕様](docs/api_reference.md)
- [再現ガイド](docs/reproduction_guide.md)

---

## 作者

デュラチャログシステム開発チーム

## 更新履歴

### v0.1.0 (2025-11-23)
- 初版リリース
- 30並列BOT実装
- リアルタイムビューアー実装
- ユーザー分析機能実装
