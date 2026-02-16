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
        
        state['detector'] = Detector(
            'models/yolo11n.pt',
            'qkYj4oT3poy5wf50aKm2',
            'crime-dp3x3/1'  # New crime detection model
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
        
        while state['running']:
            frame = state['video_source'].read()
            
            if frame is None:
                print("Video ended")
                socketio.emit('video_ended', {'message': 'Video playback complete'})
                break
            
            frame_count += 1
            
            # Detection
            person_detections = state['detector'].detect_persons(frame)
            
            # Detect weapons (every 5 frames instead of 2 to improve FPS)
            weapon_detections = []
            if frame_count % 5 == 0:
                weapon_detections = state['detector'].detect_weapons(frame)
                if len(weapon_detections) > 0:
                    print(f"[FRAME {frame_count}] Weapons detected: {len(weapon_detections)}")
            
            # Tracking and behavior
            state['tracker_memory'].update(person_detections, frame_count)
            tracked_persons = state['tracker_memory'].get_all()
            
            behaviour_scores = state['behaviour_engine'].calculate_scores(
                tracked_persons,
                weapon_detections,
                frame.shape
            )
            
            # Draw overlays
            state['ui_overlay'].draw(frame, tracked_persons, behaviour_scores)
            
            # Calculate FPS
            fps = frame_count / (time.time() - fps_start) if time.time() > fps_start else 0
            state['ui_overlay'].draw_fps(frame, fps)
            
            # Stats
            threat_count = sum(1 for s in behaviour_scores.values() if s['alert_level'] == 'THREAT')
            suspicious_count = sum(1 for s in behaviour_scores.values() if s['alert_level'] == 'SUSPICIOUS')
            
            stats = {
                'persons': len(tracked_persons),
                'suspicious': suspicious_count,
                'threats': threat_count,
                'weapons': len(weapon_detections),
                'fps': int(fps)
            }
            
            # Check threats and emit alerts
            for track_id, score_data in behaviour_scores.items():
                alert_level = score_data['alert_level']
                score = score_data['score']
                
                # Always emit alerts for any non-NORMAL level (every 30 frames to avoid spam)
                if alert_level != 'NORMAL' and frame_count % 30 == 0:
                    # Create alert message
                    factors_str = ", ".join(score_data['factors']) if score_data['factors'] else "Multiple factors"
                    alert_msg = f"Person ID {track_id} - {alert_level} (Score: {score:.1f}) - {factors_str}"
                    
                    socketio.emit('alert', {
                        'type': alert_level,
                        'message': alert_msg,
                        'time': datetime.now().strftime("%H:%M:%S"),
                        'person_id': track_id,
                        'score': score
                    })
                    
                    print(f"[ALERT] {alert_level} - Person ID {track_id}, Score: {score:.1f}, Factors: {factors_str}")
                
                # For crowd situations, always generate alerts
                if len(tracked_persons) > 3:  # If more than 3 people
                    if frame_count % 60 == 0:  # Every 60 frames
                        socketio.emit('alert', {
                            'type': 'SUSPICIOUS',
                            'message': f"Crowd detected - {len(tracked_persons)} people present",
                            'time': datetime.now().strftime("%H:%M:%S"),
                            'person_id': 0,
                            'score': len(tracked_persons)
                        })
                        print(f"[ALERT] CROWD - {len(tracked_persons)} people detected")
                
                # Save screenshot for THREAT level
                if alert_level == 'THREAT' and track_id not in screenshot_captured:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    os.makedirs('screenshots', exist_ok=True)
                    screenshot_path = f"screenshots/threat_id{track_id}_{timestamp}.jpg"
                    cv2.imwrite(screenshot_path, frame)
                    
                    screenshot_captured.add(track_id)
                    print(f"[SCREENSHOT] Saved threat screenshot: {screenshot_path}")
            
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
            
            time.sleep(0.015)  # ~60 FPS target
        
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
