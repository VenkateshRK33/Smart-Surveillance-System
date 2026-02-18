"""
Test Roboflow initialization to debug gun detection issue
"""
from roboflow import Roboflow

try:
    print("Testing Roboflow initialization...")
    print("=" * 60)
    
    api_key = 'qkYj4oT3poy5wf50aKm2'
    model_id = 'crime-dp3x3/1'
    
    print(f"API Key: {api_key}")
    print(f"Model ID: {model_id}")
    print()
    
    rf = Roboflow(api_key=api_key)
    print("✓ Roboflow object created")
    
    parts = model_id.split('/')
    project_name, version = parts
    workspace = "bahria-university-g0y7w"
    
    print(f"Workspace: {workspace}")
    print(f"Project: {project_name}")
    print(f"Version: {version}")
    print()
    
    project = rf.workspace(workspace).project(project_name)
    print(f"✓ Project loaded: {project}")
    
    model = project.version(int(version)).model
    print(f"✓ Model loaded: {model}")
    
    print()
    print("=" * 60)
    print("SUCCESS! Roboflow model initialized correctly")
    print("=" * 60)
    
except Exception as e:
    print()
    print("=" * 60)
    print("ERROR! Roboflow initialization failed")
    print("=" * 60)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
