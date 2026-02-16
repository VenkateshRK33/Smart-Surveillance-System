# Smart Surveillance System - Web Interface

## 🎨 Professional Web GUI

A modern, professional web interface for the Smart Surveillance System built with HTML, CSS, and JavaScript.

## ✨ Features

### Design
- **Dark Theme**: Professional dark mode interface with blue accents
- **Responsive Layout**: Works on desktop, tablet, and mobile
- **Modern UI**: Clean, minimalist design with smooth animations
- **Real-time Stats**: Live updates for persons, threats, weapons, and FPS
- **Alert System**: Real-time threat notifications

### Functionality
- **Multiple Video Sources**:
  - Webcam (default camera)
  - CCTV Stream (RTSP/HTTP)
  - Video File Upload
  
- **Detection Settings**:
  - Toggle person detection
  - Toggle weapon detection
  - Toggle behavior analysis
  - Adjustable crowd threshold
  - Confidence level slider

- **Restricted Zone**:
  - Enable/disable restricted zones
  - Define zone coordinates
  
- **Video Controls**:
  - Play/Pause
  - Stop
  - Screenshot capture

## 🚀 Getting Started

### 1. Start the Web Server

```bash
python web_server.py
```

### 2. Open Your Browser

Navigate to: **http://localhost:5000**

### 3. Configure Settings

1. **Select Video Source**:
   - Choose Webcam, CCTV Stream, or Video File
   - For CCTV: Enter RTSP URL (e.g., `rtsp://username:password@ip:port/stream`)
   - For Video: Click "Choose File" and select your video

2. **Configure Detection**:
   - Enable/disable detection features
   - Set crowd threshold (default: 5 people)
   - Adjust confidence level (default: 40%)

3. **Optional - Restricted Zone**:
   - Enable restricted zone
   - Enter coordinates (X1, Y1, X2, Y2)

### 4. Start Surveillance

Click the **"Start Surveillance"** button

## 📊 Dashboard Features

### Stats Cards
- **Persons Detected**: Real-time count of people in frame
- **Threats Detected**: Number of threat-level alerts
- **Weapons Detected**: Count of weapons identified
- **FPS**: Current processing speed

### Video Feed
- Live video stream with detection overlays
- Bounding boxes for persons and weapons
- Color-coded threat levels (green/yellow/red)

### Alerts Panel
- Real-time threat notifications
- Timestamp for each alert
- Scrollable history (last 10 alerts)

## 🎨 Color Scheme

- **Primary**: Blue (#2563eb) - Actions, highlights
- **Success**: Green (#10b981) - Normal status, persons
- **Warning**: Orange (#f59e0b) - Suspicious activity
- **Danger**: Red (#ef4444) - Threats, weapons
- **Background**: Dark slate (#0f172a, #1e293b)
- **Text**: Light slate (#f1f5f9, #cbd5e1)

## 🔧 Technical Details

### Frontend Stack
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with gradients, animations
- **Vanilla JavaScript**: No frameworks, pure JS

### Backend Integration
- **Flask**: Python web server
- **WebSocket**: Real-time communication (to be implemented)
- **Video Streaming**: Frame-by-frame processing

## 📱 Responsive Design

The interface adapts to different screen sizes:
- **Desktop**: Full layout with sidebar
- **Tablet**: Stacked layout
- **Mobile**: Single column, optimized controls

## 🎯 Usage Tips

### For Testing with Video Files
1. Select "Video File" option
2. Click "Choose File"
3. Select a video with people/weapons
4. Click "Start Surveillance"
5. Watch real-time detection

### For CCTV Streams
1. Select "CCTV Stream"
2. Enter RTSP URL format:
   - `rtsp://username:password@192.168.1.100:554/stream1`
   - `http://192.168.1.100:8080/video`
3. Click "Start Surveillance"

### For Webcam
1. Select "Webcam" (default)
2. Click "Start Surveillance"
3. Allow camera access when prompted

## 🔒 Security Notes

- The web server runs on localhost by default
- For production, use a proper WSGI server (gunicorn, uwsgi)
- Implement authentication for remote access
- Use HTTPS for secure streaming

## 🎬 Next Steps

To fully integrate the backend:
1. Implement WebSocket connection in `script.js`
2. Create video streaming endpoint in Python
3. Send detection results to frontend
4. Update canvas with processed frames

## 📝 Customization

### Change Colors
Edit `web/styles.css` and modify the `:root` variables:
```css
:root {
    --primary: #2563eb;  /* Change primary color */
    --bg-primary: #0f172a;  /* Change background */
}
```

### Modify Layout
Edit `web/index.html` to add/remove sections

### Add Features
Edit `web/script.js` to add new functionality

## 🐛 Troubleshooting

### Server won't start
- Check if port 5000 is available
- Try a different port: `app.run(port=8000)`

### Can't access from other devices
- Server runs on `0.0.0.0` (all interfaces)
- Check firewall settings
- Use your local IP: `http://192.168.1.X:5000`

### Video not showing
- Check browser console for errors
- Ensure video source is valid
- Verify camera permissions

## 📄 License

Part of the Smart Surveillance System project.
