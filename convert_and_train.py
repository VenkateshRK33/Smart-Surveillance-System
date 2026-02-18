"""
Convert COCO format dataset to YOLO format and train gun detection model
Dataset: C:\\Users\\11one\\OneDrive\\Desktop\\guns train and test
"""
import os
import json
import shutil
from pathlib import Path
from ultralytics import YOLO

def convert_coco_to_yolo(coco_json_path, images_dir, output_labels_dir):
    """Convert COCO format annotations to YOLO format"""
    print(f"Converting {coco_json_path}...")
    
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
    
    # Create output directory
    os.makedirs(output_labels_dir, exist_ok=True)
    
    # Get image dimensions
    images = {img['id']: img for img in coco_data['images']}
    
    # Group annotations by image
    annotations_by_image = {}
    for ann in coco_data['annotations']:
        img_id = ann['image_id']
        if img_id not in annotations_by_image:
            annotations_by_image[img_id] = []
        annotations_by_image[img_id].append(ann)
    
    # Process each image
    converted_count = 0
    for img_id, img_info in images.items():
        img_width = img_info['width']
        img_height = img_info['height']
        img_filename = img_info['file_name']
        
        # Create label file
        label_filename = os.path.splitext(img_filename)[0] + '.txt'
        label_path = os.path.join(output_labels_dir, label_filename)
        
        # Get annotations for this image
        if img_id in annotations_by_image:
            with open(label_path, 'w') as f:
                for ann in annotations_by_image[img_id]:
                    # COCO bbox format: [x, y, width, height]
                    x, y, w, h = ann['bbox']
                    
                    # Convert to YOLO format: [class_id, x_center, y_center, width, height] (normalized)
                    x_center = (x + w / 2) / img_width
                    y_center = (y + h / 2) / img_height
                    norm_width = w / img_width
                    norm_height = h / img_height
                    
                    # Class ID (gun is category_id 1, YOLO uses 0-indexed so subtract 1)
                    class_id = 0  # We only have one class: gun
                    
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {norm_width:.6f} {norm_height:.6f}\n")
            
            converted_count += 1
    
    print(f"✓ Converted {converted_count} images with annotations")
    return converted_count

def setup_yolo_dataset(source_path, output_path):
    """Setup YOLO format dataset structure"""
    print("\n" + "=" * 60)
    print("CONVERTING DATASET TO YOLO FORMAT")
    print("=" * 60)
    
    # Create output directories
    yolo_path = Path(output_path)
    yolo_path.mkdir(exist_ok=True)
    
    for split in ['train', 'valid', 'test']:
        (yolo_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (yolo_path / split / 'labels').mkdir(parents=True, exist_ok=True)
    
    # Convert each split
    for split in ['train', 'valid', 'test']:
        print(f"\nProcessing {split} split...")
        
        source_split_path = os.path.join(source_path, split)
        coco_json = os.path.join(source_split_path, '_annotations.coco.json')
        
        if not os.path.exists(coco_json):
            print(f"  ⚠ Skipping {split} - no annotations found")
            continue
        
        # Copy images
        print(f"  Copying images...")
        images_copied = 0
        for img_file in os.listdir(source_split_path):
            if img_file.endswith(('.jpg', '.jpeg', '.png')):
                src = os.path.join(source_split_path, img_file)
                dst = yolo_path / split / 'images' / img_file
                shutil.copy2(src, dst)
                images_copied += 1
        print(f"  ✓ Copied {images_copied} images")
        
        # Convert annotations
        labels_dir = yolo_path / split / 'labels'
        convert_coco_to_yolo(coco_json, source_split_path, str(labels_dir))
    
    # Create data.yaml
    data_yaml_content = f"""# Gun Detection Dataset
path: {str(yolo_path.absolute())}
train: train/images
val: valid/images
test: test/images

nc: 1
names: ['gun']
"""
    
    data_yaml_path = yolo_path / 'data.yaml'
    with open(data_yaml_path, 'w') as f:
        f.write(data_yaml_content)
    
    print(f"\n✓ Created data.yaml at {data_yaml_path}")
    print(f"\nYOLO dataset ready at: {yolo_path}")
    
    return str(data_yaml_path)

def train_model(data_yaml_path):
    """Train YOLOv11 model"""
    print("\n" + "=" * 60)
    print("STARTING MODEL TRAINING")
    print("=" * 60)
    
    import torch
    
    # Check if CUDA is available
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    config = {
        'model': 'yolo11n.pt',  # Nano model (fastest, good for real-time)
        'epochs': 100,  # Number of training epochs
        'imgsz': 640,  # Image size
        'batch': 8 if device == 'cpu' else 16,  # Smaller batch for CPU
        'device': device,  # Auto-detect GPU/CPU
        'project': 'models',
        'name': 'gun_detection',
    }
    
    print(f"\nConfiguration:")
    print(f"  Device: {device.upper()} {'(GPU available)' if device == 'cuda' else '(No GPU - using CPU, will be slower)'}")
    print(f"  Model: {config['model']}")
    print(f"  Epochs: {config['epochs']}")
    print(f"  Image Size: {config['imgsz']}")
    print(f"  Batch Size: {config['batch']}")
    
    try:
        # Load model
        print(f"\nLoading {config['model']}...")
        model = YOLO(config['model'])
        print("✓ Model loaded")
        
        # Train
        print("\nTraining started... (this will take a while)")
        results = model.train(
            data=data_yaml_path,
            epochs=config['epochs'],
            imgsz=config['imgsz'],
            batch=config['batch'],
            device=config['device'],
            project=config['project'],
            name=config['name'],
            patience=15,  # Early stopping
            save=True,
            plots=True,
            verbose=True,
            val=True,
        )
        
        print("\n" + "=" * 60)
        print("TRAINING COMPLETE!")
        print("=" * 60)
        
        best_model = os.path.join(config['project'], config['name'], 'weights', 'best.pt')
        if os.path.exists(best_model):
            print(f"\n✓ Best model saved: {best_model}")
            print(f"\nTo use in your surveillance system:")
            print(f"  1. The model is ready at: {best_model}")
            print(f"  2. Update detector_roboflow.py to load this model")
        
        return best_model
        
    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("GUN DETECTION MODEL TRAINING")
    print("=" * 60)
    
    # Paths
    source_dataset = r"C:\Users\11one\OneDrive\Desktop\guns train and test"
    yolo_dataset = "gun_dataset_yolo"
    
    # Check source exists
    if not os.path.exists(source_dataset):
        print(f"\n❌ ERROR: Dataset not found at {source_dataset}")
        exit(1)
    
    print(f"\nSource dataset: {source_dataset}")
    print(f"YOLO dataset will be created at: {yolo_dataset}")
    
    # Convert dataset
    data_yaml = setup_yolo_dataset(source_dataset, yolo_dataset)
    
    # Train model
    print("\n" + "=" * 60)
    input("Press Enter to start training (or Ctrl+C to cancel)...")
    
    best_model = train_model(data_yaml)
    
    if best_model:
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"\nYour trained gun detection model is ready!")
        print(f"Location: {best_model}")
    else:
        print("\n" + "=" * 60)
        print("Training did not complete successfully")
        print("=" * 60)
