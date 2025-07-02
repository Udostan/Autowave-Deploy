#!/usr/bin/env python3
"""
Test script to verify Agentic Code functionality.
"""

import sys
import os
import requests
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_agentic_code_generation():
    """Test Agentic Code generation functionality."""
    
    print("🤖 Testing Agentic Code Generation\n")
    
    # Test cases for different types of apps
    test_cases = [
        {
            "name": "Todo App",
            "prompt": "Create a fully functional todo app with add, edit, delete, and mark complete features. Include local storage and a clean modern UI.",
            "expected_files": ["index.html", "style.css", "script.js"]
        },
        {
            "name": "Calculator App", 
            "prompt": "Build a working calculator app with all basic operations, memory functions, and keyboard support.",
            "expected_files": ["index.html", "style.css", "script.js"]
        },
        {
            "name": "Weather Dashboard",
            "prompt": "Create a weather dashboard that shows current weather and 5-day forecast with search functionality.",
            "expected_files": ["index.html", "style.css", "script.js"]
        }
    ]
    
    base_url = "http://localhost:5001"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📝 Test {i}: {test_case['name']}")
        print(f"   Prompt: {test_case['prompt'][:80]}...")
        
        try:
            # Test the code generation endpoint
            response = requests.post(
                f"{base_url}/api/super-agent/generate-project",
                json={
                    "prompt": test_case["prompt"],
                    "project_type": "web",
                    "complexity": "moderate"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and data.get("files"):
                    files = data["files"]
                    print(f"   ✅ Generated {len(files)} files")
                    
                    # Check if expected files are present
                    file_names = [f["name"] for f in files]
                    missing_files = [f for f in test_case["expected_files"] if f not in file_names]
                    
                    if not missing_files:
                        print(f"   ✅ All expected files present: {', '.join(file_names)}")
                    else:
                        print(f"   ⚠️  Missing files: {', '.join(missing_files)}")
                    
                    # Check if files have substantial content
                    for file in files:
                        content_length = len(file.get("content", ""))
                        if content_length > 500:  # Substantial content
                            print(f"   ✅ {file['name']}: {content_length} characters (substantial)")
                        elif content_length > 100:
                            print(f"   ⚠️  {file['name']}: {content_length} characters (basic)")
                        else:
                            print(f"   ❌ {file['name']}: {content_length} characters (too short)")
                    
                    # Check for functional features in JavaScript
                    js_files = [f for f in files if f["name"].endswith(".js")]
                    if js_files:
                        js_content = js_files[0]["content"]
                        functional_features = []
                        
                        if "addEventListener" in js_content:
                            functional_features.append("Event Listeners")
                        if "localStorage" in js_content:
                            functional_features.append("Local Storage")
                        if "function" in js_content or "=>" in js_content:
                            functional_features.append("Functions")
                        if "document.querySelector" in js_content or "document.getElementById" in js_content:
                            functional_features.append("DOM Manipulation")
                        
                        if functional_features:
                            print(f"   ✅ Functional features: {', '.join(functional_features)}")
                        else:
                            print(f"   ❌ No functional features detected")
                    
                else:
                    print(f"   ❌ Generation failed: {data.get('error', 'Unknown error')}")
            
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {str(e)}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
        
        print()

def test_agentic_code_api():
    """Test the Agentic Code API endpoint."""
    
    print("🔌 Testing Agentic Code API\n")
    
    base_url = "http://localhost:5001"
    
    try:
        # Test a simple request
        response = requests.post(
            f"{base_url}/api/agentic-code/process",
            json={
                "message": "Create a simple button that changes color when clicked",
                "current_code": "",
                "session_id": "test_session"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response received")
            print(f"   Plan: {data.get('plan', 'No plan')[:100]}...")
            print(f"   Steps: {len(data.get('steps', []))} steps")
            
            if data.get('code'):
                print(f"   Code: {len(data['code'])} characters")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API Test failed: {str(e)}")

if __name__ == "__main__":
    test_agentic_code_generation()
    test_agentic_code_api()
