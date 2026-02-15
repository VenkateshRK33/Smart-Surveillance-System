# Smart Surveillance System – Suspicious Activity Detection (YOLO11 + Roboflow)

## Project Overview

This project is a real-time Smart Surveillance System designed to detect suspicious behaviour using computer vision and object detection.
It processes webcam or CCTV footage, tracks individuals over time, analyses behaviour using a scoring system, and generates alerts when potential threats are detected.

The system uses:

* YOLO11 for person detection and tracking
* Roboflow-trained YOLO model for weapon detection (knife/gun)
* A custom Behaviour Scoring Engine for real-time decision making

This implementation focuses on practical deployment rather than research-level AI.

---

## Core Features

### Real-Time Person Detection and Tracking

* Detects people in live video streams
* Assigns unique tracking IDs using YOLO tracking
* Maintains per-person memory

### Stay Duration Monitoring

* Calculates how long each person remains in view
* Displays live timer near bounding box

### Behaviour Scoring System

Each person receives a dynamic risk score based on behaviour:

* Long stay duration
* Restricted zone presence
* Low movement (loitering)
* Crowd conditions
* Weapon detection

Alert Levels:

* NORMAL
* SUSPICIOUS
* THREAT

### Weapon Detection (Roboflow + YOLO11)

* Detects knife/gun objects using a custom-trained model
* Immediately raises threat-level alerts

### Restricted Zone Monitoring

* Detects if a person enters a defined surveillance area
* Adds behaviour score accordingly

### Crowd Detection

* Raises alerts when number of detected people exceeds threshold

### Visual Alert System

* Color-coded bounding boxes (Green / Yellow / Red)
* Behaviour score display
* Stay duration display
* FPS counter

### Threat Screenshot Capture

* Saves frame automatically when threat-level score is reached

---

## System Architecture

```
Video Input
   ↓
Detection Layer (YOLO11 + Roboflow Model)
   ↓
Tracking & Memory System
   ↓
Behaviour Scoring Engine
   ↓
Alert & UI Overlay
   ↓
Display Output / Screenshot Logs
```

---

## Project Structure

```
SmartSurveillance/

main.py
video_input.py
detector.py
memory.py
behaviour.py
ui.py

models/
   yolo11n.pt
   best.pt
```

---

## File Responsibilities

### main.py

* Entry point of the application
* Controls main loop
* Connects all modules together
* Handles frame pipeline order

Responsibilities:

* Read frame
* Call detectors
* Update memory
* Compute behaviour score
* Render UI

---

### video_input.py

Manages video sources.

Responsibilities:

* Handle webcam or CCTV video file
* Provide frame-by-frame input
* Abstract video reading logic

Key Concept:

```
VideoSource class → read() method returns frame
```

---

### detector.py

Handles all AI detection tasks.

Responsibilities:

* Load YOLO11 person model
* Load Roboflow weapon model
* Perform detection and tracking
* Return structured detection data

Outputs:

* Bounding boxes
* Class IDs
* Tracking IDs

---

### memory.py

Maintains per-person tracking memory.

Responsibilities:

* Store first_seen_time
* Store last position
* Maintain behaviour score
* Remove lost IDs

Example Structure:

```
person_memory[id] = {
   first_seen_time,
   last_position,
   behaviour_score
}
```

---

### behaviour.py

Core decision-making logic.

Responsibilities:

* Calculate behaviour score
* Evaluate suspicious conditions
* Assign alert level

Scoring Example:

* Long stay → +1
* Restricted zone → +2
* Weapon detected → +5

---

### ui.py

Handles all visual rendering.

Responsibilities:

* Draw bounding boxes
* Show ID and timer
* Display score and alert level
* Draw restricted zone
* Show FPS counter

No AI or logic should be written here.

---

## Processing Pipeline (Main Loop Flow)

```
1. Read frame from video_input
2. Detect persons (YOLO11 tracking)
3. Detect weapons (Roboflow model)
4. Update person memory
5. Calculate behaviour score
6. Determine alert level
7. Draw overlays
8. Display frame
```

---

## Requirements

* Python 3.10+
* NVIDIA GPU (RTX 3050 recommended)
* CUDA-enabled PyTorch
* OpenCV
* Ultralytics YOLO

Install:

```
pip install ultralytics opencv-python
```

---

## Running the System

Inside main.py configure source:

```
source = 0           # webcam
source = "video.mp4" # CCTV footage
```

Run:

```
python main.py
```

---

## Performance Notes

* Person detection runs every frame
* Weapon detection runs every 2–3 frames for better FPS
* YOLO11 Nano model recommended for real-time performance

---

## Design Philosophy

This system does not attempt to determine intent or criminal behaviour.
Instead, it highlights unusual patterns using rule-based analysis so that human operators can make decisions.

---

## Future Improvements (Optional)

* Threat timeline panel
* Multi-camera support
* Alert notification system
* Behaviour score decay over time
* Database logging

---

## Author Notes

This project focuses on practical real-time surveillance engineering using modular design principles.
Each module is separated to maintain clarity, scalability, and debugging simplicity.
