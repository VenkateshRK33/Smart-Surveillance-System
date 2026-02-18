"""
Train YOLOv11 Gun Detection Model
Dataset path: C:\\Users\\11one\\OneDrive\\Desktop\\guns train and test
"""
from ultralytics import YOLO
import os

print("=" * 60)
print("GUN DETECTION MODEL TRAINING")
print("=" * 60)

# Dataset path
dataset_path = r"C:\Users\11one\OneDrive\Desktop\guns train and test"

print(f"\nDataset location: {dataset_path}")
print("\nChecking dataset structure...")

# Check if dataset exists
if not os.path.exists(dataset_path):
    print(f"ERROR: Dataset path not found: {dataset_path}")
    exit(1)

# List contents
print("\nDataset contents:")
for item in os.listdir(dataset_path):
    item_path = os.path.join(dataset_path, item)
    if os.path.isdir(item_path):
        print(f"  📁 {item}/")
        # List subdirectory contents
        try:
            sub_items = os.listdir(item_path)
            print(f"     Contains {len(sub_items)} items")
        except:
            pass
    else:
        print(f"  📄 {item}")

print("\n" + "=" * 60)
print("TRAINING CONFIGURATION")
print("=" * 60)

# Training configuration
config = {
    'model': 'yolo11n.pt',  # Nano model (fastest)
    'epochs': 50,  # Number of training epochs
    'imgsz': 640,  # Image size
    'batch': 16,  # Batch size (adjust based on GPU memory)
    'device': 0,  # Use GPU if available, else CPU
    'project': 'models',  # Save location
    'name': 'gun_detection',  # Model name
}

print(f"\nModel: {config['model']}")
print(f"Epochs: {config['epochs']}")
print(f"Image Size: {config['imgsz']}")
print(f"Batch Size: {config['batch']}")
print(f"Output: {config['project']}/{config['name']}")

print("\n" + "=" * 60)
print("IMPORTANT: Dataset Format Required")
print("=" * 60)
print("""
Your dataset should be organized as:

guns train and test/
├── data.yaml          # Dataset configuration file
├── train/
│   ├── images/       # Training images
│   └── labels/       # Training labels (.txt files)
└── valid/
    ├── images/       # Validation images
    └── labels/       # Validation labels (.txt files)

The data.yaml file should contain:
---
train: ../train/images
val: ../valid/images
nc: 1
names: ['gun']
---

If your dataset is not in this format, please reorganize it first.
""")

# Ask user to confirm
response = input("\nIs your dataset in the correct YOLO format? (yes/no): ")

if response.lower() != 'yes':
    print("\nPlease organize your dataset in YOLO format first.")
    print("You can use Roboflow to export in YOLO format, or manually create the structure.")
    exit(0)

# Check for data.yaml
data_yaml = os.path.join(dataset_path, 'data.yaml')
if not os.path.exists(data_yaml):
    print(f"\nERROR: data.yaml not found at {data_yaml}")
    print("Creating a template data.yaml file...")
    
    # Create template
    yaml_content = f"""# Gun Detection Dataset Configuration
train: {dataset_path}/train/images
val: {dataset_path}/valid/images

nc: 1  # number of classes
names: ['gun']  # class names
"""
    
    with open(data_yaml, 'w') as f:
        f.write(yaml_content)
    
    print(f"✓ Created template data.yaml")
    print("Please verify the paths are correct and run this script again.")
    exit(0)

print("\n" + "=" * 60)
print("STARTING TRAINING")
print("=" * 60)

try:
    # Load YOLO model
    print(f"\nLoading {config['model']}...")
    model = YOLO(config['model'])
    
    print("✓ Model loaded")
    print("\nStarting training... This may take a while!")
    print("(Training time depends on dataset size and hardware)")
    
    # Train the model
    results = model.train(
        data=data_yaml,
        epochs=config['epochs'],
        imgsz=config['imgsz'],
        batch=config['batch'],
        device=config['device'],
        project=config['project'],
        name=config['name'],
        patience=10,  # Early stopping patience
        save=True,
        plots=True,
        verbose=True
    )
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    
    # Find the best model
    best_model_path = os.path.join(config['project'], config['name'], 'weights', 'best.pt')
    
    if os.path.exists(best_model_path):
        print(f"\n✓ Best model saved at: {best_model_path}")
        print(f"\nTo use this model in your surveillance system:")
        print(f"1. Copy {best_model_path} to models/gun_detection.pt")
        print(f"2. Update detector_roboflow.py to use this model")
    else:
        print(f"\nModel training completed but best.pt not found at expected location")
    
    print("\nTraining metrics and plots saved in:")
    print(f"  {os.path.join(config['project'], config['name'])}")
    
except Exception as e:
    print(f"\n✗ Training failed: {e}")
    import traceback
    traceback.print_exc()
    
print("\n" + "=" * 60)
