#!/usr/bin/env python3
"""
Comprehensive test to verify trial limits for different user types
"""

import requests
import sys
import time

BASE_URL = "http://localhost:5001"

def test_guest_trial_limit():
    """Test that guest users are limited to 1 trial per session"""
    print("🧪 Testing Guest Trial Limit (1 trial expected)...")
    
    session = requests.Session()
    
    try:
        test_payload = {
            "message": "Create a simple HTML page",
            "current_code": "",
            "session_id": "guest_test"
        }
        
        # First trial should work
        response = session.post(f"{BASE_URL}/api/agentic-code/process", json=test_payload, timeout=30)
        print(f"   Guest trial 1: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ First trial failed: {response.text}")
            return False
        
        # Second trial should be blocked
        response = session.post(f"{BASE_URL}/api/agentic-code/process", json=test_payload, timeout=30)
        print(f"   Guest trial 2: {response.status_code}")
        
        if response.status_code == 402:
            result = response.json()
            if result.get('guest_mode'):
                print("   ✅ Guest correctly limited to 1 trial")
                return True
            else:
                print("   ⚠️ Guest mode flag missing")
                return False
        else:
            print(f"   ❌ Second trial should have been blocked")
            return False
            
    except Exception as e:
        print(f"   ❌ Guest trial test failed: {str(e)}")
        return False

def test_multiple_guest_sessions():
    """Test that different guest sessions each get 1 trial"""
    print("\n🧪 Testing Multiple Guest Sessions...")
    
    try:
        test_payload = {
            "message": "Create a simple HTML page",
            "current_code": "",
            "session_id": "guest_test"
        }
        
        # Test 3 different sessions
        for i in range(1, 4):
            session = requests.Session()
            response = session.post(f"{BASE_URL}/api/agentic-code/process", json=test_payload, timeout=30)
            print(f"   Session {i} trial 1: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ Session {i} first trial failed")
                return False
        
        print("   ✅ All guest sessions got their 1 trial")
        return True
        
    except Exception as e:
        print(f"   ❌ Multiple sessions test failed: {str(e)}")
        return False

def test_configuration_consistency():
    """Test that configuration is consistent across files"""
    print("\n🧪 Testing Configuration Consistency...")
    
    try:
        # Check agentic_code.py
        with open('app/api/agentic_code.py', 'r') as f:
            agentic_code_content = f.read()
        
        # Check pricing.html
        with open('app/templates/pricing.html', 'r') as f:
            pricing_content = f.read()
        
        # Verify trial limit in code
        if "@trial_limit('code_wave_daily_trials', 3" in agentic_code_content:
            print("   ✅ Agentic Code configured for 3 trials")
        else:
            print("   ❌ Agentic Code not configured for 3 trials")
            return False
        
        # Verify guest limit in code
        if "guest_limit=1" in agentic_code_content:
            print("   ✅ Guest limit configured for 1 trial")
        else:
            print("   ❌ Guest limit not configured correctly")
            return False
        
        # Verify pricing page
        if "Code Wave - 3 trials per day" in pricing_content:
            print("   ✅ Pricing page shows 3 trials per day")
        else:
            print("   ❌ Pricing page doesn't show 3 trials per day")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {str(e)}")
        return False

def test_admin_bypass():
    """Test that admin bypass is still working"""
    print("\n🧪 Testing Admin Bypass Configuration...")
    
    try:
        # Check paywall decorators
        with open('app/decorators/paywall.py', 'r') as f:
            paywall_content = f.read()
        
        if "admin_service.is_admin" in paywall_content:
            print("   ✅ Admin bypass logic found in paywall decorators")
        else:
            print("   ❌ Admin bypass logic missing")
            return False
        
        # Check admin service
        with open('app/services/admin_service.py', 'r') as f:
            admin_content = f.read()
        
        if 'reffynestan@gmail.com' in admin_content and 'autowave101@gmail.com' in admin_content:
            print("   ✅ Admin emails configured correctly")
        else:
            print("   ❌ Admin emails not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Admin bypass test failed: {str(e)}")
        return False

def main():
    """Run comprehensive trial limit tests"""
    print("🚀 Starting Comprehensive Trial Limit Tests")
    print("=" * 60)
    
    tests = [
        ("Configuration Consistency", test_configuration_consistency),
        ("Admin Bypass Configuration", test_admin_bypass),
        ("Guest Trial Limit", test_guest_trial_limit),
        ("Multiple Guest Sessions", test_multiple_guest_sessions)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)  # Brief pause between tests
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All comprehensive tests passed!")
        print("\n📋 Current Trial Limits:")
        print("   • Guest users: 1 trial per session")
        print("   • Free users: 3 trials per day")
        print("   • Admin users: Unlimited (bypass all restrictions)")
        print("   • Paid users: Unlimited (credit-based)")
        print("\n💡 Recommendations:")
        print("   • Test with a real free user account to verify 3-trial limit")
        print("   • Monitor trial usage in production")
        print("   • Consider adding trial reset notifications")
        return 0
    else:
        print("⚠️ Some comprehensive tests failed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
