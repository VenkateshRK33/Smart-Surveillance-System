# Requirements Document

## Introduction

The Smart Surveillance System is a real-time computer vision application designed to detect and track suspicious behaviour in video streams from webcams or CCTV footage. The system uses YOLO11 for person detection and tracking, a Roboflow-trained model for weapon detection, and a custom behaviour scoring engine to assess threat levels. The system provides visual alerts through color-coded bounding boxes and automatically captures screenshots when threat-level conditions are met. This implementation focuses on practical deployment for security monitoring operations.

## Glossary

- **Surveillance System**: The complete Smart Surveillance application
- **Person Tracker**: The component that assigns and maintains unique tracking IDs for detected persons
- **Behaviour Engine**: The scoring system that evaluates suspicious activity based on multiple factors
- **Weapon Detector**: The Roboflow-trained YOLO model that identifies knives and guns
- **Person Detector**: The YOLO11 model that identifies and tracks people in video frames
- **Video Source**: The input stream from webcam or CCTV footage
- **Restricted Zone**: A defined area within the surveillance frame where presence increases behaviour score
- **Alert Level**: Classification of threat (NORMAL, SUSPICIOUS, THREAT)
- **Behaviour Score**: Numerical value representing cumulative suspicious activity for a tracked person
- **Stay Duration**: Time elapsed since a person was first detected in the video stream
- **Tracking ID**: Unique identifier assigned to each detected person by YOLO tracking
- **Person Memory**: Data structure storing tracking history for each detected person
- **UI Overlay**: Visual rendering layer displaying bounding boxes, scores, and alerts

## Requirements

### Requirement 1

**User Story:** As a security operator, I want the system to detect and track people in real-time video streams, so that I can monitor individuals throughout their presence in the surveillance area

#### Acceptance Criteria

1. WHEN the Surveillance System receives a video frame, THE Person Detector SHALL identify all persons visible in the frame
2. WHEN a person is detected, THE Person Tracker SHALL assign a unique Tracking ID to that person
3. WHILE a person remains visible across consecutive frames, THE Person Tracker SHALL maintain the same Tracking ID for that person
4. THE Surveillance System SHALL process video frames at a minimum rate of 15 frames per second
5. WHEN a person exits the frame for more than 3 seconds, THE Person Memory SHALL remove that person's tracking data

### Requirement 2

**User Story:** As a security operator, I want to see how long each person has been in view, so that I can identify individuals who remain in the area for extended periods

#### Acceptance Criteria

1. WHEN a person is first detected, THE Person Memory SHALL record the timestamp as first_seen_time
2. WHILE a person remains tracked, THE Surveillance System SHALL calculate Stay Duration as the difference between current time and first_seen_time
3. THE UI Overlay SHALL display the Stay Duration in seconds near each person's bounding box
4. THE Stay Duration SHALL update in real-time for each tracked person

### Requirement 3

**User Story:** As a security operator, I want the system to detect weapons in the video stream, so that I can respond immediately to potential threats

#### Acceptance Criteria

1. THE Weapon Detector SHALL load the Roboflow-trained YOLO model from the models directory
2. WHEN the Surveillance System processes a frame, THE Weapon Detector SHALL identify knives and guns within the frame
3. THE Weapon Detector SHALL execute detection at intervals of 2 to 3 frames to maintain performance
4. WHEN a weapon is detected, THE Behaviour Engine SHALL increase the associated person's Behaviour Score by 5 points
5. WHEN a weapon is detected near a tracked person, THE Surveillance System SHALL immediately classify that person's Alert Level as THREAT

### Requirement 4

**User Story:** As a security operator, I want the system to calculate a behaviour score for each person based on multiple suspicious factors, so that I can prioritize monitoring efforts

#### Acceptance Criteria

