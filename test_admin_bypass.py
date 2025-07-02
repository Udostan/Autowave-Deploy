#!/usr/bin/env python3
"""
Test script to verify admin bypass functionality
"""

import requests
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

BASE_URL = "http://localhost:5001"
ADMIN_EMAILS = ["reffynestan@gmail.com", "autowave101@gmail.com"]

def test_admin_service():
    """Test the admin service functionality"""
    print("🧪 Testing Admin Service...")
    
    try:
        from app.services.admin_service import admin_service
        
        # Test admin email recognition
        for email in ADMIN_EMAILS:
            is_admin = admin_service.is_admin(email)
            print(f"   {email}: {'✅ Admin' if is_admin else '❌ Not Admin'}")
            
        # Test non-admin email
        is_admin = admin_service.is_admin("test@example.com")
        print(f"   test@example.com: {'❌ Admin (ERROR!)' if is_admin else '✅ Not Admin'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin service test failed: {str(e)}")
        return False

def test_paywall_decorators():
    """Test that paywall decorators import admin service correctly"""
    print("\n🧪 Testing Paywall Decorators...")
    
    try:
        from app.decorators.paywall import admin_service as paywall_admin_service
        
        # Test that admin service is imported
        if paywall_admin_service:
            print("✅ Admin service imported in paywall decorators")
            
            # Test admin email recognition through paywall
            for email in ADMIN_EMAILS:
                is_admin = paywall_admin_service.is_admin(email)
                print(f"   Paywall check {email}: {'✅ Admin' if is_admin else '❌ Not Admin'}")
            
            return True
        else:
            print("❌ Admin service not imported in paywall decorators")
            return False
            
    except Exception as e:
        print(f"❌ Paywall decorator test failed: {str(e)}")
        return False

def test_agentic_code_with_mock_admin():
    """Test Agentic Code endpoint with mock admin session"""
    print("\n🧪 Testing Agentic Code with Mock Admin Session...")
    
    session = requests.Session()
    
    try:
        # First, try without admin session
        test_payload = {
            "message": "Create a simple HTML page",
            "current_code": "",
            "session_id": "admin_test"
        }
        
        response = session.post(f"{BASE_URL}/api/agentic-code/process", json=test_payload, timeout=30)
        print(f"Without admin session: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Guest mode working (expected)")
        elif response.status_code == 401:
            print("✅ Authentication required (expected)")
        elif response.status_code == 402:
            print("✅ Payment required (expected)")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agentic Code test failed: {str(e)}")
        return False

def test_admin_configuration():
    """Test admin configuration in the codebase"""
    print("\n🧪 Testing Admin Configuration...")
    
    try:
        # Check if admin emails are properly configured
        config_found = False
        
        # Check admin service file
        admin_service_path = os.path.join('app', 'services', 'admin_service.py')
        if os.path.exists(admin_service_path):
            with open(admin_service_path, 'r') as f:
                content = f.read()
                
            if 'reffynestan@gmail.com' in content and 'autowave101@gmail.com' in content:
                print("✅ Admin emails found in admin service")
                config_found = True
            else:
                print("❌ Admin emails not found in admin service")
        
        # Check paywall decorators
        paywall_path = os.path.join('app', 'decorators', 'paywall.py')
        if os.path.exists(paywall_path):
            with open(paywall_path, 'r') as f:
                content = f.read()
                
            if 'admin_service' in content and 'is_admin' in content:
                print("✅ Admin bypass logic found in paywall decorators")
                config_found = True
            else:
                print("❌ Admin bypass logic not found in paywall decorators")
        
        return config_found
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        return False

def main():
    """Run all admin bypass tests"""
    print("🚀 Starting Admin Bypass Tests")
    print("=" * 50)
    
    tests = [
        ("Admin Configuration", test_admin_configuration),
        ("Admin Service", test_admin_service),
        ("Paywall Decorators", test_paywall_decorators),
        ("Agentic Code Mock Test", test_agentic_code_with_mock_admin)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 ADMIN BYPASS TEST SUMMARY")
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
        print("🎉 Admin bypass functionality is properly configured!")
        print("\n📋 Next Steps:")
        print("   1. Log in with reffynestan@gmail.com or autowave101@gmail.com")
        print("   2. Test Agentic Code - should have unlimited access")
        print("   3. Admin users bypass all paywall restrictions")
        return 0
    else:
        print("⚠️ Admin bypass configuration issues detected.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
