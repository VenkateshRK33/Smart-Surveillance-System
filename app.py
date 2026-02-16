"""
Smart Surveillance System - Integrated Web Application
Flask backend with real-time video streaming and detection
"""
import os
import cv2
import base64
import json
import threading
from flask import Flask, render_template, send_from_directory, request, jsonify, Response
from flask_socketio import SocketIO, emit
import numpy as np
from datetime import datetime

from video_input import VideoSource
from detector_roboflow import Detector
from tracker_memory import TrackerMemory
from behaviour_engine import BehaviourEngine
from ui_overlay import UIOverlay

app = Flask(__name__, static_folder='web', template_folder='web')
app.config['SECRET_KEY'] = 'smart-surveillance-secret'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=500 * 1024 * 1024)

# Global state
surveillance_state = {
    'running': False,
    'video_source': None,
    'detector': None,
    'tracker_memory': None,
    'behaviour_engine': None,
    'ui_overlay': None,
    'config': {},
    'stats': {
        'persons': 0,
        'threats': 0,
        'weapons': 0,
        'fps': 0
    },
    'thread': None
}

# Routes
@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_video():
    """Handle video file upload"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
    
    try:
        print("[INFO] Upload request received")
        print(f"[INFO] Request method: {request.method}")
        print(f"[INFO] Content-Type: {request.content_type}")
        print(f"[INFO] Files in request: {list(request.files.keys())}")
        
        if 'video' not in request.files:
            print("[ERROR] No video file in request")
            return jsonify({'status': 'error', 'message': 'No video file'}), 400
        
        file = request.files['video']
        print(f"[INFO] File received: {file.filename}")
        
        if file.filename == '':
            print("[ERROR] Empty filename")
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        # Save uploaded file
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, file.filename)
        print(f"[INFO] Saving to: {filepath}")
        file.save(filepath)
        print(f"[INFO] File saved successfully")
        
        response = jsonify({
            'status': 'success',
            'message': 'File uploaded',
            'filepath': filepath
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    
    except Exception as e:
        print(f"[ERROR] Upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_surveillance():
    """Start surveillance with given configuration"""
    try:
        config = request.json
        surveillance_state['config'] = config
        
        # Initialize components
        init_surveillance(config)
        
        # Start processing thread
        if not surveillance_state['running']:
            surveillance_state['running'] = True
            thread = threading.Thread(target=process_video_stream)
            thread.daemon = True
            thread.start()
            surveillance_state['thread'] = thread
        
        return jsonify({'status': 'success', 'message': 'Surveillance started'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_surveillance():
    """Stop surveillance"""
    try:
        surveillance_state['running'] = False
        
        # Release resources
        if surveillance_state['video_source']:
            surveillance_state['video_source'].release()
            surveillance_state['video_source'] = None
        
        # Reset stats
        surveillance_state['stats'] = {
            'persons': 0,
            'threats': 0,
            'weapons': 0,
            'fps': 0
        }
        
        return jsonify({'status': 'success', 'message': 'Surveillance stopped'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

def init_surveillance(config):
    """Initialize surveillance components"""
    print("[INFO] Initializing surveillance system...")
    
    # Determine video source
    source_type = config.get('source', 'webcam')
    
    if source_type == 'webcam':
        video_source = 0
    elif source_type == 'cctv':
        video_source = config.get('sourceUrl', '')
    elif source_type == 'video':
        video_source = config.get('sourceFile', '')
    else:
        video_source = 0
    
    print(f"[INFO] Video source: {video_source}")
    
    # Initialize VideoSource
    surveillance_state['video_source'] = VideoSource(video_source)
    
    # Initialize Detector
    person_model_path = 'models/yolo11n.pt'
    roboflow_api_key = 'qkYj4oT3poy5wf50aKm2'
    roboflow_model_id = 'weapon-c6q7e/1'
    
    surveillance_state['detector'] = Detector(
        person_model_path,
        roboflow_api_key,
        roboflow_model_id
    )
    
    # Initialize TrackerMemory
    surveillance_state['tracker_memory'] = TrackerMemory()
    
    # Initialize BehaviourEngine
    restricted_zone = config.get('restrictedZone')
    crowd_threshold = config.get('crowdThreshold', 5)
    
    surveillance_state['behaviour_engine'] = BehaviourEngine(
        restricted_zone=restricted_zone,
        crowd_threshold=crowd_threshold
    )
    
    # Initialize UIOverlay
    surveillance_state['ui_overlay'] = UIOverlay(restricted_zone=restricted_zone)
    
    print("[INFO] Surveillance system initialized")

def process_video_stream():
    """Process video stream and emit frames via WebSocket"""
    import time
    
    frame_count = 0
    fps_start_time = time.time()
    fps = 0
    
    screenshot_captured = set()
    
    print("[INFO] Starting video processing...")
    
    while surveillance_state['running']:
        try:
            # Read frame
            frame = surveillance_state['video_source'].read()
            
            if frame is None:
                print("[WARNING] No frame received")
                break
            
            frame_count += 1
            
            # Detect persons
            person_detections = surveillance_state['detector'].detect_persons(frame)
            
            # Detect weapons (every 3 frames)
            weapon_detections = []
            if frame_count % 3 == 0:
                weapon_detections = surveillance_state['detector'].detect_weapons(frame)
            
            # Update tracker
            surveillance_state['tracker_memory'].update(person_detections, frame_count)
            tracked_persons = surveillance_state['tracker_memory'].get_all()
            
            # Calculate behavior scores
            behaviour_scores = surveillance_state['behaviour_engine'].calculate_scores(
                tracked_persons,
                weapon_detections,
                frame.shape
            )
            
            # Draw UI overlays
            surveillance_state['ui_overlay'].draw(frame, tracked_persons, behaviour_scores)
            
            # Calculate FPS
            fps_elapsed = time.time() - fps_start_time
            if fps_elapsed > 0:
                fps = frame_count / fps_elapsed
            
            surveillance_state['ui_overlay'].draw_fps(frame, fps)
            
            # Update stats
            threat_count = sum(1 for s in behaviour_scores.values() if s['alert_level'] == 'THREAT')
            
            surveillance_state['stats'] = {
                'persons': len(tracked_persons),
                'threats': threat_count,
                'weapons': len(weapon_detections),
                'fps': int(fps)
            }
            
            # Check for threats and emit alerts
            for track_id, score_data in behaviour_scores.items():
                if score_data['alert_level'] == 'THREAT':
                    if track_id not in screenshot_captured:
                        # Save screenshot
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_dir = 'screenshots'
                        os.makedirs(screenshot_dir, exist_ok=True)
                        
                        screenshot_path = os.path.join(
                            screenshot_dir,
                            f"threat_id{track_id}_{timestamp}.jpg"
                        )
                        cv2.imwrite(screenshot_path, frame)
                        
                        # Emit alert
                        socketio.emit('alert', {
                            'type': 'THREAT DETECTED',
                            'message': f'Person ID {track_id} - Threat level detected',
                            'time': datetime.now().strftime("%H:%M:%S"),
                            'screenshot': screenshot_path
                        })
                        
                        screenshot_captured.add(track_id)
            
            # Cleanup tracker memory
            if frame_count % 30 == 0:
                surveillance_state['tracker_memory'].cleanup(frame_count, timeout=90)
            
            # Encode frame to base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Emit frame and stats
            socketio.emit('frame', {
                'image': frame_base64,
                'stats': surveillance_state['stats']
            })
            
            # Control frame rate
            time.sleep(0.033)  # ~30 FPS
            
        except Exception as e:
            print(f"[ERROR] Processing error: {e}")
            break
    
    print("[INFO] Video processing stopped")
    
    # Cleanup
    if surveillance_state['video_source']:
        surveillance_state['video_source'].release()

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('[INFO] Client connected')
    emit('connected', {'status': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('[INFO] Client disconnected')

@socketio.on('start_surveillance')
def handle_start(data):
    """Handle start surveillance request from WebSocket"""
    try:
        surveillance_state['config'] = data
        init_surveillance(data)
        
        if not surveillance_state['running']:
            surveillance_state['running'] = True
            thread = threading.Thread(target=process_video_stream)
            thread.daemon = True
            thread.start()
            surveillance_state['thread'] = thread
        
        emit('status', {'status': 'success', 'message': 'Surveillance started'})
    
    except Exception as e:
        emit('status', {'status': 'error', 'message': str(e)})

@socketio.on('stop_surveillance')
def handle_stop():
    """Handle stop surveillance request"""
    surveillance_state['running'] = False
    emit('status', {'status': 'success', 'message': 'Surveillance stopped'})

if __name__ == '__main__':
    print("=" * 60)
    print("SMART SURVEILLANCE SYSTEM - WEB APPLICATION")
    print("=" * 60)
    print("\nStarting integrated web server...")
    print("Open your browser and navigate to:")
    print("\n  http://localhost:5000")
    print("\nFeatures:")
    print("  ✓ Real-time video streaming")
    print("  ✓ Person detection (YOLO11)")
    print("  ✓ Weapon detection (Roboflow)")
    print("  ✓ Behavior analysis")
    print("  ✓ Live stats and alerts")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
