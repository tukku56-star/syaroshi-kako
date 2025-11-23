import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

# --- Configuration ---
APP_SECRET = 'drrrkari-log-viewer-2025-optimized'
NETWORK_DRIVE_PATH = r"\\Desktop-jp91uul\開発関連"
LOCAL_FALLBACK_PATH = "../log"  # ネットワークドライブがない場合の予備
POLL_INTERVAL = 2.0            # 監視間隔（秒）

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='.') # HTMLが同じ階層にあると仮定
app.config['SECRET_KEY'] = APP_SECRET
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class LogManager:
    def __init__(self):
        self.rooms_cache = {}  # {room_id: {metadata...}}
        self.file_index = {}   # {file_path: last_mtime}
        self.lock = threading.RLock()
        self.base_path = self._determine_base_path()
        
    def _determine_base_path(self):
        """ネットワークパスが有効か確認し、だめならローカルを使う"""
        if os.path.exists(NETWORK_DRIVE_PATH):
            logger.info(f"📂 Network drive found: {NETWORK_DRIVE_PATH}")
            return NETWORK_DRIVE_PATH
        logger.warning(f"⚠️ Network drive not found. Using local: {LOCAL_FALLBACK_PATH}")
        if not os.path.exists(LOCAL_FALLBACK_PATH):
            os.makedirs(LOCAL_FALLBACK_PATH)
        return LOCAL_FALLBACK_PATH

    def _parse_room_file(self, filepath):
        """ファイルを読み込んでルーム情報を返す（失敗時はNone）"""
        try:
            # ファイルサイズが0ならスキップ
            if os.path.getsize(filepath) == 0:
                return None

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict) or 'room_id' not in data:
                return None
                
            return {
                'id': data.get('room_id'),
                'name': data.get('room_name', 'Unknown'),
                'last_updated': data.get('last_updated'),
                'message_count': len(data.get('messages', [])),
                'filepath': filepath,
            stat = os.stat(filepath)
            mtime = stat.st_mtime
            
            # 変更がなければスキップ
            if filepath in self.file_index and self.file_index[filepath] == mtime:
                return False

            room_data = self._parse_room_file(filepath)
            if not room_data:
                return False

            room_id = room_data['id']
            
            with self.lock:
                # キャッシュ更新（同じ部屋IDで複数のファイルがある場合、最新を優先してマージするロジックが必要だが、
                # ここではシンプルに「最新の更新日時を持つもの」をメタデータとして採用し、
                # メッセージ取得時に全ファイルを結合する方式をとる）
                
                if room_id not in self.rooms_cache:
                    self.rooms_cache[room_id] = {'files': set()}
                
                # この部屋に紐づくファイルパスを記録
                self.rooms_cache[room_id]['files'].add(filepath)
                
                # メタデータの更新（より新しい場合のみ）
                current_meta = self.rooms_cache[room_id].get('meta')
                new_date = room_data.get('last_updated', '')
                
                should_update = False
                if not current_meta:
                    should_update = True
                elif new_date > current_meta.get('last_updated', ''):
                    should_update = True
                
                if should_update:
                    self.rooms_cache[room_id]['meta'] = {
                        'id': room_data['id'],
                        'name': room_data['name'],
                        'last_updated': room_data['last_updated'],
                        # message_countは全ファイルの合計にするため、ここでは仮
                    }
                
                # 全ファイルの合計メッセージ数を再計算
                total_msgs = 0
                for fpath in self.rooms_cache[room_id]['files']:
                    # 注: 厳密には全ファイル開くのは重いが、頻繁な処理ではないため許容
                    # 高速化するならファイルごとのcountを別途キャッシュする
                    try:
                        if fpath == filepath: 
                            total_msgs += room_data['message_count']
                        else:
                            # 簡易的にサイズから推測等はせず、開く（正確性重視）
                            with open(fpath, 'r', encoding='utf-8') as f:
                                d = json.load(f)
                                total_msgs += len(d.get('messages', []))
                    except: pass
                
                if 'meta' in self.rooms_cache[room_id]:
                    self.rooms_cache[room_id]['meta']['message_count'] = total_msgs

                self.file_index[filepath] = mtime
                return True # 更新あり

        except Exception as e:
            return False

    def get_all_rooms(self):
        """ルーム一覧を返す"""
        with self.lock:
            rooms = []
            for r_data in self.rooms_cache.values():
                if 'meta' in r_data:
                    rooms.append(r_data['meta'])
            # 更新日時順にソート
            return sorted(rooms, key=lambda x: x.get('last_updated', ''), reverse=True)

    def get_messages(self, room_id, limit=None):
        """指定ルームの全メッセージを取得"""
        with self.lock:
            if room_id not in self.rooms_cache:
                return []
            
            all_messages = []
            files = self.rooms_cache[room_id]['files']
            
            seen_ids = set()
            
            for filepath in files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        msgs = data.get('messages', [])
                        for m in msgs:
                            if m['id'] not in seen_ids:
                                all_messages.append(m)
                                seen_ids.add(m['id'])
                except:
                    continue
            
            # 時系列ソート（新しい順）
            all_messages.sort(key=lambda x: x.get('time', 0), reverse=True)
            
            if limit:
                return all_messages[:limit]
            return all_messages

    def search(self, query):
        """全メッセージから検索 (キャッシュ活用は今後の課題、現在はファイル走査)"""
        # メモリ効率のため、直近のファイルのみ検索などの制限を入れるのが望ましい
        results = []
        query = query.lower()
        
        with self.lock:
            # 全部屋をループ
            for room_id, cache in self.rooms_cache.items():
                files = cache['files']
                room_name = cache.get('meta', {}).get('name', 'Unknown')
                
                for filepath in files:
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for msg in data.get('messages', []):
                                if (query in msg.get('name', '').lower() or 
                                    query in msg.get('message', '').lower() or
                                    query in str(msg.get('trip', ''))):
                                    
                                    msg['room_name'] = room_name
                                    msg['room_id'] = room_id
                                    results.append(msg)
                    except: continue
                    
        # 新しい順
        results.sort(key=lambda x: x.get('time', 0), reverse=True)
        return results[:200] # 最大200件

# Initialize Manager
log_manager = LogManager()

def monitor_logs_background():
    """効率的なポーリング監視タスク"""
    logger.info("👀 Log monitor started")
    
    while True:
        try:
            # 1. 今日の日付フォルダを特定
            now = datetime.now()
            targets = [
                now.strftime("%Y-%m-%d"),
                (now - timedelta(days=1)).strftime("%Y-%m-%d") # 昨日も一応見る
            ]
            
            base = log_manager.base_path
            updated_rooms = set()

            # ターゲットの日付フォルダ内のlogディレクトリのみを監視
            for date_str in targets:
                # パターン1: base/YYYY-MM-DD/log/
                # パターン2: base/log/ (ルート直下)
                
                check_paths = [
                    os.path.join(base, date_str, "log"),
                    os.path.join(base, "log")
                ]

                for log_dir in check_paths:
                    if not os.path.exists(log_dir): continue
                    
                    # ディレクトリ自体の更新日時をチェック（Linux/Unix系で有効、Windowsは注意）
                    # Windowsのネットワークドライブだとdirのmtimeが変わらないことがあるため
                    # ファイルリストを取得してループするが、ターゲットフォルダを限定しているので軽量
                    
                    try:
                        for filename in os.listdir(log_dir):
                            if not filename.endswith('.json'): continue
                            
                            filepath = os.path.join(log_dir, filename)
                            
                            # キャッシュ更新を試みる
                            if log_manager.update_file_cache(filepath):
                                # 部屋IDをファイル名から簡易抽出 (room_{id}_...)
                                parts = filename.split('_')
                                if len(parts) >= 2:
                                    updated_rooms.add(parts[1])
                    except Exception as e:
                        logger.error(f"Polling error in {log_dir}: {e}")

            # 更新があった部屋があればクライアントに通知
            for room_id in updated_rooms:
                # 最新のメッセージを取得して送信
                msgs = log_manager.get_messages(room_id, limit=50)
                room_info = log_manager.rooms_cache[room_id].get('meta')
                
                if room_info:
                    socketio.emit('new_messages', {
                        'room_id': room_id,
                        'room_name': room_info['name'],
                        'messages': msgs,
                        'timestamp': datetime.now().isoformat()
                    }, namespace='/')
                    logger.info(f"📡 Emitted update for room {room_id}")

            time.sleep(POLL_INTERVAL)
            
        except Exception as e:
            room_id = room_data['id']
            
            with self.lock:
                # キャッシュ更新（同じ部屋IDで複数のファイルがある場合、最新を優先してマージするロジックが必要だが、
                # ここではシンプルに「最新の更新日時を持つもの」をメタデータとして採用し、
                # メッセージ取得時に全ファイルを結合する方式をとる）
                
                if room_id not in self.rooms_cache:
                    self.rooms_cache[room_id] = {'files': set()}
                
                # この部屋に紐づくファイルパスを記録
                self.rooms_cache[room_id]['files'].add(filepath)
                
                # メタデータの更新（より新しい場合のみ）
                current_meta = self.rooms_cache[room_id].get('meta')
                new_date = room_data.get('last_updated', '')
                
                should_update = False
                if not current_meta:
                    should_update = True
                elif new_date > current_meta.get('last_updated', ''):
                    should_update = True
                
                if should_update:
                    self.rooms_cache[room_id]['meta'] = {
                        'id': room_data['id'],
                        'name': room_data['name'],
                        'last_updated': room_data['last_updated'],
                        # message_countは全ファイルの合計にするため、ここでは仮
                    }
                
                # 全ファイルの合計メッセージ数を再計算
                total_msgs = 0
                for fpath in self.rooms_cache[room_id]['files']:
                    # 注: 厳密には全ファイル開くのは重いが、頻繁な処理ではないため許容
                    # 高速化するならファイルごとのcountを別途キャッシュする
                    try:
                        if fpath == filepath: 
                            total_msgs += room_data['message_count']
                        else:
                            # 簡易的にサイズから推測等はせず、開く（正確性重視）
                            with open(fpath, 'r', encoding='utf-8') as f:
                                d = json.load(f)
                                total_msgs += len(d.get('messages', []))
                    except: pass
                
                if 'meta' in self.rooms_cache[room_id]:
                    self.rooms_cache[room_id]['meta']['message_count'] = total_msgs

                self.file_index[filepath] = mtime
                return True # 更新あり

        except Exception as e:
            return False

    def get_all_rooms(self):
        """ルーム一覧を返す"""
        with self.lock:
            rooms = []
            for r_data in self.rooms_cache.values():
                if 'meta' in r_data:
                    rooms.append(r_data['meta'])
            # 更新日時順にソート
            return sorted(rooms, key=lambda x: x.get('last_updated', ''), reverse=True)

    def get_messages(self, room_id, limit=None):
        """指定ルームの全メッセージを取得"""
        with self.lock:
            if room_id not in self.rooms_cache:
                return []
            
            all_messages = []
            files = self.rooms_cache[room_id]['files']
            
            seen_ids = set()
            
            for filepath in files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        msgs = data.get('messages', [])
                        for m in msgs:
                            if m['id'] not in seen_ids:
                                all_messages.append(m)
                                seen_ids.add(m['id'])
                except:
                    continue
            
            # 時系列ソート（新しい順）
            all_messages.sort(key=lambda x: x.get('time', 0), reverse=True)
            
            if limit:
                return all_messages[:limit]
            return all_messages

    def search(self, query):
        """全メッセージから検索 (キャッシュ活用は今後の課題、現在はファイル走査)"""
        # メモリ効率のため、直近のファイルのみ検索などの制限を入れるのが望ましい
        results = []
        query = query.lower()
        
        with self.lock:
            # 全部屋をループ
            for room_id, cache in self.rooms_cache.items():
                files = cache['files']
                room_name = cache.get('meta', {}).get('name', 'Unknown')
                
                for filepath in files:
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for msg in data.get('messages', []):
                                if (query in msg.get('name', '').lower() or 
                                    query in msg.get('message', '').lower() or
                                    query in str(msg.get('trip', ''))):
                                    
                                    msg['room_name'] = room_name
                                    msg['room_id'] = room_id
                                    results.append(msg)
                    except: continue
                    
        # 新しい順
        results.sort(key=lambda x: x.get('time', 0), reverse=True)
        return results[:200] # 最大200件

# Initialize Manager
log_manager = LogManager()

def monitor_logs_background():
    """効率的なポーリング監視タスク"""
    logger.info("👀 Log monitor started")
    
    while True:
        try:
            # 1. 今日の日付フォルダを特定
            now = datetime.now()
            targets = [
                now.strftime("%Y-%m-%d"),
                (now - timedelta(days=1)).strftime("%Y-%m-%d") # 昨日も一応見る
            ]
            
            base = log_manager.base_path
            updated_rooms = set()

            # ターゲットの日付フォルダ内のlogディレクトリのみを監視
            for date_str in targets:
                # パターン1: base/YYYY-MM-DD/log/
                # パターン2: base/log/ (ルート直下)
                
                check_paths = [
                    os.path.join(base, date_str, "log"),
                    os.path.join(base, "log")
                ]

                for log_dir in check_paths:
                    if not os.path.exists(log_dir): continue
                    
                    # ディレクトリ自体の更新日時をチェック（Linux/Unix系で有効、Windowsは注意）
                    # Windowsのネットワークドライブだとdirのmtimeが変わらないことがあるため
                    # ファイルリストを取得してループするが、ターゲットフォルダを限定しているので軽量
                    
                    try:
                        for filename in os.listdir(log_dir):
                            if not filename.endswith('.json'): continue
                            
                            filepath = os.path.join(log_dir, filename)
                            
                            # キャッシュ更新を試みる
                            if log_manager.update_file_cache(filepath):
                                # 部屋IDをファイル名から簡易抽出 (room_{id}_...)
                                parts = filename.split('_')
                                if len(parts) >= 2:
                                    updated_rooms.add(parts[1])
                    except Exception as e:
                        logger.error(f"Polling error in {log_dir}: {e}")

            # 更新があった部屋があればクライアントに通知
            for room_id in updated_rooms:
                # 最新のメッセージを取得して送信
                msgs = log_manager.get_messages(room_id, limit=50)
                room_info = log_manager.rooms_cache[room_id].get('meta')
                
                if room_info:
                    socketio.emit('new_messages', {
                        'room_id': room_id,
                        'room_name': room_info['name'],
                        'messages': msgs,
                        'timestamp': datetime.now().isoformat()
                    }, namespace='/')
                    logger.info(f"📡 Emitted update for room {room_id}")

            time.sleep(POLL_INTERVAL)
            
        except Exception as e:
            logger.error(f"Monitor loop fatal error: {e}")
            time.sleep(5)

# --- Routes ---

@app.route('/')
def index():
    # テンプレートディレクトリから読み込むように変更
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'viewer.html')
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Template load error: {e}")
        return f"Error loading viewer.html from {template_path}. Please check the file exists."

@app.route('/api/rooms')
def api_rooms():
    return jsonify(log_manager.get_all_rooms())

@app.route('/api/room/<room_id>/messages')
def api_room_messages(room_id):
    limit = request.args.get('limit', None)
    if limit: limit = int(limit)
    return jsonify(log_manager.get_messages(room_id, limit))

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    return jsonify(log_manager.search(query))

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('connected', {'status': 'ok'})

def background_scanner():
    """初期スキャンと監視を行うバックグラウンドタスク"""
    # 1. 初期スキャン (ここでブロックしてもサーバー起動には影響しない)
    log_manager.scan_all()
    
    # 2. 監視ループ開始
    monitor_logs_background()

if __name__ == '__main__':
    # 監視スレッド開始 (初期スキャンもこの中で行う)
    monitor_thread = threading.Thread(target=background_scanner, daemon=True)
    monitor_thread.start()
    
    print("="*60)
    print(f"🚀 Optimized Log Viewer running on http://localhost:5000")
    print(f"📂 Watching: {log_manager.base_path}")
    print("="*60)
    
    # SocketIO Server Start
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)