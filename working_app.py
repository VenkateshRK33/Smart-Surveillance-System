"""
Complete Working Smart Surveillance System
Fixed version with proper upload and video processing
"""
import os
import cv2
import base64
import threading
import time
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

from video_input import VideoSource
from detector_roboflow import Detector
from tracker_memory import TrackerMemory
from behaviour_engine import BehaviourEngine
from ui_overlay import UIOverlay

app = Flask(__name__, static_folder='web')
app.config['SECRET_KEY'] = 'smart-surveillance'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
state = {
    'running': False,
    'video_source': None,
    'detector': None,
    'tracker_memory': None,
    'behaviour_engine': None,
    'ui_overlay': None,
    'thread': None
}

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_video():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    try:
        print("\n" + "="*60)
        print("UPLOAD REQUEST")
        print("="*60)
        
        if 'video' not in request.files:
            return jsonify({'status': 'error', 'message': 'No video file'}), 400
        
        file = request.files['video']
        if not file.filename:
            return jsonify({'status': 'error', 'message': 'Empty filename'}), 400
        
        os.makedirs('uploads', exist_ok=True)
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        
        print(f"✓ File saved: {filepath}")
        return jsonify({'status': 'success', 'filepath': filepath})
    
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def process_video(config):
    """Process video and emit frames via WebSocket"""
    
    def _deduplicate_weapons(weapons):
        """Deduplicate weapons using aggressive NMS"""
        if len(weapons) == 0:
            return []
        
        # Sort by confidence
        weapons.sort(key=lambda x: x['confidence'], reverse=True)
        
        def calculate_iou(box1, box2):
            x1_1, y1_1, x2_1, y2_1 = box1
            x1_2, y1_2, x2_2, y2_2 = box2
            
            x_left = max(x1_1, x1_2)
            y_top = max(y1_1, y1_2)
            x_right = min(x2_1, x2_2)
            y_bottom = min(y2_1, y2_2)
            
            if x_right < x_left or y_bottom < y_top:
                return 0.0
            
            intersection = (x_right - x_left) * (y_bottom - y_top)
            box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
            box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
            union = box1_area + box2_area - intersection
            
            return intersection / union if union > 0 else 0.0
        
        keep = []
        for weapon in weapons:
            is_duplicate = False
            for kept in keep:
                iou = calculate_iou(weapon['bbox'], kept['bbox'])
                # More aggressive: consider duplicate if IoU > 0.3 OR same class
                if iou > 0.3 and weapon['class'] == kept['class']:
                    is_duplicate = True
                    break
            if not is_duplicate:
                keep.append(weapon)
        
        print(f"[DEDUPE] Reduced {len(weapons)} weapons to {len(keep)} unique")
        return keep
    
    try:
        print("\n" + "="*60)
        print("STARTING VIDEO PROCESSING")
        print("="*60)
        
        # Get video source
        source_type = config.get('source', 'webcam')
        if source_type == 'webcam':
            video_path = 0
        elif source_type == 'cctv':
            video_path = config.get('sourceUrl', '')
        else:  # video file
            video_path = config.get('sourceFile', '')
        
        print(f"Video source: {video_path}")
        
        # Initialize components
        state['video_source'] = VideoSource(video_path)
        
        # Initialize detector with custom trained gun model
        gun_model_path = 'runs/detect/models/gun_detection/weights/best.pt'
        state['detector'] = Detector(
            person_model_path='models/yolo11n.pt',
            gun_model_path=gun_model_path
        )
        
        state['tracker_memory'] = TrackerMemory()
        state['behaviour_engine'] = BehaviourEngine(
            restricted_zone=config.get('restrictedZone'),
            crowd_threshold=config.get('crowdThreshold', 5)
        )
        state['ui_overlay'] = UIOverlay(restricted_zone=config.get('restrictedZone'))
        
        print("✓ All components initialized")
        
        frame_count = 0
        fps_start = time.time()
        screenshot_captured = set()
        
        # Persistent counters - these accumulate and don't reset
        max_weapons_detected = 0  # Track maximum weapons seen
        max_threats_detected = 0  # Track maximum threats seen
        
        # Weapon memory - remember weapons for longer (5 seconds)
        weapon_memory = []  # List of (frame_number, weapon_detection)
        weapon_memory_timeout = 150  # Remember for 150 frames (~5 seconds at 30fps)
        
        while state['running']:
            frame = state['video_source'].read()
            
            if frame is None:
                print("Video ended")
                socketio.emit('video_ended', {'message': 'Video playback complete'})
                break
            
            frame_count += 1
            
            # Detection
            person_detections = state['detector'].detect_persons(frame)
            
            # Detect weapons EVERY FRAME for maximum detection (especially for guns)
            weapon_detections = []
            new_weapons = state['detector'].detect_weapons(frame)
            
            if len(new_weapons) > 0:
                print(f"[FRAME {frame_count}] Weapons detected: {len(new_weapons)}")
                # Replace memory with new detections (don't accumulate)
                weapon_memory = [(frame_count, w) for w in new_weapons]
            else:
                # Clean up old weapon memory if no new detections
                weapon_memory = [(f, w) for f, w in weapon_memory if frame_count - f < weapon_memory_timeout]
            
            # Detect suspicious items (every 5 frames)
            suspicious_items = []
            if frame_count % 5 == 0:
                suspicious_items = state['detector'].detect_suspicious_items(frame)
                if len(suspicious_items) > 0:
                    print(f"[FRAME {frame_count}] Suspicious items detected: {len(suspicious_items)}")
            
            # Get unique weapons from memory using NMS
            if len(weapon_memory) > 0:
                all_weapons = [w for f, w in weapon_memory]
                # Apply aggressive NMS to deduplicate weapons in memory
                weapon_detections = _deduplicate_weapons(all_weapons)
            else:
                weapon_detections = []
            
            # Update max weapons counter (persistent) - only update if we have actual detections
            if len(weapon_detections) > 0 and len(weapon_detections) > max_weapons_detected:
                max_weapons_detected = len(weapon_detections)
                print(f"[PERSISTENT] Max weapons updated: {max_weapons_detected}")
            
            # Tracking and behavior
            state['tracker_memory'].update(person_detections, frame_count)
            tracked_persons = state['tracker_memory'].get_all()
            
            behaviour_scores = state['behaviour_engine'].calculate_scores(
                tracked_persons,
                weapon_detections,
                frame.shape,
                suspicious_items  # Add suspicious items parameter
            )
            
            # Draw overlays
            state['ui_overlay'].draw(frame, tracked_persons, behaviour_scores)
            
            # Calculate FPS
            fps = frame_count / (time.time() - fps_start) if time.time() > fps_start else 0
            state['ui_overlay'].draw_fps(frame, fps)
            
            # Stats with crowd-based suspicious activity
            threat_count = sum(1 for s in behaviour_scores.values() if s['alert_level'] == 'THREAT')
            suspicious_count = sum(1 for s in behaviour_scores.values() if s['alert_level'] == 'SUSPICIOUS')
            
            # Add suspicious activity for crowds (2 or more people)
            if len(tracked_persons) >= 2:
                suspicious_count = max(suspicious_count, len(tracked_persons) - 1)
            
            stats = {
                'persons': len(tracked_persons),
                'suspicious': suspicious_count,
                'threats': threat_count,
                'weapons': max_weapons_detected,  # Use persistent counter
                'fps': int(fps)
            }
            
            # Check threats and emit alerts
            for track_id, score_data in behaviour_scores.items():
                alert_level = score_data['alert_level']
                score = score_data['score']
                
                # If weapons detected, automatically upgrade to THREAT
                if len(weapon_detections) > 0 and alert_level != 'THREAT':
                    alert_level = 'THREAT'
                    score = max(score, 5)  # Ensure threat level score
                    print(f"[ALERT] Person ID {track_id} upgraded to THREAT due to weapons in scene")
                
                # Always emit alerts for any non-NORMAL level (every 30 frames to avoid spam)
                if alert_level != 'NORMAL' and frame_count % 30 == 0:
                    # Create alert message
                    factors_str = ", ".join(score_data['factors']) if score_data['factors'] else "Multiple factors"
                    if len(weapon_detections) > 0:
                        factors_str += f", {len(weapon_detections)} weapon(s) in scene"
                    alert_msg = f"Person ID {track_id} - {alert_level} (Score: {score:.1f}) - {factors_str}"
                    
                    socketio.emit('alert', {
                        'type': alert_level,
                        'message': alert_msg,
                        'time': datetime.now().strftime("%H:%M:%S"),
                        'person_id': track_id,
                        'score': score
                    })
                    
                    print(f"[ALERT] {alert_level} - Person ID {track_id}, Score: {score:.1f}, Factors: {factors_str}")
                
                # Save screenshot for THREAT level
                if alert_level == 'THREAT' and track_id not in screenshot_captured:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    os.makedirs('screenshots', exist_ok=True)
                    screenshot_path = f"screenshots/threat_id{track_id}_{timestamp}.jpg"
                    cv2.imwrite(screenshot_path, frame)
                    
                    screenshot_captured.add(track_id)
                    print(f"[SCREENSHOT] Saved threat screenshot: {screenshot_path}")
            
            # For crowd situations, always generate alerts
            if len(tracked_persons) >= 2:  # If 2 or more people
                if frame_count % 60 == 0:  # Every 60 frames
                    socketio.emit('alert', {
                        'type': 'SUSPICIOUS',
                        'message': f"Multiple people detected - {len(tracked_persons)} people present",
                        'time': datetime.now().strftime("%H:%M:%S"),
                        'person_id': 0,
                        'score': len(tracked_persons)
                    })
                    print(f"[ALERT] CROWD - {len(tracked_persons)} people detected")
            
            # Recalculate threat count after weapon upgrade
            threat_count = sum(1 for s in behaviour_scores.values() if s['alert_level'] == 'THREAT')
            if len(weapon_detections) > 0:
                threat_count = len(tracked_persons)  # All persons are threats if weapons present
            
            # Update max threats counter (persistent)
            if threat_count > max_threats_detected:
                max_threats_detected = threat_count
                print(f"[PERSISTENT] Max threats updated: {max_threats_detected}")
            
            stats['threats'] = max_threats_detected  # Use persistent counter
            
            # Cleanup (less frequent for better FPS)
            if frame_count % 60 == 0:
                state['tracker_memory'].cleanup(frame_count, timeout=90)
            
            # Encode and emit frame with better compression for faster streaming
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            socketio.emit('frame', {
                'image': frame_base64,
                'stats': stats
            })
            
            time.sleep(0.001)  # Minimal sleep for maximum FPS (~1000 FPS target, actual will be limited by processing)
        
        print("Processing stopped")
        
    except Exception as e:
        print(f"Processing error: {e}")
        import traceback
        traceback.print_exc()
        socketio.emit('error', {'message': str(e)})
    
    finally:
        if state['video_source']:
            state['video_source'].release()
        state['running'] = False

