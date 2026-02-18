// Smart Surveillance System - Frontend JavaScript

// WebSocket connection
let socket = null;

// State management
const state = {
    isRunning: false,
    source: 'webcam',
    stats: {
        persons: 0,
        threats: 0,
        weapons: 0,
        fps: 0
    },
    uploadedFile: null
};

// DOM Elements
const elements = {
    startBtn: document.getElementById('startBtn'),
    statusBadge: document.getElementById('statusBadge'),
    videoPlaceholder: document.getElementById('videoPlaceholder'),
    videoCanvas: document.getElementById('videoCanvas'),
    videoControls: document.getElementById('videoControls'),
    cctvInput: document.getElementById('cctvInput'),
    videoInput: document.getElementById('videoInput'),
    videoFile: document.getElementById('videoFile'),
    uploadBox: document.getElementById('uploadBox'),
    fileInfo: document.getElementById('fileInfo'),
    fileName: document.getElementById('fileName'),
    fileStatus: document.getElementById('fileStatus'),
    changeFileBtn: document.getElementById('changeFileBtn'),
    enableZone: document.getElementById('enableZone'),
    zoneConfig: document.getElementById('zoneConfig'),
    personCount: document.getElementById('personCount'),
    suspiciousCount: document.getElementById('suspiciousCount'),
    threatCount: document.getElementById('threatCount'),
    weaponCount: document.getElementById('weaponCount'),
    fpsCount: document.getElementById('fpsCount'),
    alertsList: document.getElementById('alertsList')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeWebSocket();
    updateUI();
});

function initializeWebSocket() {
    // Connect to WebSocket server
    socket = io('http://localhost:5000');
    
    socket.on('connect', () => {
        console.log('Connected to server');
        updateStatus('Connected', 'success');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateStatus('Disconnected', 'danger');
    });
    
    socket.on('frame', (data) => {
        // Update video canvas with new frame
        updateVideoFrame(data.image);
        
        // Update stats
        if (data.stats) {
            updateStats(data.stats);
        }
    });
    
    socket.on('alert', (data) => {
        // Add alert to panel
        addAlert(data.type, data.message, data.time);
    });
    
    socket.on('status', (data) => {
        console.log('Status:', data);
        if (data.status === 'error') {
            showNotification(data.message, 'error');
        }
    });
}

function initializeEventListeners() {
    // Source selection
    document.querySelectorAll('input[name="source"]').forEach(radio => {
        radio.addEventListener('change', handleSourceChange);
    });

    // Start button
    elements.startBtn.addEventListener('click', handleStartStop);

    // Video controls
    document.getElementById('pauseBtn').addEventListener('click', handlePause);
    document.getElementById('stopBtn').addEventListener('click', handleStop);
    document.getElementById('screenshotBtn').addEventListener('click', handleScreenshot);

    // File input - improved upload UI
    elements.uploadBox.addEventListener('click', () => {
        elements.videoFile.click();
    });
    
    elements.videoFile.addEventListener('change', handleFileSelect);
    
    elements.changeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetFileUpload();
        elements.videoFile.click();
    });

    // Zone toggle
    elements.enableZone.addEventListener('change', (e) => {
        elements.zoneConfig.style.display = e.target.checked ? 'block' : 'none';
    });
}

function handleSourceChange(e) {
    state.source = e.target.value;
    
    // Hide all inputs
    elements.cctvInput.style.display = 'none';
    elements.videoInput.style.display = 'none';
    
    // Show relevant input
    if (state.source === 'cctv') {
        elements.cctvInput.style.display = 'block';
    } else if (state.source === 'video') {
        elements.videoInput.style.display = 'block';
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        // Show file info
        elements.uploadBox.style.display = 'none';
        elements.fileInfo.style.display = 'flex';
        elements.fileName.textContent = file.name;
        elements.fileStatus.textContent = 'Uploading...';
        elements.fileStatus.className = 'file-status uploading';
        
        state.uploadedFile = file;
        
        // Upload file to server
        uploadVideoFile(file);
    }
}

function resetFileUpload() {
    elements.uploadBox.style.display = 'block';
    elements.fileInfo.style.display = 'none';
    elements.videoFile.value = '';
    state.uploadedFile = null;
    state.uploadedFilePath = null;
}

