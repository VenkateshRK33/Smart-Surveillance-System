# Implementation Plan

- [x] 1. Implement VideoSource class for video input handling





  - Create VideoSource class with __init__, read(), and release() methods
  - Use cv2.VideoCapture to handle both webcam (int) and video file (str) sources
  - Validate source availability on initialization with isOpened() check
  - Return None from read() when video ends or source unavailable
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.2_

- [x] 2. Implement Detector class for YOLO-based detection






  - [x] 2.1 Create Detector class and load YOLO models

    - Initialize Detector class with person_model_path and weapon_model_path parameters
    - Load YOLO11 model for person detection using YOLO() from ultralytics
    - Load Roboflow weapon model using YOLO() from ultralytics
    - Add error handling for model loading failures
    - _Requirements: 1.1, 3.1_
  

  - [x] 2.2 Implement detect_persons() method with tracking

    - Use model.track() to get person detections with tracking IDs
    - Parse YOLO results to extract track_id, bbox coordinates, and confidence
    - Return list of detection dictionaries with required fields
    - Handle cases where no persons are detected (return empty list)
    - _Requirements: 1.1, 1.2, 1.3_

  

  - [x] 2.3 Implement detect_weapons() method

    - Use model.predict() to detect knives and guns
    - Parse results to extract bbox, class name, and confidence
    - Return list of weapon detection dictionaries
    - Handle cases where no weapons are detected (return empty list)
    - _Requirements: 3.2, 3.3_

- [x] 3. Implement TrackerMemory class for person tracking state





  - [x] 3.1 Create TrackerMemory class with memory storage


    - Initialize empty dictionary for storing person tracking data
    - Define data structure with track_id, first_seen_time, last_position, bbox, last_seen_frame
    - _Requirements: 1.2, 1.3, 2.1_
  

  - [x] 3.2 Implement update() method

    - Accept list of person detections as input
    - For new track_ids, create new entry with current timestamp
    - For existing track_ids, update last_position, bbox, and last_seen_frame
    - Calculate center position from bbox coordinates
    - _Requirements: 1.2, 1.3, 2.1_
  

  - [x] 3.3 Implement get(), get_all(), and cleanup() methods

    - Implement get(track_id) to retrieve single person data
    - Implement get_all() to return all tracked persons dictionary
    - Implement cleanup() to remove persons not seen for 90 frames (3 seconds)
    - _Requirements: 1.5, 2.1_

- [x] 4. Implement BehaviourEngine class for scoring and alert classification





  - [x] 4.1 Create BehaviourEngine class with configuration


    - Initialize with restricted_zone parameter (optional dict with x1, y1, x2, y2)
    - Initialize with crowd_threshold parameter (default 5)
    - _Requirements: 4.1, 4.5, 7.1_
  
  - [x] 4.2 Implement calculate_scores() method


    - Accept tracked_persons dict, weapon_detections list, and frame_shape tuple
    - Initialize score dictionary for each tracked person
    - Calculate stay_duration for each person using current time minus first_seen_time
    - _Requirements: 2.2, 4.1, 4.6_
  

  - [x] 4.3 Implement scoring factors logic

    - Add +1 point when stay_duration exceeds 30 seconds
    - Add +2 points when person center is inside restricted_zone
    - Add +1 point when position change is less than 20 pixels over 5 seconds (low movement)
    - Add +1 point per person when total person count exceeds crowd_threshold
    - Add +5 points when weapon bbox overlaps with person bbox (check IoU)
    - Track contributing factors in a list for each person
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 3.4, 3.5, 7.2_
  

  - [x] 4.4 Implement alert level classification

    - Assign 'NORMAL' when score is 0-2
    - Assign 'SUSPICIOUS' when score is 3-4
    - Assign 'THREAT' when score is 5 or greater
    - Return dictionary mapping track_id to score data (score, alert_level, stay_duration, factors)
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 5. Implement UIOverlay class for visual rendering






  - [x] 5.1 Create UIOverlay class and implement bounding box drawing

    - Initialize with restricted_zone parameter (optional)
    - Implement draw() method accepting frame, tracked_persons, and behaviour_scores
    - Draw bounding boxes with color based on alert_level: green (NORMAL), yellow (SUSPICIOUS), red (THREAT)
    - Use cv2.rectangle() with thickness 2
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  

  - [x] 5.2 Implement text label rendering





    - Display track_id above each bounding box
    - Display behaviour score and alert_level text
    - Display stay_duration in seconds
    - Use cv2.putText() with FONT_HERSHEY_SIMPLEX, size 0.5
    - Match text color to bounding box color
    - Add boundary checks to prevent text from going off-frame
    - _Requirements: 6.4, 6.5, 2.3, 2.4_

  
  - [x] 5.3 Implement restricted zone and FPS display





    - Draw restricted zone rectangle if configured (blue color, thickness 2)
    - Implement draw_fps() method to display FPS counter at top-left corner
    - Use white text with black background rectangle for visibility
    - _Requirements: 6.6, 7.3_

- [x] 6. Implement main.py orchestration and processing loop






  - [x] 6.1 Create configuration and initialize components

    - Define configuration variables: video_source, model paths, restricted_zone, crowd_threshold
    - Initialize VideoSource with configured source
    - Initialize Detector with model paths
    - Initialize TrackerMemory
    - Initialize BehaviourEngine with restricted_zone and crowd_threshold
    - Initialize UIOverlay with restricted_zone
    - Create screenshots directory if it doesn't exist
    - _Requirements: 9.1, 9.2, 7.1_
  


  - [x] 6.2 Implement main processing loop

    - Create while loop to process frames continuously
    - Read frame from VideoSource, break if None
    - Call detect_persons() on every frame
    - Call detect_weapons() every 2-3 frames (use frame counter modulo 3)
    - Update TrackerMemory with person detections
    - Calculate behaviour scores using BehaviourEngine
    - Draw UI overlays on frame
    - Calculate and display FPS
    - _Requirements: 1.1, 1.4, 3.3, 4.6, 6.6_


  
  - [x] 6.3 Implement screenshot capture and exit handling


    - Check if any person has alert_level 'THREAT'
    - Save screenshot with timestamp filename when THREAT detected
    - Use cv2.imwrite() to save to screenshots directory
    - Track captured screenshots to avoid duplicates per person
    - Display frame using cv2.imshow()
    - Check for 'q' key press to exit loop
    - Release VideoSource and destroy all OpenCV windows on exit
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 10.1, 10.2, 10.3, 10.4_

- [x] 7. Implement cleanup and memory management




  - Call TrackerMemory.cleanup() periodically in main loop (every 30 frames)
  - Ensure proper resource cleanup in finally block or exit handler
  - _Requirements: 1.5, 10.2, 10.3_
