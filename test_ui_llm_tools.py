#!/usr/bin/env python3
"""
Test script to verify LLM tools work through the UI
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5009"

def test_email_campaign_ui():
    """Test email campaign through the UI by simulating the request"""
    print("Testing Email Campaign Manager through UI simulation...")

    # Test the LLM endpoint directly first
    data = {
        "topic": "New Product Launch",
        "audience": "tech enthusiasts",
        "campaign_type": "announcement",
        "tone": "enthusiastic"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/llm-tools/email-campaign", json=data)
        print(f"Direct API Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Email Campaign API working!")
            print(f"Campaign Topic: {result['data']['campaign_topic']}")
            print(f"Subject Lines: {len(result['data']['subject_lines'])} generated")
            return True
        else:
            print(f"❌ API Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_seo_optimization_ui():
    """Test SEO optimization through the UI by simulating the request"""
    print("\nTesting SEO Content Optimizer through UI simulation...")

    data = {
        "content": "This is a sample article about artificial intelligence and machine learning technologies.",
        "target_keywords": ["AI", "machine learning", "artificial intelligence"],
        "content_type": "article"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/llm-tools/seo-optimize", json=data)
        print(f"Direct API Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ SEO Optimization API working!")
            print(f"Original word count: {result['data']['current_analysis']['word_count']}")
            print(f"Optimized word count: {result['data']['optimized_analysis']['word_count']}")
            return True
        else:
            print(f"❌ API Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_learning_path_ui():
    """Test learning path through the UI by simulating the request"""
    print("\nTesting Learning Path Generator through UI simulation...")

    data = {
        "subject": "Python Programming",
        "skill_level": "beginner",
        "learning_style": "visual",
        "time_commitment": "moderate"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/llm-tools/learning-path", json=data)
        print(f"Direct API Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Learning Path API working!")
            print(f"Subject: {result['data']['subject']}")
            print(f"Total modules: {result['data']['curriculum']['total_modules']}")
            return True
        else:
            print(f"❌ API Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_tool_detection():
    """Test the tool detection patterns"""
    print("\nTesting tool detection patterns...")

    test_cases = [
        ("create an email campaign for new product launch", "email-campaign"),
        ("generate email marketing campaign about summer sale", "email-campaign"),
        ("optimize this content for SEO: AI is transforming business", "seo-optimize"),
        ("improve SEO for my blog post", "seo-optimize"),
        ("create a learning path for Python programming", "learning-path"),
        ("how to learn JavaScript step by step", "learning-path"),
        ("study plan for data science", "learning-path"),
        ("regular search query", None)
    ]

    # Since we can't directly test the JavaScript detection, we'll test the patterns
    import re

    def detect_tool_python(description):
        """Python version of the JavaScript detection logic"""
        lowerDesc = description.lower()

        # Email patterns
        email_patterns = [
            r'create\s+(?:an?\s+)?email\s+campaign',
            r'generate\s+(?:an?\s+)?email\s+campaign',
            r'email\s+marketing\s+campaign',
            r'marketing\s+email'
        ]

        for pattern in email_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return 'email-campaign'

        # SEO patterns
        seo_patterns = [
            r'optimize\s+(?:this\s+)?(?:for\s+)?seo',
            r'optimize\s+(?:this\s+)?content',
            r'seo\s+optimization',
            r'improve\s+seo'
        ]

        for pattern in seo_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return 'seo-optimize'

        # Learning patterns
        learning_patterns = [
            r'create\s+(?:a\s+)?learning\s+path',
            r'learning\s+curriculum',
            r'study\s+plan',
            r'how\s+to\s+learn\s+',
            r'learn\s+.+\s+step\s+by\s+step'
        ]

        for pattern in learning_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                return 'learning-path'

        return None

    passed = 0
    total = len(test_cases)

    for description, expected in test_cases:
        detected = detect_tool_python(description)
        if detected == expected:
            print(f"✅ '{description}' -> {detected or 'None'}")
            passed += 1
        else:
            print(f"❌ '{description}' -> Expected: {expected}, Got: {detected}")

    print(f"\nTool Detection: {passed}/{total} tests passed")
    return passed == total

def main():
    """Run all tests"""
    print("=== LLM Tools UI Integration Test ===\n")

    results = []

    # Test direct API endpoints
    results.append(("Email Campaign API", test_email_campaign_ui()))
    results.append(("SEO Optimization API", test_seo_optimization_ui()))
    results.append(("Learning Path API", test_learning_path_ui()))
    results.append(("Tool Detection Logic", test_tool_detection()))

    print(f"\n{'='*50}")
    print("SUMMARY")
    print('='*50)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All LLM tools are working! You can now test them in the UI:")
        print("1. Go to http://127.0.0.1:5009/agent-wave")
        print("2. Try these example prompts:")
        print("   - 'Create an email campaign for new product launch'")
        print("   - 'Optimize this content for SEO: [your content]'")
        print("   - 'Create a learning path for Python programming'")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
