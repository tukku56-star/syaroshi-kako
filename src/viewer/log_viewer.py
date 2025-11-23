import os
import json
import threading
import logging
from flask import Flask, jsonify, Response
from flask_socketio import SocketIO, emit
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import csv
import io
from config import config, PROJECT_ROOT
from src.utils.logger import setup_logger

# Logger setup
logger = setup_logger("viewer")

app = Flask(__name__)
app.config['SECRET_KEY'] = config.APP_SECRET
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Simple log manager
rooms_cache = {}

def scan_logs():
    """Scan log directory and build room cache"""
    global rooms_cache
    # logger.info("🔄 Scanning logs...")
    
    # Try Google Drive first if enabled, otherwise local
    scan_dir = config.GOOGLE_DRIVE_PATH if config.GOOGLE_DRIVE_ENABLED and os.path.exists(config.GOOGLE_DRIVE_PATH) else config.LOG_DIR
    
    # If Google Drive path is set but not found, fallback to local
    if config.GOOGLE_DRIVE_ENABLED and not os.path.exists(config.GOOGLE_DRIVE_PATH):
        logger.warning(f"Google Drive path not found: {config.GOOGLE_DRIVE_PATH}. Falling back to local: {config.LOG_DIR}")
        scan_dir = config.LOG_DIR
    
    # Handle date-based structure in Google Drive
    # If scanning root of Google Drive path, we might need to look into date folders
    # For now, let's assume flat structure or scan recursively if needed
    # But the bot saves to YYYY-MM-DD/log/
    
    # Simplified: Just scan the configured LOG_DIR (local) for now to ensure stability, 
    # or if we want to view Drive logs, we need to handle the date structure.
    # Let's stick to the behavior of the original viewer which scanned LOG_DIR.
    # BUT, the bot is now saving to Drive.
    
    # Strategy: Scan all subdirectories if it's a drive path
    log_files = []
    
    if config.GOOGLE_DRIVE_ENABLED and os.path.exists(config.GOOGLE_DRIVE_PATH):
        # Walk through date directories
        for root, dirs, files in os.walk(config.GOOGLE_DRIVE_PATH):
            for file in files:
                if file.endswith('.json'):
                    log_files.append(os.path.join(root, file))
    else:
        # Local scan
        if os.path.exists(config.LOG_DIR):
            for file in os.listdir(config.LOG_DIR):
                if file.endswith('.json'):
                    log_files.append(os.path.join(config.LOG_DIR, file))
    
    new_cache = {}
    
    for filepath in log_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict) or 'room_id' not in data:
                continue
            
            room_id = data.get('room_id')
            if not room_id:
                filename = os.path.basename(filepath)
                room_id = filename.replace('.json', '')
            
            new_cache[room_id] = {
                'id': room_id,
                'name': data.get('room_name', 'Unknown'),
                'last_updated': data.get('last_updated', ''),
                'message_count': len(data.get('messages', [])),
                'filepath': filepath
            }
            
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
    
    rooms_cache = new_cache
    # logger.info(f"✅ Found {len(rooms_cache)} rooms")

# Routes
@app.route('/')
def index():
    try:
        template_path = config.TEMPLATE_DIR / 'viewer.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error loading viewer.html: {e}"

@app.route('/user_analysis')
def user_analysis():
    try:
        template_path = config.TEMPLATE_DIR / 'user_analysis.html'
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
    # Sort by time (newest first)
    messages.sort(key=lambda x: x.get('time', 0), reverse=True)
    return jsonify(messages)

@app.route('/api/status')
def api_status():
    """Get current bot status"""
    try:
        status_file = PROJECT_ROOT / "data" / "bot_status.json"
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify([])
    except Exception as e:
        logger.error(f"Error reading status: {e}")
        return jsonify([])

