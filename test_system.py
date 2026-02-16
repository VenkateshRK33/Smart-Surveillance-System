"""
Test script to verify all components of the Smart Surveillance System
"""
import cv2
import sys

print("=" * 60)
print("SMART SURVEILLANCE SYSTEM - COMPONENT TEST")
print("=" * 60)

# Test 1: Import all modules
print("\n[TEST 1] Importing modules...")
try:
    from video_input import VideoSource
    from detector import Detector
    from tracker_memory import TrackerMemory
    from behaviour_engine import BehaviourEngine
    from ui_overlay import UIOverlay
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Check models exist
print("\n[TEST 2] Checking model files...")
import os
person_model = 'models/yolo11n.pt'

if os.path.exists(person_model):
    print(f"✓ Person detection model found: {person_model}")
else:
    print(f"✗ Person detection model missing: {person_model}")
    sys.exit(1)

print("✓ Weapon detection: Using Roboflow hosted API")

# Test 3: Initialize Detector
print("\n[TEST 3] Loading detection models...")
try:
    from detector_roboflow import Detector
    detector = Detector(
        person_model,
        'qkYj4oT3poy5wf50aKm2',
        'weapon-c6q7e/1'
    )
    print("✓ Detector initialized successfully")
except Exception as e:
    print(f"✗ Detector initialization failed: {e}")
    sys.exit(1)

# Test 4: Initialize other components
print("\n[TEST 4] Initializing other components...")
try:
    tracker_memory = TrackerMemory()
    print("✓ TrackerMemory initialized")
    
    behaviour_engine = BehaviourEngine(restricted_zone=None, crowd_threshold=5)
    print("✓ BehaviourEngine initialized")
    
    ui_overlay = UIOverlay(restricted_zone=None)
    print("✓ UIOverlay initialized")
except Exception as e:
    print(f"✗ Component initialization failed: {e}")
    sys.exit(1)

# Test 5: Check webcam availability
print("\n[TEST 5] Checking webcam availability...")
try:
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✓ Webcam accessible (Resolution: {frame.shape[1]}x{frame.shape[0]})")
        else:
            print("⚠ Webcam opened but cannot read frames")
        cap.release()
    else:
        print("⚠ Webcam not accessible (you can still use video files)")
except Exception as e:
    print(f"⚠ Webcam test failed: {e}")

print("\n" + "=" * 60)
print("COMPONENT TEST COMPLETED SUCCESSFULLY!")
print("=" * 60)
print("\nYou can now run the full system with: python main.py")
print("Press 'q' to exit the surveillance window")
