import time


class BehaviourEngine:
    """
    Behaviour scoring engine that evaluates suspicious activity based on multiple factors.
    
    Calculates behaviour scores for tracked persons and assigns alert levels:
    - NORMAL (0-2 points): No significant suspicious behaviour
    - SUSPICIOUS (3-4 points): Some concerning factors present
    - THREAT (5+ points): High-risk situation requiring immediate attention
    
    Scoring factors:
    - Long stay (>30s): +1 point
    - Restricted zone entry: +2 points
    - Low movement (<20px over 5s): +1 point
    - Crowd condition: +1 point per person
    - Weapon detected near person: +5 points
    """
    
    def __init__(self, restricted_zone=None, crowd_threshold=5):
        """
        Initialize BehaviourEngine with configuration parameters.
        
        Args:
            restricted_zone: Optional dict defining restricted area boundaries
                {'x1': int, 'y1': int, 'x2': int, 'y2': int}
                If None, restricted zone checking is disabled
            crowd_threshold: Number of people that triggers crowd condition (default: 5)
        """
        self.restricted_zone = restricted_zone
        self.crowd_threshold = crowd_threshold
        
        # Store position history for movement tracking (track_id -> list of (timestamp, position))
        self.position_history = {}

    def calculate_scores(self, tracked_persons, weapon_detections, frame_shape, suspicious_items=None):
        """
        Calculate behaviour scores and alert levels for all tracked persons.
        
        Evaluates multiple suspicious behaviour factors and assigns cumulative scores.
        Each factor contributes points based on specific conditions.
        
        Args:
            tracked_persons: dict from TrackerMemory.get_all()
            weapon_detections: list of weapon detection dicts
            frame_shape: tuple (height, width, channels)
            suspicious_items: list of suspicious item detections (optional)
        
        Returns:
            dict: Mapping track_id to score data with alert levels and factors
        """
        current_time = time.time()
        scores = {}
        
        # Get total person count for crowd detection
        total_persons = len(tracked_persons)
        
        # Calculate scores for each tracked person
        for track_id, person_data in tracked_persons.items():
            score = 0
            factors = []
            
            # Calculate stay duration
            stay_duration = current_time - person_data['first_seen_time']
            
            # Get person's current position and bbox
            current_position = person_data['last_position']
            person_bbox = person_data['bbox']
            
            # Update position history for movement tracking
            if track_id not in self.position_history:
                self.position_history[track_id] = []
            
            self.position_history[track_id].append((current_time, current_position))
            
            # Clean up old position history (keep only last 10 seconds)
            self.position_history[track_id] = [
                (t, pos) for t, pos in self.position_history[track_id]
                if current_time - t <= 10
            ]
            
            # Factor 1: Long stay/Loitering (>30 seconds) = +1 point
            if stay_duration > 30:
                score += 1
                factors.append(f"Loitering ({stay_duration:.1f}s)")
            
            # Factor 2: Restricted zone entry = +2 points
            if self.restricted_zone is not None:
                if self._is_in_restricted_zone(current_position):
                    score += 2
                    factors.append("In restricted zone")
            
            # Factor 3: Low movement/Suspicious stillness (<20 pixels over 5 seconds) = +1 point
            if self._has_low_movement(track_id, current_time):
                score += 1
                factors.append("Suspicious stillness")
            
            # Factor 4: Rapid/Erratic movement = +1 point
            if self._has_rapid_movement(track_id, current_time):
                score += 1
                factors.append("Erratic movement")
            
            # Factor 5: Crowd condition (2+ people) = +1 point
            if total_persons >= 2:
                score += 1
                factors.append(f"Multiple people ({total_persons})")
            
            # Factor 6: Weapon detected near person = +5 points (CRITICAL)
            weapon_near = self._check_weapon_near_person(person_bbox, weapon_detections)
            if weapon_near:
                score += 5
                factors.append(f"Weapon: {weapon_near}")
            
            # Factor 7: Suspicious items (backpack, suitcase) = +2 points
            if suspicious_items:
                suspicious_item = self._check_suspicious_item_near_person(person_bbox, suspicious_items)
                if suspicious_item:
                    score += 2
                    factors.append(f"Suspicious item: {suspicious_item}")
            
            # Factor 8: Person at edge of frame (potential escape/entry) = +1 point
            if self._is_at_frame_edge(person_bbox, frame_shape):
                score += 1
                factors.append("At frame edge")
            
            # Determine alert level based on score
            if score >= 5:
                alert_level = 'THREAT'
            elif score >= 3:
                alert_level = 'SUSPICIOUS'
            else:
                alert_level = 'NORMAL'
            
            # Store score data
            scores[track_id] = {
                'score': score,
                'alert_level': alert_level,
                'stay_duration': stay_duration,
                'factors': factors
            }
        
        return scores

    def _is_in_restricted_zone(self, position):
        """
        Check if a position is inside the restricted zone.
        
        Args:
            position: tuple (x, y) representing center coordinates
        
        Returns:
            bool: True if position is inside restricted zone, False otherwise
        """
        if self.restricted_zone is None:
            return False
        
        x, y = position
        x1 = self.restricted_zone['x1']
        y1 = self.restricted_zone['y1']
        x2 = self.restricted_zone['x2']
        y2 = self.restricted_zone['y2']
        
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def _has_low_movement(self, track_id, current_time):
        """
        Check if person has low movement (position change < 20 pixels over 5 seconds).
        
        Args:
            track_id: Unique tracking ID
            current_time: Current timestamp
        
        Returns:
            bool: True if low movement detected, False otherwise
        """
        if track_id not in self.position_history:
            return False
        
        history = self.position_history[track_id]
        
        # Need at least 2 positions to compare
        if len(history) < 2:
            return False
        
        # Find position from approximately 5 seconds ago
        position_5s_ago = None
        for timestamp, position in history:
            if current_time - timestamp >= 5:
                position_5s_ago = position
                break
        
        # If we don't have data from 5 seconds ago, can't determine low movement
        if position_5s_ago is None:
            return False
        
        # Get current position (most recent)
        current_position = history[-1][1]
        
        # Calculate distance moved
        x1, y1 = position_5s_ago
        x2, y2 = current_position
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
        return distance < 20
    
    def _has_rapid_movement(self, track_id, current_time):
        """
        Check if person has rapid/erratic movement (>100 pixels in 2 seconds).
        
        Args:
            track_id: Unique tracking ID
            current_time: Current timestamp
        
        Returns:
            bool: True if rapid movement detected, False otherwise
        """
        if track_id not in self.position_history:
            return False
        
        history = self.position_history[track_id]
        
        if len(history) < 2:
            return False
        
        # Find position from approximately 2 seconds ago
        position_2s_ago = None
        for timestamp, position in history:
            if current_time - timestamp >= 2:
                position_2s_ago = position
                break
        
        if position_2s_ago is None:
            return False
        
        current_position = history[-1][1]
        
        # Calculate distance moved
        x1, y1 = position_2s_ago
        x2, y2 = current_position
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
        return distance > 100
    
    def _check_suspicious_item_near_person(self, person_bbox, suspicious_items):
        """
        Check if any suspicious item (backpack, suitcase) is near person.
        
        Args:
            person_bbox: tuple (x1, y1, x2, y2) for person bounding box
            suspicious_items: list of suspicious item detection dicts
        
        Returns:
            str: Item class name if found near person, None otherwise
        """
        if not suspicious_items:
            return None
        
        px1, py1, px2, py2 = person_bbox
        
        # Expand person bbox to catch nearby items
        width = px2 - px1
        height = py2 - py1
        expand = 0.3
        
        px1_expanded = px1 - width * expand
        py1_expanded = py1 - height * expand
        px2_expanded = px2 + width * expand
        py2_expanded = py2 + height * expand
        
        for item in suspicious_items:
            ix1, iy1, ix2, iy2 = item['bbox']
            
            # Check if item center is near person
            item_center_x = (ix1 + ix2) / 2
            item_center_y = (iy1 + iy2) / 2
            
            if (px1_expanded <= item_center_x <= px2_expanded and 
                py1_expanded <= item_center_y <= py2_expanded):
                return item['class']
        
        return None
    
    def _is_at_frame_edge(self, person_bbox, frame_shape):
        """
        Check if person is at the edge of the frame (potential entry/exit).
        
        Args:
            person_bbox: tuple (x1, y1, x2, y2)
            frame_shape: tuple (height, width, channels)
        
        Returns:
            bool: True if person is at frame edge, False otherwise
        """
        height, width = frame_shape[:2]
        x1, y1, x2, y2 = person_bbox
        
        edge_threshold = 50  # pixels from edge
        
        # Check if person is near any edge
        at_left = x1 < edge_threshold
        at_right = x2 > width - edge_threshold
        at_top = y1 < edge_threshold
        at_bottom = y2 > height - edge_threshold
        
        return at_left or at_right or at_top or at_bottom
    
    def _check_weapon_near_person(self, person_bbox, weapon_detections):
        """
        Check if any weapon bbox overlaps with person bbox using IoU.
        Uses a more lenient proximity check to catch weapons near persons.
        
        Args:
            person_bbox: tuple (x1, y1, x2, y2) for person bounding box
            weapon_detections: list of weapon detection dicts
        
        Returns:
            str: Weapon class name if overlap detected, None otherwise
        """
        if not weapon_detections:
            return None
        
        px1, py1, px2, py2 = person_bbox
        
        # Expand person bbox by 20% to catch nearby weapons
        width = px2 - px1
        height = py2 - py1
        expand = 0.2
        
        px1_expanded = px1 - width * expand
        py1_expanded = py1 - height * expand
        px2_expanded = px2 + width * expand
        py2_expanded = py2 + height * expand
        
        for weapon in weapon_detections:
            wx1, wy1, wx2, wy2 = weapon['bbox']
            
            # Check if weapon center is near person
            weapon_center_x = (wx1 + wx2) / 2
            weapon_center_y = (wy1 + wy2) / 2
            
            if (px1_expanded <= weapon_center_x <= px2_expanded and 
                py1_expanded <= weapon_center_y <= py2_expanded):
                print(f"[BEHAVIOR] Weapon '{weapon['class']}' associated with person")
                return weapon['class']
            
            # Also check for any overlap
            intersection_x1 = max(px1, wx1)
            intersection_y1 = max(py1, wy1)
            intersection_x2 = min(px2, wx2)
            intersection_y2 = min(py2, wy2)
            
            # Check if there's an intersection
            if intersection_x1 < intersection_x2 and intersection_y1 < intersection_y2:
                print(f"[BEHAVIOR] Weapon '{weapon['class']}' overlaps with person")
                return weapon['class']
        
        return None
