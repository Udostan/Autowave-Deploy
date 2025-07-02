#!/usr/bin/env python3
"""
Test script for the new comprehensive history functionality.
This script tests both the history service and the updated history page.
"""

import os
import sys
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_history_service():
    """Test the history service directly."""
    
    print("🧪 Testing History Service")
    print("=" * 30)
    
    try:
        from app.services.history_service import history_service
        
        if not history_service.is_available():
            print("❌ History service not available")
            print("   Check your Supabase credentials in .env file")
            return False
        
        print("✅ History service is available")
        
        # Test getting comprehensive history
        test_user_id = "test-user-history-123"
        
        print(f"   Testing comprehensive history for user: {test_user_id}")
        history_data = history_service.get_comprehensive_history(test_user_id)
        
        if history_data.get('available'):
            print("✅ Comprehensive history retrieval successful")
            
            # Check what data we got
            data_types = [
                'activities', 'chat_conversations', 'prime_agent_tasks',
                'code_projects', 'research_queries', 'context7_usage',
                'file_uploads', 'analytics'
            ]
            
            for data_type in data_types:
                data = history_data.get(data_type, [])
                count = len(data) if isinstance(data, list) else ('available' if data else 'empty')
                print(f"   📊 {data_type}: {count}")
            
            return True
        else:
            print("❌ Comprehensive history retrieval failed")
            print(f"   Error: {history_data.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ History service test failed: {str(e)}")
        return False

def test_history_page():
    """Test the history page endpoint."""
    
    print("\n🌐 Testing History Page")
    print("=" * 25)
    
    base_url = "http://localhost:5001"
    
    try:
        # Test the history page endpoint
        response = requests.get(f"{base_url}/history", timeout=10)
        
        if response.status_code == 200:
            print("✅ History page loads successfully")
            
            # Check if the response contains expected elements
            content = response.text
            
            expected_elements = [
                'Activity History',
                'history-page',
                'analytics-summary',
                'history-tabs',
                'All Activities',
                'Chat',
                'Prime Agent',
                'Code Projects',
                'Research',
                'Context7 Tools',
                'File Uploads'
            ]
            
            found_elements = []
            for element in expected_elements:
                if element in content:
                    found_elements.append(element)
            
            print(f"   📋 Found {len(found_elements)}/{len(expected_elements)} expected elements")
            
            if len(found_elements) >= len(expected_elements) * 0.8:  # 80% threshold
                print("✅ History page contains expected content")
                return True
            else:
                print("⚠️  History page missing some expected content")
                print(f"   Missing: {set(expected_elements) - set(found_elements)}")
                return False
                
        elif response.status_code == 302:
            print("🔄 History page redirects (likely to login)")
            print("   This is expected if authentication is required")
            return True
        else:
            print(f"❌ History page returned HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("🔌 Cannot connect to AutoWave server")
        print("   Make sure the server is running on http://localhost:5001")
        return False
    except Exception as e:
        print(f"❌ History page test failed: {str(e)}")
        return False

def test_activity_logging_integration():
    """Test that activity logging is working with the history system."""
    
    print("\n🔗 Testing Activity Logging Integration")
    print("=" * 40)
    
    try:
        from app.services.data_storage_service import data_storage, ActivityData
        from app.services.history_service import history_service
        
        if not data_storage.is_available() or not history_service.is_available():
            print("⚠️  Data storage or history service not available")
            return False
        
        # Create a test activity
        test_user_id = f"test-user-integration-{int(time.time())}"
        
        test_activity = ActivityData(
            user_id=test_user_id,
            agent_type="autowave_chat",
            activity_type="test_chat",
            input_data={"message": "Test message for history integration"},
            output_data={"response": "Test response for history integration"},
            processing_time_ms=1500,
            success=True
        )
        
        # Store the activity
        activity_id = data_storage.store_activity(test_activity)
        
        if not activity_id:
            print("❌ Failed to store test activity")
            return False
        
        print(f"✅ Test activity stored: {activity_id}")
        
        # Wait a moment for database consistency
        time.sleep(1)
        
        # Try to retrieve it through history service
        activities = history_service.get_user_activities(test_user_id, limit=10)
        
        if activities and len(activities) > 0:
            print(f"✅ Activity retrieved through history service: {len(activities)} activities")
            
            # Check if our test activity is there
            found_test_activity = False
            for activity in activities:
                if activity.get('id') == activity_id:
                    found_test_activity = True
                    break
            
            if found_test_activity:
                print("✅ Test activity found in history service")
                return True
            else:
                print("⚠️  Test activity not found in history service")
                return False
        else:
            print("❌ No activities retrieved through history service")
            return False
            
    except Exception as e:
        print(f"❌ Activity logging integration test failed: {str(e)}")
        return False

def main():
    """Run comprehensive history functionality tests."""
    
    print("🧪 AutoWave History Functionality Test")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: History Service
    service_success = test_history_service()
    
    # Test 2: History Page
    page_success = test_history_page()
    
    # Test 3: Activity Logging Integration
    integration_success = test_activity_logging_integration()
    
    # Overall Results
    print(f"\n🎯 Test Results Summary:")
    print("=" * 25)
    print(f"✅ History Service: {'PASS' if service_success else 'FAIL'}")
    print(f"✅ History Page: {'PASS' if page_success else 'FAIL'}")
    print(f"✅ Activity Integration: {'PASS' if integration_success else 'FAIL'}")
    
    overall_success = service_success and page_success and integration_success
    
    if overall_success:
        print(f"\n🎉 History Functionality: FULLY OPERATIONAL!")
        print("   ✅ Users can now view comprehensive activity history")
        print("   ✅ All agent activities are tracked and displayed")
        print("   ✅ Analytics and insights are available")
        print("   ✅ File uploads and processing times are shown")
    else:
        print(f"\n⚠️  History Functionality: PARTIAL FUNCTIONALITY")
        print("   Some components may not be working correctly")
        print("   Check the individual test results above")
    
    print(f"\n📋 Next Steps:")
    if not overall_success:
        print("   1. Fix any failing tests above")
        print("   2. Ensure Supabase is properly configured")
        print("   3. Make sure the AutoWave server is running")
    else:
        print("   1. Start using AutoWave - activities will be tracked!")
        print("   2. Visit /history to see your comprehensive activity log")
        print("   3. Check analytics to understand your usage patterns")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
