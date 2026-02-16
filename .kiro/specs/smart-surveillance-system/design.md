# Design Document

## Overview

The Smart Surveillance System is built using a modular pipeline architecture where each component has a single, well-defined responsibility. The system processes video frames through a sequential pipeline: video input → detection → tracking → behaviour analysis → visual rendering → display output. This design prioritizes real-time performance, maintainability, and clear separation of concerns.

The architecture consists of 6 core Python modules that work together through a main processing loop. Each module exposes simple interfaces and maintains minimal coupling with other components.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   main.py       │  ← Entry point & orchestration
└────────┬────────┘
         │
         ├──→ VideoSource (video_input.py)
         │    └─ Provides frames
         │
         ├──→ Detector (detector.py)
         │    ├─ Person detection (YOLO11)
         │    └─ Weapon detection (Roboflow)
         │
         ├──→ TrackerMemory (tracker_memory.py)
         │    └─ Maintains per-person state
         │
         ├──→ BehaviourEngine (behaviour_engine.py)
         │    └─ Calculates scores & alert levels
         │
         └──→ UIOverlay (ui_overlay.py)
              └─ Renders visual elements
```

### Processing Pipeline Flow

```
1. VideoSource.read() → frame
2. Detector.detect_persons(frame) → person_detections
3. Detector.detect_weapons(frame) → weapon_detections [every 2-3 frames]
4. TrackerMemory.update(person_detections) → tracked_persons
5. BehaviourEngine.calculate_scores(tracked_persons, weapon_detections) → scores
6. UIOverlay.draw(frame, tracked_persons, scores) → annotated_frame
7. Display annotated_frame
8. If THREAT detected → save screenshot
```

## Components and Interfaces

### 1. main.py

**Responsibility:** Application entry point and main processing loop orchestration

**Key Functions:**
- `main()`: Initializes all components and runs the main loop

**Main Loop Logic:**
```python
while True:
    frame = video_source.read()
    if frame is None: break
    
    persons = detector.detect_persons(frame)
    weapons = detector.detect_weapons(frame) if frame_count % 3 == 0 else []
    
    tracker_memory.update(persons)
    scores = behaviour_engine.calculate_scores(tracker_memory.get_all(), weapons, frame.shape)
    
    ui_overlay.draw(frame, tracker_memory.get_all(), scores)
    
    if any(score['alert_level'] == 'THREAT' for score in scores.values()):
        save_screenshot(frame)
    
    cv2.imshow('Surveillance', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break
```

**Configuration:**
- Video source (webcam index or file path)
- Restricted zone coordinates
- Model paths

---

### 2. video_input.py

**Responsibility:** Abstract video source handling for webcam and video files

**Class: VideoSource**

**Interface:**
```python
class VideoSource:
    def __init__(self, source):
        """
        Args:
            source: int (webcam index) or str (video file path)
        """
        
    def read(self):
        """
        Returns:
            frame: numpy array (BGR image) or None if source ended
        """
        
    def release(self):
        """Release video capture resources"""
```

**Implementation Details:**
- Uses `cv2.VideoCapture` internally
- Validates source availability on initialization
- Returns None when video ends or source unavailable

---

### 3. detector.py

**Responsibility:** AI-based detection using YOLO models

**Class: Detector**

**Interface:**
```python
class Detector:
    def __init__(self, person_model_path, weapon_model_path):
        """
        Args:
            person_model_path: Path to YOLO11 model (yolo11n.pt)
            weapon_model_path: Path to Roboflow model (best.pt)
        """
        
    def detect_persons(self, frame):
        """
        Args:
            frame: numpy array (BGR image)
        Returns:
            List of dicts: [
                {
                    'track_id': int,
                    'bbox': (x1, y1, x2, y2),
                    'confidence': float
                }
            ]
        """
        
    def detect_weapons(self, frame):
        """
        Args:
            frame: numpy array (BGR image)
        Returns:
            List of dicts: [
                {
                    'bbox': (x1, y1, x2, y2),
                    'class': str ('knife' or 'gun'),
                    'confidence': float
                }
            ]
        """
```

**Implementation Details:**
- Load YOLO11 model with tracking enabled: `YOLO(person_model_path)`
- Use `model.track()` for person detection to get tracking IDs
- Load Roboflow weapon model separately
- Use `model.predict()` for weapon detection
- Parse results to extract bounding boxes, classes, and tracking IDs
- Person detection runs every frame
- Weapon detection runs every 2-3 frames for performance

---

### 4. tracker_memory.py

**Responsibility:** Maintain per-person tracking state and history

**Class: TrackerMemory**

**Interface:**
```python
class TrackerMemory:
    def __init__(self):
        """Initialize empty memory storage"""
        
    def update(self, person_detections):
        """
        Args:
            person_detections: List of person detection dicts
        """
        
    def get(self, track_id):
        """
        Args:
            track_id: int
        Returns:
            dict: {
                'track_id': int,
                'first_seen_time': float (timestamp),
                'last_position': (x, y),
                'bbox': (x1, y1, x2, y2),
                'last_seen_frame': int
            } or None
        """
        
    def get_all(self):
        """
        Returns:
            dict: {track_id: person_data, ...}
        """
        
    def cleanup(self, current_frame_count, timeout=90):
        """
        Remove persons not seen for timeout frames (3 seconds at 30fps)
        Args:
            current_frame_count: int
            timeout: int (frames)
        """
```

**Data Structure:**
```python
self.memory = {
    track_id: {
        'track_id': int,
        'first_seen_time': float,
        'last_position': (x, y),
        'bbox': (x1, y1, x2, y2),
        'last_seen_frame': int
    }
}
```

**Implementation Details:**
- Use `time.time()` for timestamps
- Calculate center position from bbox: `((x1+x2)/2, (y1+y2)/2)`
- Update existing entries or create new ones
- Call cleanup periodically to remove stale tracks

---

### 5. behaviour_engine.py

**Responsibility:** Calculate behaviour scores and determine alert levels

**Class: BehaviourEngine**

**Interface:**
```python
class BehaviourEngine:
    def __init__(self, restricted_zone=None, crowd_threshold=5):
        """
        Args:
            restricted_zone: dict {'x1': int, 'y1': int, 'x2': int, 'y2': int} or None
            crowd_threshold: int (number of people to trigger crowd condition)
        """
        
    def calculate_scores(self, tracked_persons, weapon_detections, frame_shape):
        """
        Args:
            tracked_persons: dict from TrackerMemory.get_all()
            weapon_detections: list of weapon detection dicts
            frame_shape: tuple (height, width, channels)
        Returns:
            dict: {
                track_id: {
                    'score': int,
                    'alert_level': str ('NORMAL', 'SUSPICIOUS', 'THREAT'),
                    'stay_duration': float (seconds),
                    'factors': list of str (reasons for score)
                }
            }
        """
```

**Scoring Logic:**

| Factor | Condition | Points |
|--------|-----------|--------|
| Long stay | Stay duration > 30 seconds | +1 |
| Restricted zone | Person center in zone | +2 |
| Low movement | Position change < 20 pixels over 5 seconds | +1 |
| Crowd | Total persons > threshold | +1 per person |
| Weapon detected | Weapon bbox overlaps person bbox | +5 |

**Alert Level Classification:**
- Score 0-2: NORMAL
- Score 3-4: SUSPICIOUS
- Score 5+: THREAT

**Implementation Details:**
- Calculate stay duration: `current_time - first_seen_time`
- Check restricted zone: person center (x, y) within zone bounds
- Detect low movement: compare current position with position from 5 seconds ago
- Weapon association: check IoU (Intersection over Union) between weapon and person bboxes
- Return factors list for debugging/display purposes

---

### 6. ui_overlay.py

**Responsibility:** Render all visual elements on the frame

**Class: UIOverlay**

**Interface:**
```python
class UIOverlay:
    def __init__(self, restricted_zone=None):
        """
        Args:
            restricted_zone: dict {'x1': int, 'y1': int, 'x2': int, 'y2': int} or None
        """
        
    def draw(self, frame, tracked_persons, behaviour_scores):
        """
        Args:
            frame: numpy array (BGR image) - modified in place
            tracked_persons: dict from TrackerMemory.get_all()
            behaviour_scores: dict from BehaviourEngine.calculate_scores()
        """
        
    def draw_fps(self, frame, fps):
        """
        Args:
            frame: numpy array (BGR image)
            fps: float
        """
```

**Visual Elements:**

1. **Bounding Boxes:**
   - Color based on alert level: Green (NORMAL), Yellow (SUSPICIOUS), Red (THREAT)
   - Thickness: 2 pixels
   - Draw using `cv2.rectangle()`

2. **Text Labels (above bbox):**
   - Line 1: `ID: {track_id}`
   - Line 2: `Score: {score} | {alert_level}`
   - Line 3: `Time: {stay_duration}s`
   - Font: `cv2.FONT_HERSHEY_SIMPLEX`
   - Size: 0.5
   - Color: Same as bbox color

3. **Restricted Zone:**
   - Draw rectangle with dashed or solid line
   - Color: Blue (255, 0, 0)
   - Thickness: 2 pixels
   - Semi-transparent overlay using `cv2.addWeighted()` (optional)

4. **FPS Counter:**
   - Top-left corner
   - Format: `FPS: {fps:.1f}`
   - Color: White (255, 255, 255)
   - Background: Black rectangle for visibility

**Implementation Details:**
- All drawing operations modify frame in place
- Use `cv2.putText()` for text rendering
- Calculate text position relative to bbox coordinates
- Ensure text doesn't go off-frame (boundary checks)

## Data Models

### Person Detection
```python
{
    'track_id': int,           # Unique ID from YOLO tracking
    'bbox': (x1, y1, x2, y2),  # Bounding box coordinates
    'confidence': float        # Detection confidence (0-1)
}
```

### Weapon Detection
```python
{
    'bbox': (x1, y1, x2, y2),  # Bounding box coordinates
    'class': str,              # 'knife' or 'gun'
    'confidence': float        # Detection confidence (0-1)
}
```

### Tracked Person (Memory)
```python
{
    'track_id': int,
    'first_seen_time': float,      # Unix timestamp
    'last_position': (x, y),       # Center coordinates
    'bbox': (x1, y1, x2, y2),
    'last_seen_frame': int         # Frame number
}
```

### Behaviour Score
```python
{
    'score': int,                  # Total behaviour score
    'alert_level': str,            # 'NORMAL', 'SUSPICIOUS', 'THREAT'
    'stay_duration': float,        # Seconds
    'factors': [str]               # List of contributing factors
}
```

### Configuration
```python
{
    'video_source': int | str,     # 0 for webcam, or file path
    'person_model': str,           # Path to yolo11n.pt
    'weapon_model': str,           # Path to best.pt
    'restricted_zone': {           # Optional
        'x1': int, 'y1': int,
        'x2': int, 'y2': int
    },
    'crowd_threshold': int,        # Default: 5
    'screenshot_dir': str          # Default: 'screenshots/'
}
```

## Error Handling

### Video Source Errors
- **Issue:** Camera not available or video file not found
- **Handling:** Print error message and exit gracefully
- **Implementation:** Check `cap.isOpened()` after initialization

### Model Loading Errors
- **Issue:** Model files not found or corrupted
- **Handling:** Print error with model path and exit
- **Implementation:** Try-except block around YOLO model loading

### Detection Failures
- **Issue:** YOLO returns no results or malformed data
- **Handling:** Return empty list, continue processing
- **Implementation:** Check if results exist before parsing

### Frame Processing Errors
- **Issue:** Frame is None or invalid
- **Handling:** Skip frame and continue loop
- **Implementation:** Check `if frame is None: continue`

### Screenshot Save Errors
- **Issue:** Unable to write screenshot to disk
- **Handling:** Log error but continue surveillance
- **Implementation:** Try-except around `cv2.imwrite()`

## Testing Strategy

### Component Testing

**1. VideoSource Testing:**
- Test webcam initialization (device 0)
- Test video file loading
- Test frame reading and None return on end
- Test release functionality

**2. Detector Testing:**
- Test person detection with sample frame
- Test weapon detection with sample frame
- Verify tracking IDs are consistent across frames
- Test with frames containing no persons/weapons

**3. TrackerMemory Testing:**
- Test adding new person
- Test updating existing person
- Test cleanup of stale tracks
- Test get and get_all methods

**4. BehaviourEngine Testing:**
- Test score calculation for each factor individually
- Test alert level classification
- Test weapon-person association logic
- Test restricted zone detection

**5. UIOverlay Testing:**
- Test bounding box colors for each alert level
- Test text rendering
- Test FPS counter display
- Test restricted zone visualization

### Integration Testing

**End-to-End Test:**
1. Load test video with known persons
2. Verify persons are detected and tracked
3. Verify behaviour scores increase over time
4. Verify alert levels change appropriately
5. Verify screenshot capture on THREAT
6. Verify clean exit on 'q' key

**Performance Test:**
- Measure FPS with different video sources
- Verify minimum 15 FPS on target hardware (RTX 3050)
- Test with multiple persons (5+) in frame
- Test weapon detection performance impact

### Manual Testing Scenarios

1. **Normal Surveillance:** Person walks through frame quickly
2. **Loitering:** Person stays in frame for 60+ seconds
3. **Restricted Zone:** Person enters defined zone
4. **Weapon Detection:** Show knife/gun to camera
5. **Crowd:** Multiple people in frame simultaneously
6. **Exit:** Press 'q' and verify clean shutdown

## Performance Considerations

### Optimization Strategies

1. **Weapon Detection Throttling:**
   - Run every 2-3 frames instead of every frame
   - Reduces computational load by 60-70%
   - Acceptable latency for weapon detection

2. **Model Selection:**
   - Use YOLO11 Nano (yolo11n.pt) for person detection
   - Smallest model with acceptable accuracy
   - Optimized for real-time performance

3. **Frame Processing:**
   - No frame resizing unless necessary
   - Direct processing of camera resolution
   - Minimize memory copies

4. **Memory Management:**
   - Cleanup stale tracks every 90 frames
   - Limit memory growth over long surveillance sessions
   - No history storage beyond current state

### Expected Performance

- **Target FPS:** 15-30 FPS
- **Hardware:** NVIDIA RTX 3050 or equivalent
- **Resolution:** 640x480 to 1920x1080
- **Max Persons:** 10-15 simultaneous tracks

## Deployment Considerations

### Directory Structure
```
SmartSurveillance/
├── main.py
├── video_input.py
├── detector.py
├── tracker_memory.py
├── behaviour_engine.py
├── ui_overlay.py
├── models/
│   ├── yolo11n.pt
│   └── best.pt
└── screenshots/
    └── (auto-generated)
```

### Dependencies
```
ultralytics>=8.0.0
opencv-python>=4.8.0
numpy>=1.24.0
```

### Configuration
- All configuration in main.py
- No external config files needed
- Hardcoded defaults with inline comments

### Running the System
```bash
python main.py
```

### Exit
- Press 'q' key to exit
- System releases resources automatically
