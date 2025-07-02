#!/usr/bin/env python3
"""
Test Flask code generation without execution to verify the fixes.
"""

import requests
import json

def test_flask_code_generation():
    """Test Flask code generation and verify the improvements."""
    
    print("🧪 Testing Flask Code Generation Improvements\n")
    
    base_url = "http://localhost:5001"
    
    # Test Flask app generation
    test_prompt = "Create a Flask web application with a contact form that saves submissions to a JSON file"
    
    try:
        print("📝 Generating Flask application...")
        response = requests.post(
            f"{base_url}/api/agentic-code/process",
            json={
                "message": test_prompt,
                "current_code": "",
                "session_id": "flask_generation_test"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            code = data.get('code', '')
            
            print("✅ Flask app generated successfully")
            print(f"📄 Generated {len(code)} characters of code")
            
            # Check for improvements
            checks = [
                ("Flask imports", any(imp in code for imp in ['from flask import', 'import flask'])),
                ("Port configuration", 'port=' in code and ('5002' in code or 'find_port' in code)),
                ("No FLASK_ENV", 'FLASK_ENV' not in code),
                ("use_reloader=False", 'use_reloader=False' in code),
                ("Host binding", 'host=' in code and '127.0.0.1' in code),
                ("Socket handling", 'socket' in code or 'find_port' in code or 'find_available_port' in code),
                ("Error handling", 'try:' in code and 'except' in code),
                ("JSON handling", 'json' in code),
                ("Form handling", 'request.form' in code or 'POST' in code),
                ("Route definitions", '@app.route' in code)
            ]
            
            print("\n🔍 Code Quality Checks:")
            for check_name, passed in checks:
                status = "✅" if passed else "❌"
                print(f"   {status} {check_name}")
            
            # Count passed checks
            passed_count = sum(1 for _, passed in checks if passed)
            total_checks = len(checks)
            
            print(f"\n📊 Quality Score: {passed_count}/{total_checks} ({passed_count/total_checks*100:.1f}%)")
            
            if passed_count >= 8:
                print("🎉 Excellent! Flask generation is working properly.")
            elif passed_count >= 6:
                print("👍 Good! Flask generation has most improvements.")
            else:
                print("⚠️  Flask generation needs more improvements.")
            
            # Show a sample of the generated code
            print(f"\n📄 Code Sample (first 800 characters):")
            print("-" * 60)
            print(code[:800] + "..." if len(code) > 800 else code)
            print("-" * 60)
            
            return True
            
        else:
            print(f"❌ Generation failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_different_flask_prompts():
    """Test different Flask-related prompts to ensure proper detection."""
    
    print("\n🎯 Testing Flask Detection with Different Prompts\n")
    
    base_url = "http://localhost:5001"
    
    test_prompts = [
        "Create a Flask API for user management",
        "Build a Python web application using Flask",
        "Make a contact form with Flask backend",
        "Create a Flask web app with database",
        "Build a REST API using Flask"
    ]
    
    results = []
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"📝 Test {i}: {prompt[:50]}...")
        
        try:
            response = requests.post(
                f"{base_url}/api/agentic-code/process",
                json={
                    "message": prompt,
                    "current_code": "",
                    "session_id": f"flask_detection_test_{i}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                code = data.get('code', '')
                language = data.get('language', 'unknown')
                
                is_flask = any(indicator in code.lower() for indicator in [
                    'from flask import', 'import flask', 'app = flask', '@app.route'
                ])
                
                has_port_config = 'port=' in code and ('5002' in code or 'find_port' in code)
                
                result = {
                    'prompt': prompt,
                    'language': language,
                    'is_flask': is_flask,
                    'has_port_config': has_port_config,
                    'code_length': len(code)
                }
                
                results.append(result)
                
                status = "✅" if is_flask and has_port_config else "⚠️" if is_flask else "❌"
                print(f"   {status} Language: {language}, Flask: {is_flask}, Port Config: {has_port_config}")
                
            else:
                print(f"   ❌ Failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Summary
    flask_detected = sum(1 for r in results if r['is_flask'])
    port_configured = sum(1 for r in results if r['has_port_config'])
    
    print(f"\n📊 Detection Summary:")
    print(f"   Flask detected: {flask_detected}/{len(results)} prompts")
    print(f"   Port configured: {port_configured}/{len(results)} prompts")
    
    if flask_detected >= 4 and port_configured >= 4:
        print("🎉 Excellent Flask detection and configuration!")
    elif flask_detected >= 3:
        print("👍 Good Flask detection!")
    else:
        print("⚠️  Flask detection needs improvement.")

if __name__ == "__main__":
    success = test_flask_code_generation()
    if success:
        test_different_flask_prompts()
    
    print("\n✅ Flask generation testing completed!")
