"""
Download weapon detection model from Roboflow
Dataset: SwifEye weapon detection
"""
from roboflow import Roboflow
import os
import shutil

print("=" * 60)
print("DOWNLOADING WEAPON DETECTION MODEL FROM ROBOFLOW")
print("=" * 60)

try:
    # Initialize Roboflow with API key
    print("\n[1/4] Connecting to Roboflow...")
    rf = Roboflow(api_key="qkYj4oT3poy5wf50aKm2")
    print("✓ Connected to Roboflow")
    
    # Access the weapon detection project
    print("\n[2/4] Accessing weapon detection dataset...")
    project = rf.workspace("swifeye").project("weapon-c6q7e")
    print("✓ Project accessed: SwifEye weapon detection")
    
    # Get the latest version and download in YOLO11 format
    print("\n[3/4] Downloading model (this may take a few minutes)...")
    version = project.version(1)
    dataset = version.download("yolov11")
    
    print("✓ Dataset downloaded")
    
    # Find and copy the trained model to models directory
    print("\n[4/4] Setting up model...")
    
    # The downloaded dataset should contain weights
    # Look for best.pt in the downloaded folder
    downloaded_path = dataset.location
    
    # Common locations for the model file
    possible_paths = [
        os.path.join(downloaded_path, "weights", "best.pt"),
        os.path.join(downloaded_path, "best.pt"),
        os.path.join(downloaded_path, "train", "weights", "best.pt"),
    ]
    
    model_found = False
    for path in possible_paths:
        if os.path.exists(path):
            # Create models directory if it doesn't exist
            os.makedirs('models', exist_ok=True)
            
            # Copy the model
            shutil.copy(path, 'models/best.pt')
            print(f"✓ Model copied to: models/best.pt")
            print(f"  Source: {path}")
            model_found = True
            break
    
    if not model_found:
        print("\n⚠ Model file not found in expected locations")
        print(f"Dataset downloaded to: {downloaded_path}")
        print("Please manually copy the best.pt file to models/best.pt")
    else:
        # Check model file size
        model_size = os.path.getsize('models/best.pt') / (1024 * 1024)
        print(f"  Model size: {model_size:.2f} MB")
    
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\nModel Details:")
    print(f"  Workspace: SwifEye")
    print(f"  Project: weapon-c6q7e")
    print(f"  Format: YOLO11")
    print(f"  Location: models/best.pt")
    
    print("\nYou can now run the surveillance system with weapon detection:")
    print("  python main.py")
    
except Exception as e:
    print(f"\n✗ Error downloading model: {e}")
    print("\nTroubleshooting:")
    print("1. Check your internet connection")
    print("2. Verify the API key is correct")
    print("3. Ensure the dataset is accessible")
    print("4. Try downloading manually from:")
    print("   https://universe.roboflow.com/swifeye/weapon-c6q7e")

print("\n" + "=" * 60)
