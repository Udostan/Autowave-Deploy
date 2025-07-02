#!/usr/bin/env python3
"""
Test script to verify guest mode functionality for Agentic Code
"""

import requests
import sys

BASE_URL = "http://localhost:5001"

def test_guest_agentic_code():
    """Test Agentic Code with guest mode"""
    print("🧪 Testing Agentic Code Guest Mode...")
    
    session = requests.Session()
    
    try:
        # Test payload for Agentic Code
        test_payload = {
            "message": "Create a simple HTML page with a welcome message",
            "current_code": "",
            "session_id": "guest_test"
        }
        
        # First request - should work for guest
        print("Making first guest request...")
        response = session.post(f"{BASE_URL}/api/agentic-code/process", json=test_payload, timeout=30)
        print(f"First request status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ First guest request successful!")
            result = response.json()
            print(f"   Response keys: {list(result.keys())}")
            
            # Second request - should hit guest limit
            print("\nMaking second guest request...")
            response = session.post(f"{BASE_URL}/api/agentic-code/process", json=test_payload, timeout=30)
            print(f"Second request status: {response.status_code}")
            
            if response.status_code == 402:
                print("✅ Second request correctly blocked (guest limit reached)")
                result = response.json()
                if result.get('guest_mode'):
                    print("✅ Guest mode flag detected in response")
                    return True
                else:
                    print("⚠️ Guest mode flag missing in response")
                    return False
            elif response.status_code == 200:
                print("⚠️ Second request unexpectedly succeeded")
                return False
            else:
                print(f"❌ Unexpected status for second request: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        elif response.status_code == 401:
            print("❌ Guest mode not working - authentication required")
            return False
        elif response.status_code == 402:
            print("❌ Guest mode not working - payment required on first request")
            return False
        else:
            print(f"❌ Unexpected status for first request: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Guest mode test failed: {str(e)}")
        return False

def test_guest_session_persistence():
    """Test that guest session persists across requests"""
    print("\n🧪 Testing Guest Session Persistence...")
    
    session = requests.Session()
    
    try:
        # Make a request to establish guest session
        response = session.get(f"{BASE_URL}/agentic-code", timeout=10)
        print(f"Page access status: {response.status_code}")
        
        # Check if session cookies are set
        cookies = session.cookies.get_dict()
        print(f"Session cookies: {list(cookies.keys())}")
        
        if cookies:
            print("✅ Session cookies established")
            return True
        else:
            print("⚠️ No session cookies found")
            return False
            
    except Exception as e:
        print(f"❌ Session persistence test failed: {str(e)}")
        return False

def main():
    """Run guest mode tests"""
    print("🚀 Starting Agentic Code Guest Mode Tests")
    print("=" * 50)
    
    tests = [
        ("Guest Session Persistence", test_guest_session_persistence),
        ("Guest Agentic Code Access", test_guest_agentic_code)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 GUEST MODE TEST SUMMARY")
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
        print("🎉 Guest mode is working correctly!")
        return 0
    else:
        print("⚠️ Guest mode issues detected.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
