import os
import json
import threading
import logging
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit

# Configuration
APP_SECRET = 'drrrkari-log-viewer-2025'
LOG_DIR = "./log"  # ローカルログディレクトリ

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = APP_SECRET
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Simple log manager
rooms_cache = {}

def scan_logs():
    """Scan log directory and build room cache"""
    global rooms_cache
    logger.info("🔄 Scanning logs...")
    
    abs_path = os.path.abspath(LOG_DIR)
    logger.info(f"Scanning: {abs_path}")
    logger.info(f"Exists: {os.path.exists(LOG_DIR)}")
    
    if not os.path.exists(LOG_DIR):
        logger.warning(f"Log directory does not exist: {LOG_DIR} (abs: {abs_path})")
        return
    
    rooms_cache = {}
    
    for filename in os.listdir(LOG_DIR):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(LOG_DIR, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict) or 'room_id' not in data:
                continue
            
            room_id = data.get('room_id')
            if not room_id:
                # Use filename as fallback ID
                room_id = filename.replace('.json', '')
            
            rooms_cache[room_id] = {
                'id': room_id,
                'name': data.get('room_name', 'Unknown'),
                'last_updated': data.get('last_updated', ''),
                'message_count': len(data.get('messages', [])),
                'filepath': filepath
            }
            
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
    
    logger.info(f"✅ Found {len(rooms_cache)} rooms")

# Routes
@app.route('/')
def index():
    try:
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'viewer.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error loading viewer.html: {e}"

@app.route('/user_analysis')
def user_analysis():
    try:
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'user_analysis.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error loading user_analysis.html: {e}"

@app.route('/api/rooms')
def api_rooms():
    return jsonify(list(rooms_cache.values()))

@app.route('/api/room/<room_id>/messages')
def api_room_messages(room_id):
    if room_id not in rooms_cache:
        return jsonify([])
    
    filepath = rooms_cache[room_id]['filepath']
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data.get('messages', []))
    except:
        return jsonify([])

@app.route('/api/user/<uid>/profile')
def api_user_profile(uid):
    """Get user profile by uid - shows all usernames used, rooms visited, etc."""
    profile = {
        'uid': uid,
        'usernames': set(),
        'rooms': set(),
        'message_count': 0,
        'first_seen': None,
        'last_seen': None
    }
    
    # Scan all room logs
    for room_id, room_data in rooms_cache.items():
        filepath = room_data['filepath']
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = data.get('messages', [])
            for msg in messages:
                if msg.get('uid') == uid:
                    profile['usernames'].add(msg.get('name', '不明'))
                    profile['rooms'].add((room_id, room_data.get('name', '不明')))
                    profile['message_count'] += 1
                    
                    msg_time = msg.get('time', 0)
                    if profile['first_seen'] is None or msg_time < profile['first_seen']:
                        profile['first_seen'] = msg_time
                    if profile['last_seen'] is None or msg_time > profile['last_seen']:
                        profile['last_seen'] = msg_time
        except:
            continue
    
    # Convert sets to lists for JSON
    profile['usernames'] = list(profile['usernames'])
    profile['rooms'] = [{'id': r[0], 'name': r[1]} for r in profile['rooms']]
    
    return jsonify(profile)

@app.route('/api/user/<uid>/messages')
def api_user_messages(uid):
    """Get all messages by a specific uid"""
    messages = []
    
    for room_id, room_data in rooms_cache.items():
        filepath = room_data['filepath']
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for msg in data.get('messages', []):
                if msg.get('uid') == uid:
                    msg_copy = msg.copy()
                    msg_copy['room_id'] = room_id
                    msg_copy['room_name'] = room_data.get('name', '不明')
                    messages.append(msg_copy)
        except:
            continue
    
    # Sort by time (newest first)
    messages.sort(key=lambda x: x.get('time', 0), reverse=True)
def background_monitor():
    """Periodically rescan logs"""
    import time
    while True:
        time.sleep(5)
        scan_logs()
        socketio.emit('log_update', {}, namespace='/')

if __name__ == '__main__':
    # Initial scan
    scan_logs()
    
    # Start background monitor
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    print("=" * 60)
    print(f"🚀 Log Viewer running on http://localhost:5000")
    print(f"📂 Watching: {os.path.abspath(LOG_DIR)}")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
