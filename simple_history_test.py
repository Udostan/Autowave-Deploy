#!/usr/bin/env python3
"""
Simple test to check if the history page is accessible and properly structured.
"""

import requests
import sys

BASE_URL = "http://localhost:5001"

def test_history_page_structure():
    """Test if the history page has the correct structure"""
    print("🧪 Testing History Page Structure...")
    
    try:
        # Test the history page
        response = requests.get(f"{BASE_URL}/history", timeout=10, allow_redirects=False)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ History page redirects to login (expected for unauthenticated users)")
            
            # Check if redirect is to login
            location = response.headers.get('Location', '')
            if 'login' in location.lower() or 'auth' in location.lower():
                print("✅ Redirect is to authentication page")
                return True
            else:
                print(f"⚠️ Unexpected redirect to: {location}")
                return False
                
        elif response.status_code == 200:
            print("✅ History page accessible")
            
            # Check if the page contains expected elements
            content = response.text.lower()
            if 'history' in content and ('activity' in content or 'no activities' in content):
                print("✅ History page contains expected content")
                return True
            else:
                print("⚠️ History page may not have correct structure")
                return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing history page: {str(e)}")
        return False

def test_activity_logger_import():
    """Test if activity logger can be imported"""
    print("\n🧪 Testing Activity Logger Import...")
    
    try:
        sys.path.append('app')
        from app.services.activity_logger import activity_logger
        print("✅ Activity logger imported successfully")
        
        # Check if it has required methods
        if hasattr(activity_logger, 'log_activity'):
            print("✅ Activity logger has log_activity method")
            return True
        else:
            print("❌ Activity logger missing log_activity method")
            return False
            
    except Exception as e:
        print(f"❌ Failed to import activity logger: {str(e)}")
        return False

def test_database_connection():
    """Test if database connection is working"""
    print("\n🧪 Testing Database Connection...")
    
    try:
        sys.path.append('app')
        from app.services.supabase_service import supabase_service
        
        # Try to get user activities (this will test the connection)
        result = supabase_service.get_user_activities('test_user', limit=1)
        print("✅ Database connection working")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def main():
    """Run simple history tests"""
    print("🚀 Starting Simple History Tests")
    print("=" * 40)
    
    tests = [
        ("History Page Structure", test_history_page_structure),
        ("Activity Logger Import", test_activity_logger_import),
        ("Database Connection", test_database_connection)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Print summary
    print("\n" + "=" * 40)
    print("📋 TEST SUMMARY")
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
        print("🎉 All basic tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
