# Quick Start Guide - Smart Surveillance System

## 🚀 Getting Started

### 1. Start the Application

```bash
python app.py
```

The server will start on **http://localhost:5000**

### 2. Open Your Browser

Navigate to: **http://localhost:5000**

You'll see the professional web interface with:
- Configuration panel (left)
- Video feed and stats (right)

## 📹 Testing with Video File

Since you don't have a webcam, here's how to test with a video file:

### Step 1: Select Video Source
1. In the left panel, click on **"Video File"** option
2. Click the **"Choose File"** button
3. Select a video file from your computer (MP4, AVI, MOV, etc.)
4. Wait for the upload to complete

### Step 2: Configure Settings (Optional)
- **Person Detection**: ✓ (enabled by default)
- **Weapon Detection**: ✓ (enabled by default)
- **Behavior Analysis**: ✓ (enabled by default)
- **Crowd Threshold**: 5 (adjust as needed)
- **Confidence Level**: 40% (adjust slider)

### Step 3: Start Surveillance
1. Click the blue **"Start Surveillance"** button
2. The video will start processing
3. Watch the real-time detection in action!

## 📊 What You'll See

### Video Feed
- **Green boxes**: Detected persons (NORMAL)
- **Yellow boxes**: Suspicious behavior
- **Red boxes**: THREAT level
- **Red boxes on objects**: Detected weapons
- **Track IDs**: Unique identifier for each person
- **Behavior scores**: Displayed above each person

### Live Stats
- **Persons Detected**: Current count
- **Threats Detected**: Number of threat-level alerts
- **Weapons Detected**: Count of weapons found
- **FPS**: Processing speed

### Alerts Panel
- Real-time threat notifications
- Timestamp for each alert
- Automatic screenshot capture

## 🎮 Controls

### Video Controls (bottom of video)
- **Pause**: Pause the surveillance
- **Stop**: Stop and return to start
- **Screenshot**: Capture current frame

### Stop Surveillance
Click the red **"Stop Surveillance"** button to end the session

## 📁 Output Files

### Screenshots
Threat-level screenshots are automatically saved to:
```
screenshots/threat_idXX_YYYYMMDD_HHMMSS.jpg
```

### Uploaded Videos
Your uploaded videos are stored in:
```
uploads/your_video_name.mp4
```

## 🎯 Testing Tips

### Good Test Videos
Look for videos with:
- People walking/moving
- Crowded scenes
- Objects that might be detected as weapons (knives, tools)
- Different lighting conditions

### Where to Find Test Videos
- YouTube (download with youtube-dl or similar)
- Free stock video sites (Pexels, Pixabay)
- Your own recorded videos

### Expected Behavior
- **Normal walking**: Green boxes, low scores
- **Erratic movement**: Yellow boxes, medium scores
- **Weapon detected**: Red boxes, high scores, THREAT alert
- **Crowded scene**: Crowd warning if threshold exceeded

## 🔧 Troubleshooting

### Video not uploading
- Check file size (large files take time)
- Ensure video format is supported (MP4, AVI, MOV)
- Check browser console for errors

### No detection showing
- Verify models are loaded (check terminal output)
- Ensure video has people in it
- Try adjusting confidence level

### Slow processing
- Lower the video resolution
- Reduce confidence threshold
- Close other applications

### Connection issues
- Ensure server is running (check terminal)
- Refresh the browser page
- Check if port 5000 is available

## 🌐 CCTV Stream (Advanced)

If you have access to a CCTV camera:

1. Select **"CCTV Stream"**
2. Enter RTSP URL format:
   ```
   rtsp://username:password@192.168.1.100:554/stream1
   ```
3. Click **"Start Surveillance"**

## 📝 Configuration Options

### Restricted Zone
1. Enable **"Restricted Zone"**
2. Enter coordinates (X1, Y1, X2, Y2)
3. Anyone entering this zone gets higher threat score

### Crowd Threshold
- Set the number of people that triggers crowd alert
- Default: 5 people
- Adjust based on your use case

### Confidence Level
- Lower = more detections (may include false positives)
- Higher = fewer detections (more accurate)
- Recommended: 30-50%

## 🎨 Interface Features

### Professional Design
- Dark theme for reduced eye strain
- Color-coded alerts (green/yellow/red)
- Smooth animations
- Responsive layout

### Real-time Updates
- Live video streaming (~30 FPS)
- Instant stat updates
- Immediate threat alerts

## 🛑 Stopping the Server

Press **Ctrl+C** in the terminal to stop the server

## 📞 Support

If you encounter issues:
1. Check the terminal for error messages
2. Verify all dependencies are installed
3. Ensure models are downloaded
4. Check the browser console (F12)

## 🎉 Enjoy!

You now have a fully functional smart surveillance system with:
- ✅ Professional web interface
- ✅ Real-time person detection
- ✅ Weapon detection via Roboflow
- ✅ Behavior analysis
- ✅ Automatic threat alerts
- ✅ Screenshot capture

Test it with your video files and see the AI in action!
