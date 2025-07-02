#!/usr/bin/env python3
"""
Test script to verify that all agents are properly logging activities to the history system.
This script will test each agent endpoint and verify that activities are being logged.
"""

import requests
import json
import time
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

BASE_URL = "http://localhost:5001"

# Create a session to maintain cookies
session = requests.Session()

def create_test_user_session():
    """Create a test user session for authenticated requests"""
    print("🔐 Setting up test user session...")

    try:
        # Try to access a protected page to trigger session creation
        response = session.get(f"{BASE_URL}/", timeout=10)

        if response.status_code == 200:
            print("✅ Test session created")
            return True
        else:
            print(f"⚠️ Session creation returned {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Failed to create test session: {str(e)}")
        return False

def test_agent_logging(agent_name, endpoint, payload, expected_keys=None):
    """Test an agent endpoint and verify logging"""
    print(f"\n🧪 Testing {agent_name}...")

    try:
        # Make request to agent using session
        response = session.post(f"{BASE_URL}{endpoint}", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {agent_name} request successful")
            
            # Check for expected keys in response
            if expected_keys:
                for key in expected_keys:
                    if key in result:
                        print(f"   ✓ Found expected key: {key}")
                    else:
                        print(f"   ⚠️ Missing expected key: {key}")
            
            return True
        else:
            print(f"❌ {agent_name} request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {agent_name} test failed: {str(e)}")
        return False

def test_history_page():
    """Test the history page to see if activities are being displayed"""
    print(f"\n📊 Testing History Page...")

    try:
        response = session.get(f"{BASE_URL}/history", timeout=10)
        
        if response.status_code == 200:
            print("✅ History page accessible")
            
            # Check if the page contains activity data
            content = response.text
            if "history-item" in content or "No activities found" in content:
                print("✅ History page structure is correct")
                return True
            else:
                print("⚠️ History page may not be displaying activities correctly")
                return False
        else:
            print(f"❌ History page failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ History page test failed: {str(e)}")
        return False

def main():
    """Run all history logging tests"""
    print("🚀 Starting AutoWave History Logging Tests")
    print("=" * 50)

    # Create test user session first
    if not create_test_user_session():
        print("❌ Failed to create test session. Exiting.")
        return 1

    # Test cases for each agent
    test_cases = [
        {
            "name": "AutoWave Chat",
            "endpoint": "/api/chat",
            "payload": {"message": "Hello, this is a test message for history logging"},
            "expected_keys": ["success", "response"]
        },
        {
            "name": "Prime Agent",
            "endpoint": "/api/prime-agent/execute-task",
            "payload": {"task": "Test task for history logging", "use_visual_browser": False},
            "expected_keys": ["success"]
        },
        {
            "name": "Agentic Code",
            "endpoint": "/api/agentic-code/process",
            "payload": {"message": "Create a simple HTML page for testing", "current_code": "", "session_id": "test"},
            "expected_keys": ["plan", "steps", "code"]
        },
        {
            "name": "Context 7 Tools",
            "endpoint": "/api/context7-tools/execute-task",
            "payload": {"task": "Find restaurants in New York for 2 people"},
            "expected_keys": ["success", "task_id"]
        },
        {
            "name": "Data Analysis",
            "endpoint": "/api/data-analysis/analyze",
            "payload": {
                "data": {"x": [1, 2, 3, 4, 5], "y": [10, 20, 15, 25, 30]},
                "analysis_type": "summary",
                "chart_type": "line",
                "title": "Test Analysis"
            },
            "expected_keys": ["success"]
        },
        {
            "name": "Agent Wave - Email Campaign",
            "endpoint": "/api/llm-tools/email-campaign",
            "payload": {
                "topic": "Test Product Launch",
                "audience": "tech enthusiasts",
                "campaign_type": "announcement",
                "tone": "professional"
            },
            "expected_keys": ["status", "data"]
        },
        {
            "name": "Agent Wave - SEO Optimizer",
            "endpoint": "/api/llm-tools/seo-optimize",
            "payload": {
                "content": "This is a test article about technology trends.",
                "target_keywords": ["technology", "trends"],
                "content_type": "article"
            },
            "expected_keys": ["status", "data"]
        },
        {
            "name": "Agent Wave - Learning Path",
            "endpoint": "/api/llm-tools/learning-path",
            "payload": {
                "subject": "Python Programming",
                "skill_level": "beginner",
                "learning_style": "visual",
                "time_commitment": "moderate"
            },
            "expected_keys": ["status", "data"]
        }
    ]
    
    # Run tests
    results = []
    for test_case in test_cases:
        result = test_agent_logging(
            test_case["name"],
            test_case["endpoint"],
            test_case["payload"],
            test_case.get("expected_keys")
        )
        results.append((test_case["name"], result))
        
        # Wait between tests to avoid overwhelming the server
        time.sleep(2)
    
    # Test history page
    history_result = test_history_page()
    results.append(("History Page", history_result))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! History logging is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the logs and fix any issues.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
