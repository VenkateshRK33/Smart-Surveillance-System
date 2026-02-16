"""
Direct video test - bypassing web upload
"""
import cv2
import time
from datetime import datetime

from video_input import VideoSource
from detector_roboflow import Detector
from tracker_memory import TrackerMemory
from behaviour_engine import BehaviourEngine
from ui_overlay import UIOverlay

# Video file path
VIDEO_PATH = r"C:\Users\11one\OneDrive\Desktop\Watch_Armed_criminal_s_gun_deal_filmed_on_his_own_CCTV_camera_720P.mp4"

print("=" * 60)
print("SMART SURVEILLANCE SYSTEM - DIRECT VIDEO TEST")
print("=" * 60)
print(f"\nVideo: {VIDEO_PATH}")
print("\nInitializing components...")

try:
    # Initialize VideoSource
    video_src = VideoSource(VIDEO_PATH)
    print("✓ Video source loaded")
    
    # Initialize Detector
    detector = Detector(
        'models/yolo11n.pt',
        'qkYj4oT3poy5wf50aKm2',
        'weapon-c6q7e/1'
    )
    print("✓ Detector initialized")
    
    # Initialize other components
    tracker_memory = TrackerMemory()
    behaviour_engine = BehaviourEngine(restricted_zone=None, crowd_threshold=5)
    ui_overlay = UIOverlay(restricted_zone=None)
    print("✓ All components ready")
    
    print("\n" + "=" * 60)
    print("STARTING ANALYSIS")
    print("=" * 60)
    print("Press 'q' to quit\n")
    
    frame_count = 0
    fps_start_time = time.time()
    screenshot_captured = set()
    
    while True:
        frame = video_src.read()
        
        if frame is None:
            print("\n[INFO] Video ended")
            break
        
        frame_count += 1
        
        # Detect persons
        person_detections = detector.detect_persons(frame)
        
        # Detect weapons (every 3 frames)
        weapon_detections = []
        if frame_count % 3 == 0:
            weapon_detections = detector.detect_weapons(frame)
        
        # Update tracker
        tracker_memory.update(person_detections, frame_count)
        tracked_persons = tracker_memory.get_all()
        
        # Calculate behavior scores
        behaviour_scores = behaviour_engine.calculate_scores(
            tracked_persons,
            weapon_detections,
            frame.shape
        )
        
        # Draw overlays
        ui_overlay.draw(frame, tracked_persons, behaviour_scores)
        
        # Calculate FPS
        fps_elapsed = time.time() - fps_start_time
        fps = frame_count / fps_elapsed if fps_elapsed > 0 else 0
        ui_overlay.draw_fps(frame, fps)
        
        # Print stats every 30 frames
        if frame_count % 30 == 0:
            threat_count = sum(1 for s in behaviour_scores.values() if s['alert_level'] == 'THREAT')
            print(f"Frame {frame_count}: Persons={len(tracked_persons)}, Weapons={len(weapon_detections)}, Threats={threat_count}, FPS={int(fps)}")
            
            # Cleanup
            tracker_memory.cleanup(frame_count, timeout=90)
        
        # Check for threats and save screenshots
        for track_id, score_data in behaviour_scores.items():
            if score_data['alert_level'] == 'THREAT':
                if track_id not in screenshot_captured:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f"screenshots/threat_id{track_id}_{timestamp}.jpg"
                    
                    import os
                    os.makedirs('screenshots', exist_ok=True)
                    cv2.imwrite(screenshot_path, frame)
                    
                    print(f"[ALERT] THREAT DETECTED! Screenshot saved: {screenshot_path}")
                    screenshot_captured.add(track_id)
        
        # Display frame
        cv2.imshow('Smart Surveillance System', frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n[INFO] Stopped by user")
            break
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Total frames processed: {frame_count}")
    print(f"Average FPS: {int(fps)}")
    print(f"Threats detected: {len(screenshot_captured)}")
    print(f"Screenshots saved: screenshots/")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

finally:
    # Cleanup
    try:
        video_src.release()
        cv2.destroyAllWindows()
    except:
        pass
    
    print("\n[INFO] Cleanup complete")
