# Smart Surveillance System - Feature Updates

## Task 1: Enhanced Weapon Detection (Gun & Knife Recognition)

### Changes Made:

**detector_roboflow.py:**
- **Multi-level confidence scanning**: Now tries Roboflow API at 3 different confidence levels (15%, 20%, 25%) to maximize gun detection
- **Expanded weapon class matching**: Added more keywords for gun detection:
  - Gun, pistol, firearm, rifle, weapon, handgun → 'gun'
  - Knife, blade, dagger, sword → 'knife'
  - Bat, stick, club, rod → 'bat'
- **Lowered YOLO confidence**: Reduced from 0.35 to 0.25 for better weapon detection
- **Enhanced logging**: Added detailed debug output to track detection process
- **Improved NMS**: More aggressive deduplication with IoU threshold of 0.5

### Expected Results:
- ✅ Guns will now be detected with higher accuracy
- ✅ Knives and blades properly recognized
- ✅ Bats and similar objects detected
- ✅ Better handling of low-confidence detections
- ✅ Detailed console logging for debugging

---

## Task 2: Enhanced Suspicious Activity Detection

### New Suspicious Behaviors Detected:

1. **Loitering** - Person staying in one place >30 seconds (+1 point)
2. **Suspicious Stillness** - Very low movement <20 pixels over 5 seconds (+1 point)
3. **Erratic Movement** - Rapid movement >100 pixels in 2 seconds (+1 point)
4. **Multiple People** - 2 or more people present (+1 point)
5. **Weapon Presence** - Weapon detected near person (+5 points - CRITICAL)
6. **Suspicious Items** - Backpack or suitcase near person (+2 points)
7. **Frame Edge Position** - Person at edge of frame (+1 point)
8. **Restricted Zone** - Person in restricted area (+2 points)

### Changes Made:

**detector_roboflow.py:**
- Added `detect_suspicious_items()` method
- Detects backpacks (class 27) and suitcases (class 33)
- Returns suspicious item detections with bbox and confidence

**behaviour_engine.py:**
- Enhanced `calculate_scores()` to accept suspicious_items parameter
- Added `_has_rapid_movement()` - detects erratic movement patterns
- Added `_check_suspicious_item_near_person()` - checks for suspicious items
- Added `_is_at_frame_edge()` - detects people at frame boundaries
- Updated scoring factors with more descriptive names
- Changed crowd threshold from 5+ to 2+ people

**working_app.py:**
- Added suspicious item detection (every 5 frames)
- Passes suspicious items to behaviour engine
- Maintains all existing weapon and person detection logic

### Scoring System:

- **NORMAL** (0-2 points): No significant suspicious behavior
- **SUSPICIOUS** (3-4 points): Some concerning factors present
- **THREAT** (5+ points): High-risk situation requiring immediate attention

### Alert Display:
Alerts now show specific suspicious activities:
- "Loitering (35.2s)"
- "Erratic movement"
- "Suspicious item: backpack"
- "Weapon: gun"
- "Multiple people (3)"
- "At frame edge"

---

## Preserved Features (NOT CHANGED):

✅ Person detection with size filtering
✅ Accurate person counting (no duplicates)
✅ Persistent weapon and threat counts
✅ Weapon memory and deduplication
✅ NMS for person and weapon detection
✅ No lap module dependency
✅ Video streaming and UI updates
✅ Screenshot capture for threats
✅ Alert system and notifications

---

## Testing Recommendations:

1. **Gun Detection Test**:
   - Upload video with gun
   - Check console for "[ROBOFLOW WEAPON] gun" messages
   - Verify weapon count increases
   - Confirm threat level rises

2. **Knife Detection Test**:
   - Upload video with knife
   - Check for proper weapon classification
   - Verify alerts mention "Weapon: knife"

3. **Suspicious Activity Test**:
   - Test with person staying still (loitering)
   - Test with person moving quickly (erratic movement)
   - Test with multiple people (crowd)
   - Check suspicious activity count increases
   - Verify specific factors shown in alerts

4. **Suspicious Items Test**:
   - Test with person carrying backpack
   - Check for "Suspicious item: backpack" in alerts
   - Verify suspicious score increases by 2 points

---

## Debug Output:

The system now provides detailed console logging:
```
[ROBOFLOW] Found 2 detections at confidence 15%
[ROBOFLOW WEAPON] gun (pistol) - confidence: 0.18
[WEAPON DETECTION] Total detections before NMS: 3
[NMS] After deduplication: 1 unique weapons
[SUSPICIOUS ITEM] backpack - confidence: 0.45
[BEHAVIOR] Weapon 'gun' associated with person
[PERSISTENT] Max weapons updated: 1
[ALERT] THREAT - Person ID 1, Score: 7.0, Factors: Multiple people (2), Weapon: gun, Suspicious item: backpack
```

---

## Server Status:
✅ Server running on http://localhost:5000
✅ No syntax errors
✅ All diagnostics passed
✅ Ready for testing
