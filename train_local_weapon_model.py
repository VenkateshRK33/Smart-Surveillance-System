"""
Train local YOLO11 weapon detection model
This will be much faster and more reliable than Roboflow API
"""
from ultralytics import YOLO
import os

print("=" * 60)
print("TRAINING LOCAL WEAPON DETECTION MODEL")
print("=" * 60)

print("\n[INFO] This will train a YOLO11 model on the crime dataset")
print("[INFO] Training time: ~10-15 minutes")
print("[INFO] The model will detect: criminal, person, weapon")

try:
    # Load YOLO11n model
    print("\n[1/3] Loading YOLO11n base model...")
    model = YOLO('yolo11n.pt')
    print("✓ Base model loaded")
    
    # Train on crime dataset
    print("\n[2/3] Starting training...")
    print("[INFO] Epochs: 30 (quick training)")
    print("[INFO] Image size: 640")
    print("[INFO] Device: CPU")
    
    results = model.train(
        data='crime-1/data.yaml',
        epochs=30,
        imgsz=640,
        batch=8,
        name='crime_detection',
        patience=5,
        save=True,
        device='cpu',
        verbose=True
    )
    
    print("\n[3/3] Saving trained model...")
    
    # Copy best model to models directory
    import shutil
    best_model = 'runs/detect/crime_detection/weights/best.pt'
    
    if os.path.exists(best_model):
        shutil.copy(best_model, 'models/crime_best.pt')
        print(f"✓ Model saved to: models/crime_best.pt")
        
        model_size = os.path.getsize('models/crime_best.pt') / (1024 * 1024)
        print(f"  Model size: {model_size:.2f} MB")
    else:
        print("✗ Could not find trained model")
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print("\nThe system will now use this local model for weapon detection")
    print("This should be MUCH more accurate than the Roboflow API")
    
except Exception as e:
    print(f"\n✗ Training failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
