"""
Setup weapon detection using Roboflow with YOLO11
"""
import os

print("=" * 60)
print("ROBOFLOW WEAPON DETECTION SETUP (YOLO11)")
print("=" * 60)

# Install roboflow package
print("\n[1/4] Installing Roboflow package...")
os.system('pip install -q roboflow')

print("\n[2/4] Roboflow Setup Instructions")
print("=" * 60)

print("\nTo use Roboflow weapon detection:")
print("\n1. Create a FREE Roboflow account:")
print("   https://app.roboflow.com/")

print("\n2. Get your API key:")
print("   - Go to Settings > Roboflow API")
print("   - Copy your API key")

print("\n3. Find a weapon detection dataset:")
print("   - Visit: https://universe.roboflow.com/")
print("   - Search: 'weapon detection' or 'gun knife detection'")
print("   - Choose a dataset with good accuracy")

print("\n4. Note the workspace and project names from the URL")
print("   Example: universe.roboflow.com/workspace-name/project-name")

print("\n[3/4] Download Model Code")
print("=" * 60)

print("\nOnce you have your API key and dataset info, run:")
print("""
from roboflow import Roboflow

# Initialize with your API key
rf = Roboflow(api_key="YOUR_API_KEY_HERE")

# Access your project
project = rf.workspace("WORKSPACE_NAME").project("PROJECT_NAME")

# Download the dataset in YOLO11 format
version = project.version(VERSION_NUMBER)
dataset = version.download("yolov11")

# The model will be in the downloaded folder
# Copy the best.pt file to models/best.pt
""")

print("\n[4/4] Alternative: Use Roboflow Inference API")
print("=" * 60)

print("\nYou can also use Roboflow's hosted inference API")
print("This doesn't require downloading the model")
print("\nI can integrate this into the detector if you prefer")

print("\n" + "=" * 60)
print("RECOMMENDED PUBLIC DATASETS")
print("=" * 60)

print("\nPopular weapon detection datasets on Roboflow Universe:")
print("1. 'Weapon Detection' - Multi-class (guns, knives)")
print("2. 'Pistol Detection' - Firearms focused")
print("3. 'Gun and Knife Detection' - Dual-class")
print("4. 'Weapon Image Classification' - Various weapons")

print("\nThese are often available as public datasets")

print("\n" + "=" * 60)
print("NEXT STEPS")
print("=" * 60)

print("\n1. Get your Roboflow API key")
print("2. Choose a weapon detection dataset")
print("3. Provide me with:")
print("   - Your API key")
print("   - Workspace name")
print("   - Project name")
print("   - Version number")


print("\n" + "=" * 60)
