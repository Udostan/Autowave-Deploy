#!/usr/bin/env python3
"""
Test script for LLM-powered tools API endpoints
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5009"

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/llm-tools/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_capabilities():
    """Test the capabilities endpoint"""
    print("\nTesting capabilities endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/llm-tools/capabilities")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_email_campaign():
    """Test the email campaign endpoint"""
    print("\nTesting email campaign endpoint...")
    try:
        data = {
            "topic": "New Product Launch",
            "audience": "tech enthusiasts",
            "campaign_type": "announcement",
            "tone": "enthusiastic"
        }
        response = requests.post(f"{BASE_URL}/api/llm-tools/email-campaign", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            if 'data' in result:
                print("Email campaign generated successfully!")
                # Print just the subject lines to verify it worked
                if 'subject_lines' in result['data']:
                    print(f"Subject lines: {result['data']['subject_lines'][:2]}...")
        else:
            print(f"Error response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_learning_path():
    """Test the learning path endpoint"""
    print("\nTesting learning path endpoint...")
    try:
        data = {
            "subject": "Python Programming",
            "skill_level": "beginner",
            "learning_style": "visual",
            "time_commitment": "moderate"
        }
        response = requests.post(f"{BASE_URL}/api/llm-tools/learning-path", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            if 'data' in result:
                print("Learning path generated successfully!")
                # Print curriculum info
                if 'curriculum' in result['data']:
                    curriculum = result['data']['curriculum']
                    print(f"Total modules: {curriculum.get('total_modules', 'N/A')}")
        else:
            print(f"Error response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_seo_optimization():
    """Test the SEO optimization endpoint"""
    print("\nTesting SEO optimization endpoint...")
    try:
        data = {
            "content": "This is a sample article about artificial intelligence and machine learning.",
            "target_keywords": ["AI", "machine learning", "artificial intelligence"],
            "content_type": "article"
        }
        response = requests.post(f"{BASE_URL}/api/llm-tools/seo-optimize", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            if 'data' in result:
                print("SEO optimization completed successfully!")
        else:
            print(f"Error response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=== LLM Tools API Test Suite ===\n")
    
    tests = [
        ("Health Check", test_health),
        ("Capabilities", test_capabilities),
        ("Email Campaign", test_email_campaign),
        ("Learning Path", test_learning_path),
        ("SEO Optimization", test_seo_optimization)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        success = test_func()
        results.append((test_name, success))
        print(f"\n{test_name}: {'✅ PASSED' if success else '❌ FAILED'}")
    
    print(f"\n{'='*50}")
    print("SUMMARY")
    print('='*50)
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
