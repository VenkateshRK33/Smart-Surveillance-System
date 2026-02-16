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

    def calculate_scores(self, tracked_persons, weapon_detections, frame_shape):
        """
        Calculate behaviour scores and alert levels for all tracked persons.
        
        Evaluates multiple suspicious behaviour factors and assigns cumulative scores.
        Each factor contributes points based on specific conditions.
        
        Args:
            tracked_persons: dict from TrackerMemory.get_all() with format:
                {
                    track_id: {
                        'track_id': int,
                        'first_seen_time': float (timestamp),
                        'last_position': (x, y),
                        'bbox': (x1, y1, x2, y2),
                        'last_seen_frame': int
                    }
                }
            weapon_detections: list of weapon detection dicts:
                [
                    {
                        'bbox': (x1, y1, x2, y2),
                        'class': str ('knife' or 'gun'),
                        'confidence': float
                    }
                ]
            frame_shape: tuple (height, width, channels)
        
        Returns:
            dict: Mapping track_id to score data:
                {
                    track_id: {
                        'score': int,
                        'alert_level': str ('NORMAL', 'SUSPICIOUS', 'THREAT'),
                        'stay_duration': float (seconds),
                        'factors': list of str (reasons for score)
                    }
                }
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
            
            # Factor 1: Long stay (>30 seconds) = +1 point
            if stay_duration > 30:
                score += 1
                factors.append(f"Long stay ({stay_duration:.1f}s)")
            
            # Factor 2: Restricted zone entry = +2 points
            if self.restricted_zone is not None:
                if self._is_in_restricted_zone(current_position):
                    score += 2
                    factors.append("In restricted zone")
            
            # Factor 3: Low movement (<20 pixels over 5 seconds) = +1 point
            if self._has_low_movement(track_id, current_time):
                score += 1
                factors.append("Low movement")
            
            # Factor 4: Crowd condition = +1 point per person
            if total_persons > self.crowd_threshold:
                score += 1
                factors.append(f"Crowd detected ({total_persons} people)")
            
            # Factor 5: Weapon detected near person = +5 points
            weapon_near = self._check_weapon_near_person(person_bbox, weapon_detections)
            if weapon_near:
                score += 5
                factors.append(f"Weapon detected ({weapon_near})")
            
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
