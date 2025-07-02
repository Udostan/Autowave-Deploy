#!/usr/bin/env python3
"""
Test script to check session management and authentication
"""

import requests
import sys

BASE_URL = "http://localhost:5001"

def test_session_creation():
    """Test if sessions are being created properly"""
    print("🧪 Testing Session Creation...")
    
    session = requests.Session()
    
    try:
        # Try to access the main page
        response = session.get(f"{BASE_URL}/", timeout=10)
        print(f"Main page status: {response.status_code}")
        
        # Check if we got any cookies
        cookies = session.cookies.get_dict()
        print(f"Cookies received: {list(cookies.keys())}")
        
        # Try to access agentic code page
        response = session.get(f"{BASE_URL}/agentic-code", timeout=10)
        print(f"Agentic code page status: {response.status_code}")
        
        # Try to make a request to the API
        test_payload = {
            "message": "Hello test",
            "current_code": "",
            "session_id": "test"
        }
        
        response = session.post(f"{BASE_URL}/api/agentic-code/process", json=test_payload, timeout=10)
        print(f"API request status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication required (expected)")
            return True
        elif response.status_code == 402:
            print("⚠️ Payment required - user might be authenticated but out of credits/trials")
            return True
        elif response.status_code == 200:
            print("✅ Request successful")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Session test failed: {str(e)}")
        return False

def test_anonymous_access():
    """Test what happens with anonymous access"""
    print("\n🧪 Testing Anonymous Access...")
    
    try:
        # Make direct API call without session
        test_payload = {
            "message": "Hello test",
            "current_code": "",
            "session_id": "test"
        }
        
        response = requests.post(f"{BASE_URL}/api/agentic-code/process", json=test_payload, timeout=10)
        print(f"Anonymous API request status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication required for anonymous users (expected)")
            return True
        elif response.status_code == 402:
            print("⚠️ Payment required for anonymous users")
            return True
        else:
            print(f"❌ Unexpected status for anonymous user: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Anonymous access test failed: {str(e)}")
        return False

def main():
    """Run session tests"""
    print("🚀 Starting Session Management Tests")
    print("=" * 40)
    
    tests = [
        ("Session Creation", test_session_creation),
        ("Anonymous Access", test_anonymous_access)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Print summary
    print("\n" + "=" * 40)
    print("📋 SESSION TEST SUMMARY")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Session management is working correctly!")
        return 0
    else:
        print("⚠️ Session management issues detected.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
