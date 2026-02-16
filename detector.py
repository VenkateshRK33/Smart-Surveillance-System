from ultralytics import YOLO


class Detector:
    """
    Detector class for YOLO-based person and weapon detection.
    Uses YOLO11 for person detection with tracking and Roboflow model for weapon detection.
    """
    
    def __init__(self, person_model_path, weapon_model_path):
        """
        Initialize Detector with YOLO models for person and weapon detection.
        
        Args:
            person_model_path: Path to YOLO11 model file (e.g., 'models/yolo11n.pt')
            weapon_model_path: Path to Roboflow weapon model file (e.g., 'models/best.pt')
        
        Raises:
            Exception: If person model loading fails
        """
        try:
            # Load YOLO11 model for person detection with tracking
            self.person_model = YOLO(person_model_path)
            print(f"[INFO] Loaded person detection model: {person_model_path}")
        except Exception as e:
            raise Exception(f"Failed to load person model from {person_model_path}: {str(e)}")
        
        # Try to load weapon model, but don't fail if it's not available
        self.weapon_model = None
        try:
            import os
            if os.path.exists(weapon_model_path) and os.path.getsize(weapon_model_path) > 0:
                self.weapon_model = YOLO(weapon_model_path)
                print(f"[INFO] Loaded weapon detection model: {weapon_model_path}")
            else:
                print(f"[WARNING] Weapon model not found or empty: {weapon_model_path}")
                print("[WARNING] Weapon detection will be disabled")
        except Exception as e:
            print(f"[WARNING] Failed to load weapon model: {str(e)}")
            print("[WARNING] Weapon detection will be disabled")
    
    def detect_persons(self, frame):
        """
        Detect and track persons in the frame using YOLO11 with tracking.
        
        Args:
            frame: numpy array (BGR image)
        
        Returns:
            List of detection dictionaries:
            [
                {
                    'track_id': int,
                    'bbox': (x1, y1, x2, y2),
                    'confidence': float
                }
            ]
            Returns empty list if no persons detected.
        """
        try:
            # Try to use tracking first, fall back to detection if tracking fails
            try:
                results = self.person_model.track(frame, persist=True, verbose=False)
            except Exception as track_error:
                # If tracking fails (e.g., lap module missing), use simple detection
                print(f"[WARNING] Tracking unavailable, using detection only: {track_error}")
                results = self.person_model.predict(frame, verbose=False)
            
            detections = []
            
            # Check if results exist and have boxes
            if results and len(results) > 0:
                result = results[0]
                
                # Check if boxes exist
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes
                    
                    # Parse each detection
                    for i in range(len(boxes)):
                        # Try to get tracking ID (may be None if tracking not available)
                        track_id = None
                        if hasattr(boxes, 'id') and boxes.id is not None and i < len(boxes.id):
                            track_id = int(boxes.id[i].item())
                        else:
                            # Use a simple counter as track_id if tracking not available
                            track_id = i + 1000  # Offset to distinguish from real track IDs
                        
                        # Get bounding box coordinates (xyxy format)
                        bbox_tensor = boxes.xyxy[i]
                        x1, y1, x2, y2 = bbox_tensor.tolist()
                        
                        # Get confidence score
                        confidence = float(boxes.conf[i].item())
                        
                        detections.append({
                            'track_id': track_id,
                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                            'confidence': confidence
                        })
            
            return detections
        
        except Exception as e:
            print(f"[ERROR] Person detection failed: {str(e)}")
            return []
    
    def detect_weapons(self, frame):
        """
        Detect weapons (knives and guns) in the frame using Roboflow-trained YOLO11 model.
        
        Args:
            frame: numpy array (BGR image)
        
        Returns:
            List of weapon detection dictionaries:
            [
                {
                    'bbox': (x1, y1, x2, y2),
                    'class': str ('knife', 'gun', 'pistol', etc.),
                    'confidence': float
                }
            ]
            Returns empty list if no weapons detected or weapon model not loaded.
        """
        # Return empty list if weapon model not loaded
        if self.weapon_model is None:
            return []
        
        try:
            # Use model.predict() for weapon detection with confidence threshold
            results = self.weapon_model.predict(frame, verbose=False, conf=0.4)
            
            detections = []
            
            # Check if results exist and have boxes
            if results and len(results) > 0:
                result = results[0]
                
                # Check if boxes exist
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes
                    
                    # Parse each detection
                    for i in range(len(boxes)):
                        # Get bounding box coordinates (xyxy format)
                        bbox_tensor = boxes.xyxy[i]
                        x1, y1, x2, y2 = bbox_tensor.tolist()
                        
                        # Get class ID and name
                        class_id = int(boxes.cls[i].item())
                        class_name = result.names[class_id].lower()
                        
                        # Get confidence score
                        confidence = float(boxes.conf[i].item())
                        
                        detections.append({
                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                            'class': class_name,
                            'confidence': confidence
                        })
            
            return detections
        
        except Exception as e:
            print(f"[ERROR] Weapon detection failed: {str(e)}")
            return []