async function uploadVideoFile(file) {
    const formData = new FormData();
    formData.append('video', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        // Check if response is ok
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned non-JSON response');
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            elements.fileStatus.textContent = 'Ready to analyze';
            elements.fileStatus.className = 'file-status success';
            state.uploadedFilePath = data.filepath;
            showNotification('Video uploaded successfully', 'success');
        } else {
            elements.fileStatus.textContent = 'Upload failed';
            elements.fileStatus.className = 'file-status error';
            showNotification('Upload failed: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        elements.fileStatus.textContent = 'Upload failed';
        elements.fileStatus.className = 'file-status error';
        showNotification('Upload error: ' + error.message, 'error');
    }
}

function handleStartStop() {
    if (state.isRunning) {
        stopSurveillance();
    } else {
        startSurveillance();
    }
}

function startSurveillance() {
    // Validate input
    if (state.source === 'cctv' && !document.getElementById('cctvUrl').value) {
        showNotification('Please enter RTSP/HTTP URL', 'error');
        return;
    }
    
    if (state.source === 'video' && !state.uploadedFilePath) {
        showNotification('Please upload a video file first', 'error');
        return;
    }
    
    state.isRunning = true;
    updateUI();
    
    // Show video canvas
    elements.videoPlaceholder.style.display = 'none';
    elements.videoCanvas.style.display = 'block';
    elements.videoControls.style.display = 'flex';
    
    // Update status
    updateStatus('Starting...', 'warning');
    
    // Get configuration
    const config = getConfiguration();
    
    // Send start command via WebSocket
    socket.emit('start_surveillance', config);
    
    updateStatus('Running', 'success');
}

function getConfiguration() {
    return {
        source: state.source,
        sourceUrl: state.source === 'cctv' ? document.getElementById('cctvUrl').value : null,
        sourceFile: state.source === 'video' ? state.uploadedFilePath : null,
        personDetection: document.getElementById('personDetection').checked,
        weaponDetection: document.getElementById('weaponDetection').checked,
        behaviorAnalysis: document.getElementById('behaviorAnalysis').checked,
        restrictedZone: elements.enableZone.checked ? {
            x1: parseInt(document.getElementById('zoneX1').value) || 0,
            y1: parseInt(document.getElementById('zoneY1').value) || 0,
            x2: parseInt(document.getElementById('zoneX2').value) || 0,
            y2: parseInt(document.getElementById('zoneY2').value) || 0
        } : null
    };
}

function stopSurveillance() {
    state.isRunning = false;
    updateUI();
    
    // Send stop command
    socket.emit('stop_surveillance');
    
    // Hide video canvas
    elements.videoPlaceholder.style.display = 'flex';
    elements.videoCanvas.style.display = 'none';
    elements.videoControls.style.display = 'none';
    
    // Update status
    updateStatus('Ready', 'success');
    
    // Reset stats
    resetStats();
    
    // Show notification with option to re-upload
    if (state.source === 'video') {
        showNotification('Analysis complete. You can upload a new video.', 'success');
    }
}

function updateVideoFrame(base64Image) {
    const canvas = elements.videoCanvas;
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
    };
    img.src = 'data:image/jpeg;base64,' + base64Image;
}

function handlePause() {
    if (state.isRunning) {
        updateStatus('Paused', 'warning');
        // Implement pause logic
    }
}

function handleStop() {
    stopSurveillance();
}

function handleScreenshot() {
    const canvas = elements.videoCanvas;
    const link = document.createElement('a');
    link.download = `surveillance_${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
    
    showAlert('Screenshot saved', 'success');
}

function updateUI() {
    if (state.isRunning) {
        elements.startBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12"></rect>
            </svg>
            Stop Surveillance
        `;
        elements.startBtn.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
    } else {
        elements.startBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            Start Surveillance
        `;
        elements.startBtn.style.background = 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)';
    }
}

function updateStatus(text, type) {
    const badge = elements.statusBadge;
    const dot = badge.querySelector('.status-dot');
    const span = badge.querySelector('span');
    
    span.textContent = text;
    
    if (type === 'success') {
        dot.style.background = '#10b981';
    } else if (type === 'warning') {
        dot.style.background = '#f59e0b';
    } else if (type === 'danger') {
        dot.style.background = '#ef4444';
    }
}

function updateStats(stats) {
    elements.personCount.textContent = stats.persons;
    elements.suspiciousCount.textContent = stats.suspicious || 0;
    elements.threatCount.textContent = stats.threats;
    elements.weaponCount.textContent = stats.weapons;
    elements.fpsCount.textContent = stats.fps;
}

function resetStats() {
    state.stats = { persons: 0, threats: 0, weapons: 0, fps: 0 };
    updateStats(state.stats);
}

function addAlert(type, message, time) {
    const alertsList = elements.alertsList;
    
    // Remove empty state
    const emptyState = alertsList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const alertItem = document.createElement('div');
    alertItem.className = 'alert-item';
    alertItem.innerHTML = `
        <div class="alert-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
        </div>
        <div class="alert-content">
            <h4>${type}</h4>
            <p>${message}</p>
        </div>
        <div class="alert-time">${time}</div>
    `;
    
    alertsList.insertBefore(alertItem, alertsList.firstChild);
    
    // Keep only last 10 alerts
    while (alertsList.children.length > 10) {
        alertsList.removeChild(alertsList.lastChild);
    }
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function connectToBackend() {
    // Deprecated - using WebSocket now
    console.log('Using WebSocket connection');
}

// Remove simulation functions
// startStatsSimulation() is no longer needed
