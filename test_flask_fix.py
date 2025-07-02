#!/usr/bin/env python3
"""
Test script to verify Flask application fixes in Agentic Code.
"""

import requests
import json
import time

def test_flask_app_generation():
    """Test Flask application generation with proper port handling."""
    
    print("🧪 Testing Flask App Generation with Port Fix\n")
    
    base_url = "http://localhost:5001"
    
    # Test Flask app generation
    test_prompt = "Create a simple Flask web application with a home page that displays 'Hello World' and a contact form that saves submissions to a JSON file."
    
    try:
        print("📝 Generating Flask application...")
        response = requests.post(
            f"{base_url}/api/agentic-code/process",
            json={
                "message": test_prompt,
                "current_code": "",
                "session_id": "flask_test_session"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Flask app generated successfully")
            
            # Check if the generated code contains proper port configuration
            code = data.get('code', '')
            if 'port=5002' in code:
                print("✅ Port 5002 correctly configured")
            else:
                print("❌ Port 5002 not found in generated code")
                
            if 'FLASK_ENV' not in code:
                print("✅ Deprecated FLASK_ENV not used")
            else:
                print("⚠️  Deprecated FLASK_ENV found in code")
                
            if 'debug=True' in code:
                print("✅ Debug mode properly configured")
            else:
                print("⚠️  Debug mode not found")
                
            # Check for Flask imports
            if 'from flask import' in code or 'import flask' in code:
                print("✅ Flask imports found")
            else:
                print("❌ Flask imports not found")
                
            print(f"\n📄 Generated code preview (first 500 chars):")
            print("-" * 50)
            print(code[:500] + "..." if len(code) > 500 else code)
            print("-" * 50)
            
        else:
            print(f"❌ Generation failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

def test_code_execution():
    """Test code execution with the fixed executor."""
    
    print("\n🚀 Testing Code Execution\n")
    
    base_url = "http://localhost:5001"
    
    # Simple Flask app code with correct port
    flask_code = '''
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Hello World!</h1><p>This Flask app is running on port 5002!</p>"

if __name__ == '__main__':
    app.run(debug=True, port=5002, host="127.0.0.1")
'''
    
    try:
        print("📝 Executing Flask application...")
        response = requests.post(
            f"{base_url}/api/agentic-code/execute",
            json={
                "files": [
                    {
                        "name": "app.py",
                        "content": flask_code
                    }
                ]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            project_id = data.get('project_id')
            print(f"✅ Execution started with project ID: {project_id}")
            
            # Wait a bit and check status
            time.sleep(3)
            
            status_response = requests.get(f"{base_url}/api/agentic-code/status/{project_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                output = status_data.get('status', {}).get('output', '')
                print(f"📊 Execution output:")
                print("-" * 50)
                print(output)
                print("-" * 50)
                
                if "port 5002" in output.lower():
                    print("✅ Port 5002 correctly used")
                if "flask_env" not in output.lower():
                    print("✅ No FLASK_ENV deprecation warnings")
                else:
                    print("⚠️  FLASK_ENV deprecation warnings found")
                    
        else:
            print(f"❌ Execution failed with status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Execution test failed: {str(e)}")

if __name__ == "__main__":
    test_flask_app_generation()
    test_code_execution()
