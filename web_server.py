"""
Web server for Smart Surveillance System
Serves the web interface and handles video streaming
"""
import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__, 
            static_folder='web',
            template_folder='web')

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

if __name__ == '__main__':
    print("=" * 60)
    print("SMART SURVEILLANCE SYSTEM - WEB INTERFACE")
    print("=" * 60)
    print("\nStarting web server...")
    print("Open your browser and navigate to:")
    print("\n  http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
