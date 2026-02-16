import time


class TrackerMemory:
    """
    Maintains per-person tracking state and history.
    
    Stores tracking data for each detected person including:
    - track_id: Unique identifier from YOLO tracking
    - first_seen_time: Unix timestamp when person was first detected
    - last_position: Center coordinates (x, y) of the person
    - bbox: Bounding box coordinates (x1, y1, x2, y2)
    - last_seen_frame: Frame number when person was last detected
    """
    
    def __init__(self):
        """Initialize empty memory storage for tracking persons."""
        self.memory = {}

    def update(self, person_detections, current_frame_count=0):
        """
        Update tracking memory with new person detections.
        
        For new track_ids, creates a new entry with current timestamp.
        For existing track_ids, updates position, bbox, and last_seen_frame.
        
        Args:
            person_detections: List of person detection dicts with format:
                [
                    {
                        'track_id': int,
                        'bbox': (x1, y1, x2, y2),
                        'confidence': float
                    }
                ]
            current_frame_count: Current frame number (default: 0)
        """
        for detection in person_detections:
            track_id = detection['track_id']
            bbox = detection['bbox']
            
            # Calculate center position from bbox coordinates
            x1, y1, x2, y2 = bbox
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            last_position = (center_x, center_y)
            
            if track_id not in self.memory:
                # Create new entry for new track_id
                self.memory[track_id] = {
                    'track_id': track_id,
                    'first_seen_time': time.time(),
                    'last_position': last_position,
                    'bbox': bbox,
                    'last_seen_frame': current_frame_count
                }
            else:
                # Update existing entry
                self.memory[track_id]['last_position'] = last_position
                self.memory[track_id]['bbox'] = bbox
                self.memory[track_id]['last_seen_frame'] = current_frame_count

    def get(self, track_id):
        """
        Retrieve tracking data for a single person.
        
        Args:
            track_id: Unique tracking ID
            
        Returns:
            dict: Person tracking data with format:
                {
                    'track_id': int,
                    'first_seen_time': float (timestamp),
                    'last_position': (x, y),
                    'bbox': (x1, y1, x2, y2),
                    'last_seen_frame': int
                }
            or None if track_id not found
        """
        return self.memory.get(track_id)
    
    def get_all(self):
        """
        Retrieve all tracked persons.
        
        Returns:
            dict: Dictionary mapping track_id to person data
                {track_id: person_data, ...}
        """
        return self.memory
    
    def cleanup(self, current_frame_count, timeout=90):
        """
        Remove persons not seen for timeout frames (3 seconds at 30fps).
        
        This prevents memory from growing indefinitely and removes stale tracks
        for persons who have left the surveillance area.
        
        Args:
            current_frame_count: Current frame number
            timeout: Number of frames before removing a track (default: 90)
        """
        # Create list of track_ids to remove (can't modify dict during iteration)
        tracks_to_remove = []
        
        for track_id, person_data in self.memory.items():
            frames_since_last_seen = current_frame_count - person_data['last_seen_frame']
            if frames_since_last_seen > timeout:
                tracks_to_remove.append(track_id)
        
        # Remove stale tracks
        for track_id in tracks_to_remove:
            del self.memory[track_id]