1. THE Behaviour Engine SHALL maintain a Behaviour Score for each tracked person starting at 0
2. WHEN Stay Duration exceeds 30 seconds, THE Behaviour Engine SHALL increase Behaviour Score by 1 point
3. WHEN a person enters a Restricted Zone, THE Behaviour Engine SHALL increase Behaviour Score by 2 points
4. WHEN a person exhibits low movement (position change less than 20 pixels over 5 seconds), THE Behaviour Engine SHALL increase Behaviour Score by 1 point
5. WHEN the number of detected persons exceeds 5, THE Behaviour Engine SHALL increase each person's Behaviour Score by 1 point
6. THE Behaviour Engine SHALL recalculate Behaviour Score for each tracked person on every processed frame

### Requirement 5

**User Story:** As a security operator, I want the system to classify threat levels based on behaviour scores, so that I can quickly identify which individuals require immediate attention

#### Acceptance Criteria

1. WHEN Behaviour Score is between 0 and 2, THE Behaviour Engine SHALL assign Alert Level as NORMAL
2. WHEN Behaviour Score is between 3 and 4, THE Behaviour Engine SHALL assign Alert Level as SUSPICIOUS
3. WHEN Behaviour Score is 5 or greater, THE Behaviour Engine SHALL assign Alert Level as THREAT
4. THE UI Overlay SHALL display the current Alert Level text near each person's bounding box

### Requirement 6

**User Story:** As a security operator, I want visual indicators that clearly show each person's threat level, so that I can quickly assess the situation at a glance

#### Acceptance Criteria

1. WHEN Alert Level is NORMAL, THE UI Overlay SHALL draw the bounding box in green color
2. WHEN Alert Level is SUSPICIOUS, THE UI Overlay SHALL draw the bounding box in yellow color
3. WHEN Alert Level is THREAT, THE UI Overlay SHALL draw the bounding box in red color
4. THE UI Overlay SHALL display the Tracking ID above each person's bounding box
5. THE UI Overlay SHALL display the Behaviour Score value near each person's bounding box
6. THE UI Overlay SHALL display the current frames per second (FPS) counter on the video frame

### Requirement 7

**User Story:** As a security operator, I want to define restricted zones in the surveillance area, so that the system can detect when people enter sensitive locations

#### Acceptance Criteria

1. THE Surveillance System SHALL allow configuration of a Restricted Zone defined by coordinate boundaries
2. WHEN a person's bounding box center point falls within the Restricted Zone coordinates, THE Behaviour Engine SHALL detect the person as inside the zone
3. THE UI Overlay SHALL draw the Restricted Zone boundary on the video frame for operator reference
4. WHILE a person remains inside the Restricted Zone, THE Behaviour Engine SHALL continuously apply the zone penalty to Behaviour Score

### Requirement 8

**User Story:** As a security operator, I want the system to automatically capture screenshots when threats are detected, so that I have evidence for review and reporting

#### Acceptance Criteria

1. WHEN any tracked person reaches Alert Level THREAT, THE Surveillance System SHALL capture the current video frame as a screenshot
2. THE Surveillance System SHALL save the screenshot to disk with a timestamp in the filename
3. THE Surveillance System SHALL save screenshots in a dedicated directory within the project structure
4. THE Surveillance System SHALL capture only one screenshot per person per THREAT event to avoid duplicate captures

### Requirement 9

**User Story:** As a security operator, I want to use either a webcam or recorded CCTV footage as input, so that I can test and deploy the system in different scenarios

#### Acceptance Criteria

1. THE Video Source SHALL support webcam input when configured with device index 0
2. THE Video Source SHALL support video file input when configured with a file path
3. WHEN the Video Source is initialized, THE Surveillance System SHALL verify the source is accessible and readable
4. THE Video Source SHALL provide frames sequentially through a read method
5. WHEN the video source ends or becomes unavailable, THE Surveillance System SHALL terminate gracefully

### Requirement 10

**User Story:** As a security operator, I want to exit the surveillance system cleanly, so that resources are properly released

#### Acceptance Criteria

1. WHEN the operator presses the 'q' key, THE Surveillance System SHALL terminate the video processing loop
2. WHEN the Surveillance System terminates, THE Video Source SHALL release the video capture device
3. WHEN the Surveillance System terminates, THE Surveillance System SHALL close all OpenCV windows
4. THE Surveillance System SHALL complete shutdown within 2 seconds of receiving the exit command
