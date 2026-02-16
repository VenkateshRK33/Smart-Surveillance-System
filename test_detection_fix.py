"""
Test script to verify person and weapon detection fixes
"""
import cv2
from detector_roboflow import Detector

# Initialize detector
print("Initializing detector...")
detector = Detector(
    'models/yolo11n.pt',
    'qkYj4oT3poy5wf50aKm2',
    'crime-dp3x3/1'
)

# Load test video
video_path = 'uploads/test2.mp4'  # Update with your video path
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"Error: Could not open video {video_path}")
    exit(1)

print(f"Testing video: {video_path}")
print("=" * 60)

frame_count = 0
max_frames = 30  # Test first 30 frames

while frame_count < max_frames:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    
    # Detect persons
    persons = detector.detect_persons(frame)
    
    # Detect weapons (every 3 frames)
    weapons = []
    if frame_count % 3 == 0:
        weapons = detector.detect_weapons(frame)
    
    print(f"\nFrame {frame_count}:")
    print(f"  Persons: {len(persons)}")
    if len(persons) > 0:
        for p in persons:
            bbox = p['bbox']
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            print(f"    - ID {p['track_id']}: {w}x{h} pixels, conf={p['confidence']:.2f}")
    
    print(f"  Weapons: {len(weapons)}")
    if len(weapons) > 0:
        for w in weapons:
            bbox = w['bbox']
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            print(f"    - {w['class']}: {width}x{height} pixels, conf={w['confidence']:.2f}")

cap.release()

print("\n" + "=" * 60)
print("Test complete!")
print("\nExpected results:")
print("  - 1 person detected consistently")
print("  - 1 weapon (bat) detected")
print("  - No duplicate detections")
