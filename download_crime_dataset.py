"""
Download crime detection dataset from Roboflow
Better weapon detection model
"""
from roboflow import Roboflow

print("=" * 60)
print("DOWNLOADING CRIME DETECTION DATASET")
print("=" * 60)

try:
    print("\n[1/3] Connecting to Roboflow...")
    rf = Roboflow(api_key="qkYj4oT3poy5wf50aKm2")
    print("✓ Connected")
    
    print("\n[2/3] Accessing crime detection dataset...")
    project = rf.workspace("bahria-university-g0y7w").project("crime-dp3x3")
    print("✓ Project accessed: Crime Detection")
    
    print("\n[3/3] Downloading dataset...")
    print("[INFO] This may take a few minutes...")
    version = project.version(1)
    dataset = version.download("yolov11")
    
    print(f"\n✓ Dataset downloaded to: {dataset.location}")
    
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE!")
    print("=" * 60)
    print("\nDataset Details:")
    print("  Workspace: Bahria University")
    print("  Project: Crime Detection")
    print("  Format: YOLO11")
    print("  Classes: Weapons, Crime activities")
    
    print("\nNext: The system will use this dataset for weapon detection")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
