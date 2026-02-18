# Roboflow Weapon Detection Setup Guide

## Current Status
- ✅ API Key Valid: `5LZ8JL3jMBKqnB5Yl2aZ`
- ❌ No access to weapon detection models
- ❌ Gun detection not working

## Problem
The API key doesn't have permission to access private weapon detection models:
- `weapon-c6q7e/1` - Returns 403 Forbidden
- `crime-dp3x3/1` - Returns 403 Forbidden
- `weapon-detection-3qwdf/2` - Returns 403 Forbidden

## Solutions

### Solution 1: Find a Public Model on Roboflow Universe

1. Visit: https://universe.roboflow.com/
2. Search for: "weapon detection" or "gun detection" or "firearm detection"
3. Filter by: **Public models only**
4. Look for models with these classes:
   - gun / pistol / firearm
   - knife
   - rifle
   - handgun

5. Click on a model you like
6. Find the model ID (usually shown as: `workspace-name/project-name/version`)
7. Copy the model ID
8. Update `working_app.py` line 147:
   ```python
   'YOUR-MODEL-ID-HERE'  # Replace with the public model ID
   ```

### Solution 2: Create Your Own Model

1. Go to: https://app.roboflow.com/
2. Sign in with your account (the one with API key `5LZ8JL3jMBKqnB5Yl2aZ`)
3. Click "Create New Project"
4. Choose "Object Detection"
5. Name it: "Weapon Detection"
6. Upload images of:
   - Guns (at least 50-100 images)
   - Knives (at least 50-100 images)
   - Bats (at least 50-100 images)
7. Label/annotate each weapon in the images
8. Click "Generate" to create dataset
9. Click "Train" to train the model
10. Wait for training to complete
11. Click "Deploy"
12. Copy your model ID (format: `your-workspace/weapon-detection/1`)
13. Update `working_app.py` with your model ID

### Solution 3: Use Pre-trained Public Models

Here are some public weapon detection models you can try:

**Option A: Search Roboflow Universe**
```
https://universe.roboflow.com/search?q=weapon+detection
```

**Option B: Try these public model patterns:**
- `roboflow-universe/weapon-detection`
- `public/gun-detection`
- `open-source/firearm-detection`

**To test a model:**
```python
python test_new_api_key.py
# Edit the file to add the model ID you want to test
```

### Solution 4: Request Access to Private Models

If you know who owns the models `weapon-c6q7e/1` or `crime-dp3x3/1`:
1. Contact them
2. Ask them to add your API key to their project
3. They need to:
   - Go to their Roboflow project settings
   - Add your API key to "Allowed API Keys"
   - Or make the model public

## How to Update the Code

Once you have a working model ID:

1. Open `working_app.py`
2. Find line 147:
   ```python
   'weapon-c6q7e/1'  # Current model
   ```
3. Replace with your model ID:
   ```python
   'your-workspace/your-project/1'  # Your model
   ```
4. Restart the server

## Testing Your Model

After updating the model ID:

```bash
python test_new_api_key.py
```

Look for:
- ✓ SUCCESS - Model accessible
- ✗ FORBIDDEN - No access (try different model)

## Current Workaround

Since we don't have access to gun detection models, the system currently:
- ✅ Detects bats (using YOLO)
- ✅ Detects knives (using YOLO)
- ❌ Cannot detect guns (not in YOLO COCO dataset)

## Need Help?

1. Check Roboflow documentation: https://docs.roboflow.com/
2. Roboflow community: https://discuss.roboflow.com/
3. Contact Roboflow support if you have a paid plan

## Alternative: Use YOLOv8 Custom Model

If Roboflow doesn't work, you can:
1. Download a pre-trained weapon detection YOLOv8 model
2. Place it in `models/` folder
3. Update detector to use local model instead of Roboflow
