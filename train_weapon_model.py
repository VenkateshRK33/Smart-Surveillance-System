"""
Train weapon detection model using YOLO11 on the downloaded dataset
"""
from ultralytics import YOLO
import os

print("=" * 60)
print("TRAINING WEAPON DETECTION MODEL (YOLO11)")
print("=" * 60)

# Check if dataset exists
if not os.path.exists('weapon-1/data.yaml'):
    print("\n✗ Dataset not found!")
    print("Please run download_roboflow_model.py first")
    exit(1)

print("\n[INFO] Dataset found: weapon-1/")

# Read data.yaml to see what we're working with
print("\n[INFO] Dataset configuration:")
with open('weapon-1/data.yaml', 'r') as f:
    print(f.read())

print("\n" + "=" * 60)
print("STARTING TRAINING")
print("=" * 60)

print("\n[INFO] Loading YOLO11n model...")
print("[INFO] This will use the pre-trained YOLO11n as a base")

try:
    # Load YOLO11n model for transfer learning
    model = YOLO('yolo11n.pt')
    
    print("\n[INFO] Starting training...")
    print("[INFO] This may take 10-30 minutes depending on your hardware")
    print("[INFO] Training parameters:")
    print("  - Epochs: 50")
    print("  - Image size: 640")
    print("  - Batch size: 16 (auto-adjusted based on GPU)")
    print("  - Device: auto (GPU if available, else CPU)")
    
    # Train the model
    results = model.train(
        data='weapon-1/data.yaml',
        epochs=50,
        imgsz=640,
        batch=16,
        name='weapon_detection',
        patience=10,
        save=True,
        device='cpu',  # Use CPU (change to 0 for GPU if available)
        verbose=True
    )
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETED!")
    print("=" * 60)
    
    # Find the best model
    best_model_path = 'runs/detect/weapon_detection/weights/best.pt'
    
    if os.path.exists(best_model_path):
        # Copy to models directory
        import shutil
        os.makedirs('models', exist_ok=True)
        shutil.copy(best_model_path, 'models/best.pt')
        
        model_size = os.path.getsize('models/best.pt') / (1024 * 1024)
        print(f"\n✓ Trained model saved to: models/best.pt")
        print(f"  Model size: {model_size:.2f} MB")
        
        print("\n[INFO] Training results saved to: runs/detect/weapon_detection/")
        print("[INFO] You can view training metrics and validation results there")
        
        print("\nYou can now run the surveillance system:")
        print("  python main.py")
    else:
        print(f"\n⚠ Could not find trained model at: {best_model_path}")
        print("Please check the runs/detect/ directory")
    
except Exception as e:
    print(f"\n✗ Training failed: {e}")
    print("\nThis might be due to:")
    print("1. Insufficient memory")
    print("2. Dataset issues")
    print("3. Missing dependencies")
    
    print("\nAlternative: Use a pre-trained model")
    print("Visit: https://universe.roboflow.com/swifeye/weapon-c6q7e")
    print("Look for 'Download Trained Model' or 'Weights' section")

print("\n" + "=" * 60)