@app.route('/api/stats')
def api_stats():
    """Get statistical data for graphs"""
    stats = {
        'hourly_activity': defaultdict(int),
        'room_activity': {},
        'active_users': Counter()
    }
    
    for room_id, room_data in rooms_cache.items():
        # Room activity
        stats['room_activity'][room_data['name']] = room_data['message_count']
        
        filepath = room_data['filepath']
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for msg in data.get('messages', []):
                # Hourly activity
                try:
                    # Time format example: "2025-11-23T12:34:56.789"
                    captured_at = msg.get('captured_at')
                    if captured_at:
                        dt = datetime.fromisoformat(captured_at)
                        hour_key = dt.strftime("%H:00")
                        stats['hourly_activity'][hour_key] += 1
                except:
                    pass
                
                # Active users
                name = msg.get('name', 'Unknown')
                stats['active_users'][name] += 1
                
        except:
            continue
            
    # Convert for JSON
    return jsonify({
        'hourly_activity': dict(sorted(stats['hourly_activity'].items())),
        'room_activity': stats['room_activity'],
        'active_users': stats['active_users'].most_common(20)
    })

@app.route('/api/analysis/ip')
def api_analysis_ip():
    """Find users sharing the same IP (encip or hostip)"""
    ip_map = defaultdict(set)
    
    for room_id, room_data in rooms_cache.items():
        filepath = room_data['filepath']
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for msg in data.get('messages', []):
                encip = msg.get('encip')
                uid = msg.get('uid')
                name = msg.get('name')
                
                if encip and uid:
                    ip_map[encip].add((uid, name))
        except:
            continue
            
    # Filter for IPs with multiple UIDs
    suspicious_ips = []
    for ip, users in ip_map.items():
        unique_uids = set(u[0] for u in users)
        if len(unique_uids) > 1:
            suspicious_ips.append({
                'ip': ip,
                'users': [{'uid': u[0], 'name': u[1]} for u in users],
                'count': len(unique_uids)
            })
            
    return jsonify(sorted(suspicious_ips, key=lambda x: x['count'], reverse=True))

@app.route('/api/analysis/suspicious')
def api_analysis_suspicious():
    """Detect suspicious behavior like frequent name changes"""
    user_history = defaultdict(list)
    suspicious_users = []
    
    for room_id, room_data in rooms_cache.items():
        filepath = room_data['filepath']
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for msg in data.get('messages', []):
                uid = msg.get('uid')
                name = msg.get('name')
                captured_at = msg.get('captured_at')
                
                if uid and name and captured_at:
                    user_history[uid].append({
                        'name': name,
                        'time': datetime.fromisoformat(captured_at)
                    })
        except:
            continue
            
    # Analyze history
    for uid, history in user_history.items():
        history.sort(key=lambda x: x['time'])
        
        # Check for name changes
        names = set()
        for event in history:
            names.add(event['name'])
            
        if len(names) > 3: # Arbitrary threshold
            suspicious_users.append({
                'uid': uid,
                'type': 'Frequent Name Change',
                'details': f"Used {len(names)} different names",
                'names': list(names)
            })
            
    return jsonify(suspicious_users)

@app.route('/api/export/<room_id>')
def api_export_room(room_id):
    """Export room logs to CSV"""
    if room_id not in rooms_cache:
        return "Room not found", 404
        
    filepath = rooms_cache[room_id]['filepath']
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Time', 'Name', 'Message', 'UID', 'IP', 'Trip'])
        
        for msg in data.get('messages', []):
            writer.writerow([
                msg.get('time', ''),
                msg.get('name', ''),
                msg.get('message', ''),
                msg.get('uid', ''),
                msg.get('encip', ''),
                msg.get('trip', '')
            ])
            
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=room_{room_id}.csv"}
        )
    except Exception as e:
        return f"Error exporting: {e}", 500

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
    print(f"🚀 Log Viewer running on http://{config.VIEWER_HOST}:{config.VIEWER_PORT}")
    print(f"📂 Watching: {config.GOOGLE_DRIVE_PATH if config.GOOGLE_DRIVE_ENABLED else config.LOG_DIR}")
    print("=" * 60)
    
    socketio.run(app, host=config.VIEWER_HOST, port=config.VIEWER_PORT, debug=config.VIEWER_DEBUG, allow_unsafe_werkzeug=True)