@socketio.on('connect')
def handle_connect():
    print('[WebSocket] Client connected')
    emit('connected', {'status': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('[WebSocket] Client disconnected')

@socketio.on('start_surveillance')
def handle_start(config):
    print('[WebSocket] Start surveillance request')
    try:
        if not state['running']:
            state['running'] = True
            thread = threading.Thread(target=process_video, args=(config,))
            thread.daemon = True
            thread.start()
            state['thread'] = thread
            emit('status', {'status': 'success', 'message': 'Started'})
        else:
            emit('status', {'status': 'error', 'message': 'Already running'})
    except Exception as e:
        emit('status', {'status': 'error', 'message': str(e)})

@socketio.on('stop_surveillance')
def handle_stop():
    print('[WebSocket] Stop surveillance request')
    state['running'] = False
    emit('status', {'status': 'success', 'message': 'Stopped'})

if __name__ == '__main__':
    print("=" * 60)
    print("SMART SURVEILLANCE SYSTEM")
    print("=" * 60)
    print("\nServer starting on http://localhost:5000")
    print("\nFeatures:")
    print("  ✓ Video file upload")
    print("  ✓ Real-time detection")
    print("  ✓ Person tracking")
    print("  ✓ Weapon detection")
    print("  ✓ Behavior analysis")
    print("  ✓ Live video streaming")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
