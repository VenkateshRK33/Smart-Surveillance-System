"""
Detector with Roboflow hosted inference API for weapon detection
This uses Roboflow's cloud API instead of local model
"""
from ultralytics import YOLO
from roboflow import Roboflow
import cv2
import numpy as np


class Detector:
    """
    Detector class for YOLO-based person detection and Roboflow weapon detection.
    Uses YOLO11 for person detection with tracking and Roboflow API for weapon detection.
    """
    
    def __init__(self, person_model_path, roboflow_api_key, roboflow_model_id):
        """
        Initialize Detector with YOLO11 for persons and Roboflow API for weapons.
        
        Args:
            person_model_path: Path to YOLO11 model file (e.g., 'models/yolo11n.pt')
            roboflow_api_key: Roboflow API key
            roboflow_model_id: Roboflow model ID (e.g., 'crime-dp3x3/1')
        
        Raises:
            Exception: If person model loading fails
        """
        try:
            # Load YOLO11 model for person detection with tracking
            self.person_model = YOLO(person_model_path)
            print(f"[INFO] Loaded person detection model: {person_model_path}")
        except Exception as e:
            raise Exception(f"Failed to load person model from {person_model_path}: {str(e)}")
        
        # Initialize Roboflow for weapon detection
        self.weapon_model = None
        try:
            print(f"[INFO] Initializing Roboflow crime detection...")
            rf = Roboflow(api_key=roboflow_api_key)
            
            # Parse model ID (format: project/version)
            parts = roboflow_model_id.split('/')
            if len(parts) == 2:
                project_name, version = parts
                workspace = "bahria-university-g0y7w"
            else:
                raise ValueError("Invalid model ID format")
            
            project = rf.workspace(workspace).project(project_name)
            self.weapon_model = project.version(int(version)).model
            
            print(f"[INFO] Roboflow crime detection initialized")
            print(f"[INFO] Using hosted model: {roboflow_model_id}")
        except Exception as e:
            print(f"[WARNING] Failed to initialize Roboflow weapon detection: {str(e)}")
            print("[WARNING] Weapon detection will be disabled")
    
    def detect_persons(self, frame):
        """
        Detect persons in the frame using YOLO11 with NMS.
        
        Args:
            frame: numpy array (BGR image)
        
        Returns:
            List of detection dictionaries (deduplicated)
        """
        try:
            # Use simple detection with higher IOU threshold for better NMS
            results = self.person_model.predict(
                frame, 
                verbose=False, 
                classes=[0],  # class 0 = person
                conf=0.50,    # Higher confidence threshold
                iou=0.5       # IoU threshold for NMS (higher = more aggressive deduplication)
            )
            
            detections = []
            
            # Check if results exist and have boxes
            if results and len(results) > 0:
                result = results[0]
                
                # Check if boxes exist
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes
                    
                    # Get frame dimensions for size filtering
                    frame_height, frame_width = frame.shape[:2]
                    min_person_height = frame_height * 0.20  # Increased from 0.15 to 0.20
                    min_person_width = frame_width * 0.10    # Increased from 0.08 to 0.10
                    
                    # Collect all valid detections first
                    valid_detections = []
                    
                    # Parse each detection
                    for i in range(len(boxes)):
                        # Get bounding box coordinates (xyxy format)
                        bbox_tensor = boxes.xyxy[i]
                        x1, y1, x2, y2 = bbox_tensor.tolist()
                        
                        # Calculate bbox dimensions
                        bbox_width = x2 - x1
                        bbox_height = y2 - y1
                        
                        # Filter out detections that are too small to be persons
                        if bbox_height < min_person_height or bbox_width < min_person_width:
                            print(f"[FILTER] Rejected small detection: {bbox_width:.0f}x{bbox_height:.0f} (min: {min_person_width:.0f}x{min_person_height:.0f})")
                            continue
                        
                        # Get confidence score
                        confidence = float(boxes.conf[i].item())
                        
                        valid_detections.append({
                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                            'confidence': confidence
                        })
                    
                    # Apply additional NMS to be extra sure (in case YOLO's NMS wasn't aggressive enough)
                    if len(valid_detections) > 1:
                        valid_detections = self._apply_person_nms(valid_detections, iou_threshold=0.3)
                    
                    # Assign track IDs based on position (left to right)
                    valid_detections.sort(key=lambda d: d['bbox'][0])  # Sort by x1 coordinate
                    
                    for idx, det in enumerate(valid_detections):
                        detections.append({
                            'track_id': idx + 1,  # Simple sequential ID
                            'bbox': det['bbox'],
                            'confidence': det['confidence']
                        })
            
            if len(detections) > 0:
                print(f"[PERSON] Detected {len(detections)} person(s)")
            
            return detections
        
        except Exception as e:
            print(f"[ERROR] Person detection failed: {str(e)}")
            return []
    
    def _apply_person_nms(self, detections, iou_threshold=0.3):
        """
        Apply NMS specifically for person detections.
        
        Args:
            detections: List of detection dictionaries with bbox and confidence
            iou_threshold: IoU threshold for merging overlapping detections
            
        Returns:
            List of deduplicated detections
        """
        if len(detections) == 0:
            return []
        
        # Sort by confidence (highest first)
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        def calculate_iou(box1, box2):
            """Calculate Intersection over Union"""
            x1_1, y1_1, x2_1, y2_1 = box1
            x1_2, y1_2, x2_2, y2_2 = box2
            
            # Intersection
            x_left = max(x1_1, x1_2)
            y_top = max(y1_1, y1_2)
            x_right = min(x2_1, x2_2)
            y_bottom = min(y2_1, y2_2)
            
            if x_right < x_left or y_bottom < y_top:
                return 0.0
            
            intersection = (x_right - x_left) * (y_bottom - y_top)
            
            # Union
            box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
            box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
            union = box1_area + box2_area - intersection
            
            return intersection / union if union > 0 else 0.0
        
        # Apply NMS
        keep = []
        for detection in detections:
            # Check if this detection overlaps with any kept detection
            is_duplicate = False
            for kept in keep:
                iou = calculate_iou(detection['bbox'], kept['bbox'])
                if iou > iou_threshold:
                    is_duplicate = True
                    print(f"[NMS] Removed duplicate person (IoU: {iou:.2f})")
                    break
            
            if not is_duplicate:
                keep.append(detection)
        
        return keep
    
    def detect_weapons(self, frame):
        """
        Detect weapons using BOTH Roboflow API AND YOLO COCO classes.
        This dual approach increases detection accuracy.
        
        Args:
            frame: numpy array (BGR image)
        
        Returns:
            List of weapon detection dictionaries (already deduplicated)
        """
        detections = []
        
        # Method 1: Try Roboflow API with lower confidence for better detection
        if self.weapon_model is not None:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                predictions = self.weapon_model.predict(frame_rgb, confidence=25).json()  # Lowered to 25 for better gun detection
                
                if 'predictions' in predictions:
                    for pred in predictions['predictions']:
                        x_center = pred['x']
                        y_center = pred['y']
                        width = pred['width']
                        height = pred['height']
                        
                        x1 = int(x_center - width / 2)
                        y1 = int(y_center - height / 2)
                        x2 = int(x_center + width / 2)
                        y2 = int(y_center + height / 2)
                        
                        class_name = pred['class'].lower()
                        confidence = pred['confidence']
                        
                        # Normalize weapon class names
                        if 'gun' in class_name or 'pistol' in class_name or 'firearm' in class_name:
                            weapon_type = 'gun'
                        elif 'knife' in class_name or 'blade' in class_name:
                            weapon_type = 'knife'
                        elif 'bat' in class_name or 'stick' in class_name:
                            weapon_type = 'bat'
                        else:
                            weapon_type = class_name
                        
                        detections.append({
                            'bbox': (x1, y1, x2, y2),
                            'class': weapon_type,
                            'confidence': confidence
                        })
                        
                        print(f"[ROBOFLOW WEAPON] {weapon_type} ({class_name}) - confidence: {confidence:.2f}")
            except Exception as e:
                print(f"[WARNING] Roboflow detection failed: {e}")
        
        # Method 2: Use YOLO person model to detect weapon-like objects
        # COCO classes: 43=knife, 76=scissors, 34=baseball bat
        weapon_classes = [43, 76, 34]
        
        try:
            results = self.person_model.predict(frame, verbose=False, classes=weapon_classes, conf=0.35)  # Lowered to 0.35
            
            if results and len(results) > 0:
                result = results[0]
                
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes
                    
                    for i in range(len(boxes)):
                        bbox_tensor = boxes.xyxy[i]
                        x1, y1, x2, y2 = bbox_tensor.tolist()
                        
                        class_id = int(boxes.cls[i].item())
                        class_name = result.names[class_id].lower()
                        confidence = float(boxes.conf[i].item())
                        
                        # Map class names
                        if 'knife' in class_name or 'scissors' in class_name:
                            weapon_type = 'knife'
                        elif 'bat' in class_name:
                            weapon_type = 'bat'
                        else:
                            weapon_type = 'weapon'
                        
                        detections.append({
                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                            'class': weapon_type,
                            'confidence': confidence
                        })
                        
                        print(f"[YOLO WEAPON] {weapon_type} ({class_name}) - confidence: {confidence:.2f}")
        
        except Exception as e:
            print(f"[ERROR] YOLO weapon detection failed: {str(e)}")
        
        # Apply aggressive NMS to remove duplicates from both detection methods
        if len(detections) > 0:
            detections = self._apply_nms(detections, iou_threshold=0.5)  # Increased from 0.4 to 0.5 for more aggressive deduplication
            print(f"[NMS] After deduplication: {len(detections)} unique weapons")
        
        return detections
    
    def _apply_nms(self, detections, iou_threshold=0.4):
        """
        Apply Non-Maximum Suppression to remove duplicate detections.
        
        Args:
            detections: List of detection dictionaries
            iou_threshold: IoU threshold for considering detections as duplicates
            
        Returns:
            List of deduplicated detections
        """
        if len(detections) == 0:
            return []
        
        # Sort by confidence (highest first)
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        def calculate_iou(box1, box2):
            """Calculate Intersection over Union"""
            x1_1, y1_1, x2_1, y2_1 = box1
            x1_2, y1_2, x2_2, y2_2 = box2
            
            # Intersection
            x_left = max(x1_1, x1_2)
            y_top = max(y1_1, y1_2)
            x_right = min(x2_1, x2_2)
            y_bottom = min(y2_1, y2_2)
            
            if x_right < x_left or y_bottom < y_top:
                return 0.0
            
            intersection = (x_right - x_left) * (y_bottom - y_top)
            
            # Union
            box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
            box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
            union = box1_area + box2_area - intersection
            
            return intersection / union if union > 0 else 0.0
        
        # Apply NMS
        keep = []
        for detection in detections:
            # Check if this detection overlaps with any kept detection
            is_duplicate = False
            for kept in keep:
                iou = calculate_iou(detection['bbox'], kept['bbox'])
                # Consider duplicate if high IoU and same class
                if iou > iou_threshold and detection['class'] == kept['class']:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                keep.append(detection)
        
        return keep
