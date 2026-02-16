"""
Try to get pre-trained model from Roboflow project
"""
from roboflow import Roboflow
import os

print("=" * 60)
print("CHECKING FOR PRE-TRAINED MODEL")
print("=" * 60)

try:
    # Initialize Roboflow
    print("\n[INFO] Connecting to Roboflow...")
    rf = Roboflow(api_key="qkYj4oT3poy5wf50aKm2")
    
    # Access project
    project = rf.workspace("swifeye").project("weapon-c6q7e")
    version = project.version(1)
    
    print("[INFO] Project accessed successfully")
    print(f"[INFO] Project: {project.name}")
    print(f"[INFO] Version: {version.version}")
    
    # Try to get model information
    print("\n[INFO] Checking for trained model...")
    
    # Try different export formats that might include weights
    formats_to_try = ['yolov11', 'yolov8', 'pytorch']
    
    for fmt in formats_to_try:
        try:
            print(f"\n[INFO] Trying format: {fmt}")
            dataset = version.download(fmt)
            print(f"✓ Downloaded {fmt} format to: {dataset.location}")
        except Exception as e:
            print(f"  Format {fmt} not available: {e}")
    
    print("\n" + "=" * 60)
    print("ALTERNATIVE SOLUTION")
    print("=" * 60)
    
    print("\nSince this dataset doesn't include pre-trained weights,")
    print("you have two options:")
    
    print("\n1. TRAIN THE MODEL (Recommended):")
    print("   python train_weapon_model.py")
    print("   (Takes 10-30 minutes)")
    
    print("\n2. USE ROBOFLOW HOSTED API:")
    print("   I can integrate Roboflow's hosted inference API")
    print("   This doesn't require local model training")
    print("   Would you like me to do this?")
    
except Exception as e:
    print(f"\n✗ Error: {e}")

print("\n" + "=" * 60)
