#!/usr/bin/env python3
"""
Test script to simulate browser interaction with Agent Wave
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5009"

def test_browser_simulation():
    """Test what happens when we submit a request through the Agent Wave interface"""
    
    print("=== Browser Simulation Test ===\n")
    
    # Test cases that should trigger LLM tools
    test_cases = [
        {
            "description": "create an email campaign for new product launch",
            "expected_tool": "email-campaign",
            "should_detect": True
        },
        {
            "description": "optimize this content for SEO: AI is transforming business",
            "expected_tool": "seo-optimize", 
            "should_detect": True
        },
        {
            "description": "create a learning path for Python programming",
            "expected_tool": "learning-path",
            "should_detect": True
        },
        {
            "description": "what is the weather today",
            "expected_tool": None,
            "should_detect": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Expected: {'LLM tool detection' if test_case['should_detect'] else 'Regular super-agent'}")
        
        # First, test if the LLM endpoint would work directly
        if test_case['should_detect']:
            print(f"Testing direct LLM endpoint: {test_case['expected_tool']}")
            
            # Create appropriate parameters for each tool
            if test_case['expected_tool'] == 'email-campaign':
                params = {
                    "topic": "new product launch",
                    "audience": "general audience",
                    "campaign_type": "promotional",
                    "tone": "professional"
                }
            elif test_case['expected_tool'] == 'seo-optimize':
                params = {
                    "content": "AI is transforming business",
                    "target_keywords": ["AI", "business"],
                    "content_type": "article"
                }
            elif test_case['expected_tool'] == 'learning-path':
                params = {
                    "subject": "Python programming",
                    "skill_level": "beginner",
                    "learning_style": "mixed",
                    "time_commitment": "moderate"
                }
            
            try:
                response = requests.post(f"{BASE_URL}/api/llm-tools/{test_case['expected_tool']}", json=params, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Direct LLM API working: {result['status']}")
                else:
                    print(f"❌ Direct LLM API failed: {response.status_code}")
            except Exception as e:
                print(f"❌ Direct LLM API error: {e}")
        
        # Now test what the super-agent would do with this request
        print("Testing super-agent endpoint...")
        try:
            super_agent_data = {
                "task_description": test_case['description'],
                "use_advanced_browser": True
            }
            
            response = requests.post(f"{BASE_URL}/api/super-agent/execute-task", json=super_agent_data, timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Super-agent responded: {result.get('status', 'unknown')}")
                if 'session_id' in result:
                    print(f"Session ID: {result['session_id']}")
            else:
                print(f"❌ Super-agent failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Super-agent error: {e}")
        
        print("-" * 50)
    
    print("\n=== Instructions for Manual Testing ===")
    print("1. Open http://127.0.0.1:5009/agent-wave in your browser")
    print("2. Open browser developer tools (F12)")
    print("3. Go to the Console tab")
    print("4. Try typing one of these prompts:")
    print("   - 'create an email campaign for new product launch'")
    print("   - 'optimize this content for SEO: AI is transforming business'")
    print("   - 'create a learning path for Python programming'")
    print("5. Look for console messages starting with:")
    print("   - 'Checking for LLM tool detection with description:'")
    print("   - '✅ Detected LLM tool request' (if working)")
    print("   - '❌ No LLM tool detected' (if not working)")
    print("6. If you see '✅ Detected LLM tool request', the integration is working!")
    print("7. If you see '❌ No LLM tool detected', there might be an issue with the patterns")

if __name__ == "__main__":
    test_browser_simulation()
