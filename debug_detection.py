"""
Debug script to test weapon detection on specific videos
"""
import cv2
from detector_roboflow import Detector

print("=" * 60)
print("WEAPON DETECTION DEBUG TEST")
print("=" * 60)

# Initialize detector
print("\n[1/3] Initializing detector...")
detector = Detector(
    'models/yolo11n.pt',
    'qkYj4oT3poy5wf50aKm2',
    'crime-dp3x3/1'
)
print("✓ Detector initialized")

# Test videos
videos = [
    r"C:\Users\11one\OneDrive\Desktop\test 1.mp4",
    r"C:\Users\11one\OneDrive\Desktop\test 2.mp4"
]

for video_path in videos:
    print(f"\n{'='*60}")
    print(f"Testing: {video_path}")
    print('='*60)
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"✗ Could not open video")
        continue
    
    frame_count = 0
    weapon_found = False
    person_count = 0
    
    # Test first 100 frames
    while frame_count < 100:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Test every 10 frames
        if frame_count % 10 == 0:
            # Detect persons
            persons = detector.detect_persons(frame)
            person_count = max(person_count, len(persons))
            
            # Detect weapons
            weapons = detector.detect_weapons(frame)
            
            if len(weapons) > 0:
                weapon_found = True
                print(f"\n[FRAME {frame_count}] WEAPONS DETECTED:")
                for w in weapons:
                    print(f"  - {w['class']}: confidence {w['confidence']:.2f}")
                    print(f"    bbox: {w['bbox']}")
            
            if len(persons) > 0 and frame_count % 30 == 0:
                print(f"[FRAME {frame_count}] Persons: {len(persons)}")
    
    cap.release()
    
    print(f"\nResults for {video_path.split('/')[-1]}:")
    print(f"  Frames tested: {frame_count}")
    print(f"  Max persons detected: {person_count}")
    print(f"  Weapons found: {'YES' if weapon_found else 'NO'}")

print("\n" + "=" * 60)
print("DEBUG TEST COMPLETE")
print("=" * 60)
