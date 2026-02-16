"""
Simple working version - File upload test
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='web')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

@app.route('/api/upload', methods=['POST'])
def upload():
    print("\n" + "="*60)
    print("UPLOAD REQUEST RECEIVED")
    print("="*60)
    print(f"Method: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"Files: {list(request.files.keys())}")
    print(f"Form: {list(request.form.keys())}")
    
    try:
        if 'video' not in request.files:
            print("ERROR: No 'video' in files")
            return jsonify({'status': 'error', 'message': 'No video file'}), 400
        
        file = request.files['video']
        print(f"File: {file.filename}")
        
        if not file.filename:
            return jsonify({'status': 'error', 'message': 'Empty filename'}), 400
        
        os.makedirs('uploads', exist_ok=True)
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        
        print(f"SUCCESS: Saved to {filepath}")
        return jsonify({'status': 'success', 'filepath': filepath})
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("Starting simple test server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
