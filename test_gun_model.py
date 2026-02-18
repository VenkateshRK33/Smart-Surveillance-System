"""
Test the gun detection model from Roboflow Universe
Model: atmaca-iwbjy/gun-detect-occkh
"""
import requests
import base64

api_key = '5LZ8JL3jMBKqnB5Yl2aZ'

print("=" * 60)
print("Testing Guns Detection Model")
print("=" * 60)
print("Model: vtcminiprojectsem4/guns-lprer")
print(f"API Key: {api_key}")
print()

# Try different versions
versions_to_test = [1, 2, 3, 4, 5]

for version in versions_to_test:
    model_id = f"guns-lprer/{version}"
    print(f"Testing version {version}: {model_id}")
    
    try:
        url = f"https://detect.roboflow.com/{model_id}?api_key={api_key}&confidence=20"
        
        # Create a small test image
        test_img = base64.b64encode(b'\xff\xd8\xff\xe0\x00\x10JFIF').decode('utf-8')
        
        response = requests.post(url, data=test_img, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=5)
        
        if response.status_code == 200:
            print(f"  ✓✓✓ SUCCESS! Model is accessible!")
            print(f"  Status: {response.status_code}")
            result = response.json()
            print(f"  Response: {result}")
            print(f"\n  USE THIS MODEL ID: {model_id}")
            break
        elif response.status_code == 403:
            print(f"  ✗ Forbidden (Status: 403)")
        elif response.status_code == 404:
            print(f"  ✗ Not Found (Status: 404)")
        else:
            print(f"  ? Status: {response.status_code}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print()

print("=" * 60)
