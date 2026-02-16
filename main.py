"""
Smart Surveillance System - Main Entry Point

Real-time computer vision application for detecting and tracking suspicious behaviour
in video streams from webcams or CCTV footage.

Features:
- Person detection and tracking using YOLO11
- Weapon detection using Roboflow-trained model
- Behaviour scoring based on multiple suspicious factors
- Visual alerts with color-coded bounding boxes
- Automatic screenshot capture for threat-level events
"""

import cv2
import os
import time
from datetime import datetime

from video_input import VideoSource
from detector_roboflow import Detector
from tracker_memory import TrackerMemory
from behaviour_engine import BehaviourEngine
from ui_overlay import UIOverlay


def main():
    """
    Main entry point for the Smart Surveillance System.
    
    Initializes all components and runs the main processing loop.
    """
    
    # ========== CONFIGURATION ==========
    
    # Video source: 0 for webcam, or path to video file
    video_source = 0  # Change to video file path for testing: 'path/to/video.mp4'
    
    # Model paths and API configuration
    person_model_path = 'models/yolo11n.pt'
    
    # Roboflow weapon detection configuration
    roboflow_api_key = 'qkYj4oT3poy5wf50aKm2'
    roboflow_model_id = 'weapon-c6q7e/1'  # SwifEye weapon detection model
    
    # Restricted zone coordinates (optional)
    # Set to None to disable, or define as: {'x1': 100, 'y1': 100, 'x2': 500, 'y2': 400}
    restricted_zone = None
    
    # Crowd threshold (number of people that triggers crowd condition)
    crowd_threshold = 5
    
    # Screenshot directory
    screenshot_dir = 'screenshots'
    
    # ========== INITIALIZATION ==========
    
    print("[INFO] Initializing Smart Surveillance System...")
    
    # Create screenshots directory if it doesn't exist
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
        print(f"[INFO] Created screenshots directory: {screenshot_dir}")
    
    try:
        # Initialize VideoSource
        print(f"[INFO] Initializing video source: {video_source}")
        video_src = VideoSource(video_source)
        
        # Initialize Detector with model paths and Roboflow API
        print("[INFO] Loading detection models...")
        detector = Detector(person_model_path, roboflow_api_key, roboflow_model_id)
        
        # Initialize TrackerMemory
        tracker_memory = TrackerMemory()
        print("[INFO] Initialized tracker memory")
        
        # Initialize BehaviourEngine with configuration
        behaviour_engine = BehaviourEngine(
            restricted_zone=restricted_zone,
            crowd_threshold=crowd_threshold
        )
        print("[INFO] Initialized behaviour engine")
        
        # Initialize UIOverlay with restricted zone
        ui_overlay = UIOverlay(restricted_zone=restricted_zone)
        print("[INFO] Initialized UI overlay")
        
        print("[INFO] All components initialized successfully")
        print("[INFO] Starting surveillance... Press 'q' to exit")
        
    except Exception as e:
        print(f"[ERROR] Initialization failed: {str(e)}")
        return

    # ========== MAIN PROCESSING LOOP ==========
    
    frame_count = 0
    fps_start_time = time.time()
    fps = 0
    
    # Track which persons have had screenshots captured to avoid duplicates
    screenshot_captured = set()
    
    try:
        while True:
            # Read frame from VideoSource
            frame = video_src.read()
            
            # Break if video ends or source unavailable
            if frame is None:
                print("[INFO] Video source ended or unavailable")
                break
            
            frame_count += 1
            
            # Detect persons on every frame
            person_detections = detector.detect_persons(frame)
            
            # Detect weapons every 2-3 frames (use frame counter modulo 3)
            weapon_detections = []
            if frame_count % 3 == 0:
                weapon_detections = detector.detect_weapons(frame)
            
            # Update TrackerMemory with person detections
            tracker_memory.update(person_detections, frame_count)
            
            # Get all tracked persons
            tracked_persons = tracker_memory.get_all()
            
            # Calculate behaviour scores using BehaviourEngine
            behaviour_scores = behaviour_engine.calculate_scores(
                tracked_persons,
                weapon_detections,
                frame.shape
            )
            
            # Draw UI overlays on frame
            ui_overlay.draw(frame, tracked_persons, behaviour_scores)
            
            # Calculate and display FPS
            fps_elapsed = time.time() - fps_start_time
            if fps_elapsed > 0:
                fps = frame_count / fps_elapsed
            ui_overlay.draw_fps(frame, fps)
            
            # ========== SCREENSHOT CAPTURE ==========
            
            # Check if any person has alert_level 'THREAT'
            for track_id, score_data in behaviour_scores.items():
                if score_data['alert_level'] == 'THREAT':
                    # Only capture one screenshot per person per THREAT event
                    if track_id not in screenshot_captured:
                        # Generate timestamp filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_filename = f"threat_id{track_id}_{timestamp}.jpg"
                        screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
                        
                        # Save screenshot using cv2.imwrite()
                        success = cv2.imwrite(screenshot_path, frame)
                        
                        if success:
                            print(f"[ALERT] THREAT detected! Screenshot saved: {screenshot_filename}")
                            screenshot_captured.add(track_id)
                        else:
                            print(f"[ERROR] Failed to save screenshot: {screenshot_path}")
            
            # ========== CLEANUP ==========
            
            # Call TrackerMemory.cleanup() periodically (every 30 frames)
            if frame_count % 30 == 0:
                tracker_memory.cleanup(frame_count, timeout=90)
            
            # ========== DISPLAY ==========
            
            # Display frame using cv2.imshow()
            cv2.imshow('Smart Surveillance System', frame)
            
            # Check for 'q' key press to exit loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[INFO] Exit requested by user")
                break
    
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
    
    except Exception as e:
        print(f"[ERROR] Processing error: {str(e)}")
    
    finally:
        # ========== EXIT HANDLING ==========
        
        print("[INFO] Shutting down...")
        
        # Release VideoSource
        video_src.release()
        print("[INFO] Video source released")
        
        # Destroy all OpenCV windows
        cv2.destroyAllWindows()
        print("[INFO] All windows closed")
        
        print("[INFO] Surveillance system terminated")


if __name__ == "__main__":
    main()
