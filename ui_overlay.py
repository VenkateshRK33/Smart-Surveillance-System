import cv2


class UIOverlay:
    """
    Renders visual elements on surveillance frames.
    
    Displays:
    - Color-coded bounding boxes based on alert level
    - Person tracking information (ID, score, duration)
    - Restricted zone boundaries
    - FPS counter
    
    Color scheme:
    - Green: NORMAL alert level (score 0-2)
    - Yellow: SUSPICIOUS alert level (score 3-4)
    - Red: THREAT alert level (score 5+)
    """
    
    def __init__(self, restricted_zone=None):
        """
        Initialize UIOverlay with optional restricted zone configuration.
        
        Args:
            restricted_zone: Optional dict defining restricted area boundaries
                {'x1': int, 'y1': int, 'x2': int, 'y2': int}
                If None, restricted zone visualization is disabled
        """
        self.restricted_zone = restricted_zone
        
        # Define color mappings for alert levels (BGR format for OpenCV)
        self.alert_colors = {
            'NORMAL': (0, 255, 0),      # Green
            'SUSPICIOUS': (0, 255, 255), # Yellow
            'THREAT': (0, 0, 255)        # Red
        }
    
    def draw(self, frame, tracked_persons, behaviour_scores):
        """
        Draw all visual overlays on the frame (modifies frame in place).
        
        Renders bounding boxes, text labels, and restricted zone visualization.
        
        Args:
            frame: numpy array (BGR image) - modified in place
            tracked_persons: dict from TrackerMemory.get_all() with format:
                {
                    track_id: {
                        'track_id': int,
                        'first_seen_time': float,
                        'last_position': (x, y),
                        'bbox': (x1, y1, x2, y2),
                        'last_seen_frame': int
                    }
                }
            behaviour_scores: dict from BehaviourEngine.calculate_scores() with format:
                {
                    track_id: {
                        'score': int,
                        'alert_level': str,
                        'stay_duration': float,
                        'factors': list of str
                    }
                }
        """
        # Draw restricted zone first (so it appears behind other elements)
        if self.restricted_zone is not None:
            self._draw_restricted_zone(frame)
        
        # Draw bounding boxes and labels for each tracked person
        for track_id, person_data in tracked_persons.items():
            # Get behaviour score data for this person
            score_data = behaviour_scores.get(track_id)
            
            # Skip if no score data available
            if score_data is None:
                continue
            
            # Get alert level and corresponding color
            alert_level = score_data['alert_level']
            color = self.alert_colors.get(alert_level, (255, 255, 255))  # Default to white
            
            # Get bounding box coordinates
            bbox = person_data['bbox']
            x1, y1, x2, y2 = bbox
            
            # Draw bounding box with thickness 2
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw text labels above bounding box
            self._draw_text_labels(frame, track_id, score_data, (x1, y1), color)
    
    def _draw_text_labels(self, frame, track_id, score_data, bbox_top_left, color):
        """
        Draw text labels above the bounding box.
        
        Displays:
        - Line 1: ID: {track_id}
        - Line 2: Score: {score} | {alert_level}
        - Line 3: Time: {stay_duration}s
        
        Args:
            frame: numpy array (BGR image)
            track_id: Unique tracking ID
            score_data: dict with score, alert_level, stay_duration
            bbox_top_left: tuple (x1, y1) - top-left corner of bounding box
            color: tuple (B, G, R) - text color matching bbox color
        """
        x1, y1 = bbox_top_left
        
        # Font configuration
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        line_height = 20  # Pixels between lines
        
        # Get frame dimensions for boundary checks
        frame_height, frame_width = frame.shape[:2]
        
        # Prepare text lines
        line1 = f"ID: {track_id}"
        line2 = f"Score: {score_data['score']} | {score_data['alert_level']}"
        line3 = f"Time: {score_data['stay_duration']:.1f}s"
        
        # Calculate starting y position (above bbox, accounting for all 3 lines)
        text_y_start = y1 - 10
        
        # Boundary check: if text would go off top of frame, draw below bbox instead
        if text_y_start - (line_height * 2) < 0:
            text_y_start = y1 + 25  # Draw below bbox top edge
        
        # Draw each line of text
        lines = [line1, line2, line3]
        for i, text in enumerate(lines):
            text_y = text_y_start - (i * line_height)
            
            # Boundary check for x position
            text_x = max(5, x1)  # Keep at least 5 pixels from left edge
            
            # Get text size to check right boundary
            (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
            if text_x + text_width > frame_width - 5:
                text_x = frame_width - text_width - 5
            
            # Draw text with black background for visibility
            cv2.putText(frame, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness + 2)
            cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness)
    
    def _draw_restricted_zone(self, frame):
        """
        Draw restricted zone rectangle on the frame.
        
        Args:
            frame: numpy array (BGR image)
        """
        if self.restricted_zone is None:
            return
        
        x1 = self.restricted_zone['x1']
        y1 = self.restricted_zone['y1']
        x2 = self.restricted_zone['x2']
        y2 = self.restricted_zone['y2']
        
        # Draw blue rectangle with thickness 2
        blue_color = (255, 0, 0)  # BGR format
        cv2.rectangle(frame, (x1, y1), (x2, y2), blue_color, 2)
        
        # Add label for restricted zone
        label = "RESTRICTED ZONE"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        # Position label at top of restricted zone
        label_x = x1 + 5
        label_y = y1 - 10 if y1 > 30 else y1 + 25
        
        # Draw label with black background
        cv2.putText(frame, label, (label_x, label_y), font, font_scale, (0, 0, 0), thickness + 2)
        cv2.putText(frame, label, (label_x, label_y), font, font_scale, blue_color, thickness)
    
    def draw_fps(self, frame, fps):
        """
        Draw FPS counter at top-left corner of frame.
        
        Args:
            frame: numpy array (BGR image)
            fps: float - frames per second value
        """
        # Format FPS text
        fps_text = f"FPS: {fps:.1f}"
        
        # Font configuration
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        
        # Position at top-left corner
        text_x = 10
        text_y = 30
        
        # Get text size for background rectangle
        (text_width, text_height), baseline = cv2.getTextSize(fps_text, font, font_scale, thickness)
        
        # Draw black background rectangle for visibility
        bg_x1 = text_x - 5
        bg_y1 = text_y - text_height - 5
        bg_x2 = text_x + text_width + 5
        bg_y2 = text_y + baseline + 5
        cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
        
        # Draw white text
        white_color = (255, 255, 255)
        cv2.putText(frame, fps_text, (text_x, text_y), font, font_scale, white_color, thickness)
