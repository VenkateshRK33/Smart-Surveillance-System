"""
Test new Roboflow API key: 5LZ8JL3jMBKqnB5Yl2aZ
"""
from roboflow import Roboflow
import requests

api_key = '5LZ8JL3jMBKqnB5Yl2aZ'

print("=" * 60)
print("Testing Roboflow API Key")
print("=" * 60)
print(f"API Key: {api_key}")
print()

# Test 1: Check if API key is valid
print("[Test 1] Checking API key validity...")
try:
    rf = Roboflow(api_key=api_key)
    print("✓ API key is valid - Roboflow object created")
except Exception as e:
    print(f"✗ API key invalid: {e}")
    exit(1)

print()

# Test 2: Try to access weapon detection models
print("[Test 2] Testing weapon detection models...")
print()

models_to_test = [
    ('weapon-c6q7e/1', 'SwifEye Weapon Detection'),
    ('crime-dp3x3/1', 'Crime Detection'),
    ('weapon-detection-3qwdf/2', 'Generic Weapon Detection'),
]

for model_id, model_name in models_to_test:
    print(f"Testing: {model_name} ({model_id})")
    try:
        # Test with HTTP API
        url = f"https://detect.roboflow.com/{model_id}?api_key={api_key}&confidence=20"
        
        # Create a small test image (1x1 pixel)
        import base64
        test_img = base64.b64encode(b'\xff\xd8\xff\xe0\x00\x10JFIF').decode('utf-8')
        
        response = requests.post(url, data=test_img, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=5)
        
        if response.status_code == 200:
            print(f"  ✓ SUCCESS - Model accessible (Status: {response.status_code})")
            result = response.json()
            print(f"  Response: {result}")
        elif response.status_code == 403:
            print(f"  ✗ FORBIDDEN - No access to this model (Status: 403)")
        elif response.status_code == 404:
            print(f"  ✗ NOT FOUND - Model doesn't exist (Status: 404)")
        else:
            print(f"  ? UNKNOWN - Status: {response.status_code}")
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
    
    print()

print("=" * 60)
print("Test Complete")
print("=" * 60)
