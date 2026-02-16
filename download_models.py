"""
Download required models for Smart Surveillance System
"""
import os
from ultralytics import YOLO

print("=" * 60)
print("DOWNLOADING MODELS FOR SMART SURVEILLANCE SYSTEM")
print("=" * 60)

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

# Download YOLO11n person detection model
print("\n[1/2] Downloading YOLO11n person detection model...")
print("This may take a few minutes depending on your internet speed...")
try:
    model = YOLO('yolo11n.pt')  # This will auto-download
    # Save to models directory
    model.save('models/yolo11n.pt')
    print("✓ YOLO11n model downloaded successfully")
except Exception as e:
    print(f"✗ Failed to download YOLO11n: {e}")

print("\n[2/2] Weapon detection model...")
print("⚠ The weapon detection model (best.pt) needs to be trained or obtained separately.")
print("Options:")
print("  1. Train your own using Roboflow dataset")
print("  2. Use a pre-trained weapon detection model")
print("  3. For testing, the system will work without weapon detection")

print("\n" + "=" * 60)
print("MODEL DOWNLOAD COMPLETED")
print("=" * 60)
print("\nNote: The system will work for person detection and tracking.")
print("Weapon detection will be skipped if best.pt is not available.")
