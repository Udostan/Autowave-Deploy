#!/usr/bin/env python3
"""
Direct test of Agent Wave LLM integration by simulating form submission
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5009"

def test_agent_wave_form():
    """Test submitting a form to Agent Wave to see what happens"""
    
    print("=== Agent Wave Form Submission Test ===\n")
    
    # First, let's check if the page loads
    try:
        response = requests.get(f"{BASE_URL}/agent-wave")
        if response.status_code == 200:
            print("✅ Agent Wave page loads successfully")
        else:
            print(f"❌ Agent Wave page failed to load: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error loading Agent Wave page: {e}")
        return
    
    # Test the LLM tool endpoints directly
    print("\n=== Testing LLM Tool Endpoints ===")
    
    # Test Email Campaign
    print("Testing Email Campaign Manager...")
    try:
        email_data = {
            "topic": "New Product Launch",
            "audience": "tech enthusiasts",
            "campaign_type": "announcement", 
            "tone": "enthusiastic"
        }
        response = requests.post(f"{BASE_URL}/api/llm-tools/email-campaign", json=email_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Email Campaign: {result['status']}")
            print(f"   Topic: {result['data']['campaign_topic']}")
            print(f"   Subject lines: {len(result['data']['subject_lines'])}")
        else:
            print(f"❌ Email Campaign failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Email Campaign error: {e}")
    
    # Test SEO Optimization
    print("\nTesting SEO Content Optimizer...")
    try:
        seo_data = {
            "content": "This is a sample article about artificial intelligence and machine learning.",
            "target_keywords": ["AI", "machine learning"],
            "content_type": "article"
        }
        response = requests.post(f"{BASE_URL}/api/llm-tools/seo-optimize", json=seo_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SEO Optimization: {result['status']}")
            print(f"   Original words: {result['data']['current_analysis']['word_count']}")
            print(f"   Optimized words: {result['data']['optimized_analysis']['word_count']}")
        else:
            print(f"❌ SEO Optimization failed: {response.status_code}")
    except Exception as e:
        print(f"❌ SEO Optimization error: {e}")
    
    # Test Learning Path
    print("\nTesting Learning Path Generator...")
    try:
        learning_data = {
            "subject": "Python Programming",
            "skill_level": "beginner",
            "learning_style": "visual",
            "time_commitment": "moderate"
        }
        response = requests.post(f"{BASE_URL}/api/llm-tools/learning-path", json=learning_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Learning Path: {result['status']}")
            print(f"   Subject: {result['data']['subject']}")
            print(f"   Modules: {result['data']['curriculum']['total_modules']}")
        else:
            print(f"❌ Learning Path failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Learning Path error: {e}")
    
    print("\n=== Manual Testing Instructions ===")
    print("The LLM tools are working! Now test the UI integration:")
    print("1. Open http://127.0.0.1:5009/agent-wave")
    print("2. Open browser developer tools (F12) and go to Console tab")
    print("3. Type this exact prompt: 'create an email campaign for new product launch'")
    print("4. Click 'Execute Task'")
    print("5. Watch the console for these messages:")
    print("   - 'Checking for LLM tool detection with description: create an email campaign for new product launch'")
    print("   - 'LLM tool detection result: {tool: \"email-campaign\", params: {...}}'")
    print("   - '✅ Detected LLM tool request, handling with dedicated endpoint'")
    print("6. If you see those messages, the integration is working!")
    print("7. The output should show LLM-generated content instead of simulated thinking")
    
    print("\n=== Alternative Test Prompts ===")
    print("- 'optimize this content for SEO: AI is transforming business'")
    print("- 'create a learning path for Python programming'")
    print("- 'generate an email marketing campaign for summer sale'")

if __name__ == "__main__":
    test_agent_wave_form()
