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
        Detect and track persons in the frame using YOLO11 with tracking.
        
        Args:
            frame: numpy array (BGR image)
        
        Returns:
            List of detection dictionaries
        """
        try:
            # Use simple detection with lower confidence threshold for better detection
            results = self.person_model.predict(frame, verbose=False, classes=[0], conf=0.25)  # class 0 = person, conf=0.25
            
            detections = []
            
            # Check if results exist and have boxes
            if results and len(results) > 0:
                result = results[0]
                
                # Check if boxes exist
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes
                    
                    # Parse each detection
                    for i in range(len(boxes)):
                        # Use index as track_id (simple tracking)
                        track_id = i + 1000
                        
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
        Detect weapons using BOTH Roboflow API AND YOLO COCO classes.
        This dual approach increases detection accuracy.
        
        Args:
            frame: numpy array (BGR image)
        
        Returns:
            List of weapon detection dictionaries
        """
        detections = []
        
        # Method 1: Try Roboflow API
        if self.weapon_model is not None:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                predictions = self.weapon_model.predict(frame_rgb, confidence=10).json()
                
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
                        
                        detections.append({
                            'bbox': (x1, y1, x2, y2),
                            'class': class_name,
                            'confidence': confidence
                        })
                        
                        print(f"[ROBOFLOW WEAPON] {class_name} - confidence: {confidence:.2f}")
            except Exception as e:
                pass  # Silently fail and try YOLO method
        
        # Method 2: Use YOLO person model to detect weapon-like objects
        # COCO classes: 43=knife, 44=spoon, 45=bowl, 46=banana, 47=apple, 48=sandwich, 49=orange, 50=broccoli, 51=carrot, 52=hot dog, 53=pizza, 54=donut, 55=cake, 56=chair, 57=couch, 58=potted plant, 59=bed, 60=dining table, 61=toilet, 62=tv, 63=laptop, 64=mouse, 65=remote, 66=keyboard, 67=cell phone, 68=microwave, 69=oven, 70=toaster, 71=sink, 72=refrigerator, 73=book, 74=clock, 75=vase, 76=scissors, 77=teddy bear, 78=hair drier, 79=toothbrush
        # We want: 43=knife, 76=scissors, 32=sports ball, 33=kite, 34=baseball bat, 35=baseball glove, 36=skateboard, 37=surfboard, 38=tennis racket
        weapon_classes = [43, 76, 34]  # knife, scissors, baseball bat
        
        try:
            results = self.person_model.predict(frame, verbose=False, classes=weapon_classes, conf=0.15)
            
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
        
        return detections
