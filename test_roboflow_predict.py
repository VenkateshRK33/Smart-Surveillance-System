"""
Test different Roboflow prediction methods
"""
from roboflow import Roboflow
import cv2
from PIL import Image
import numpy as np

# Load a test image
frame = cv2.imread('uploads/test 3.mp4')  # This won't work, just for testing
if frame is None:
    # Create a dummy frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

print("Testing Roboflow prediction methods...")
print("=" * 60)

try:
    rf = Roboflow(api_key='qkYj4oT3poy5wf50aKm2')
    project = rf.workspace("bahria-university-g0y7w").project("crime-dp3x3")
    version = project.version(1)
    
    print(f"Version object: {version}")
    print(f"Version type: {type(version)}")
    print(f"Version attributes: {dir(version)}")
    print()
    
    # Check if it has a model attribute
    if hasattr(version, 'model'):
        print(f"Has model attribute: {version.model}")
    
    # Check for predict method
    if hasattr(version, 'predict'):
        print("Has predict method!")
    else:
        print("NO predict method found!")
        
    print()
    print("Available methods:")
    for attr in dir(version):
        if not attr.startswith('_'):
            print(f"  - {attr}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
