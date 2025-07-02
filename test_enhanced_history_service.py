#!/usr/bin/env python3
"""
Test the enhanced history service directly to identify database issues
"""

import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_enhanced_history_service():
    """Test the enhanced history service directly"""
    
    try:
        from services.enhanced_history_service import enhanced_history_service
        
        print("🚀 Testing Enhanced History Service...")
        
        # Test if service is available
        print(f"📊 Service available: {enhanced_history_service.is_available()}")
        
        # Test logging an activity
        print("\n🧪 Testing activity logging...")
        test_user_id = str(uuid.uuid4())  # Use proper UUID
        
        try:
            activity_id = enhanced_history_service.log_activity(
                user_id=test_user_id,
                agent_type='agent_wave',
                activity_type='test_activity',
                input_data={'task_description': 'Direct service test'},
                output_data={'result': 'Test result'},
                success=True
            )
            
            print(f"✅ Activity logged successfully: {activity_id}")
            
            # Test getting unified history
            print(f"\n📋 Testing unified history for user: {test_user_id}")
            history = enhanced_history_service.get_unified_history(test_user_id, limit=10)
            
            print(f"📊 Found {len(history)} history items")
            for item in history:
                print(f"   - {item.get('session_name', 'Unknown')} ({item.get('agent_type', 'Unknown')})")
            
            # Check if our activity appears
            found_our_activity = any(
                item.get('session_id') != 'demo-1' and 
                item.get('session_id') != 'demo-2' and 
                item.get('session_id') != 'demo-3'
                for item in history
            )
            
            if found_our_activity:
                print("✅ Our test activity appears in history!")
            else:
                print("❌ Our test activity does NOT appear in history")
                print("   This indicates the activity wasn't actually stored in the database")
            
        except Exception as e:
            print(f"❌ Error testing activity logging: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test database connection directly
        print("\n🔗 Testing direct database connection...")
        try:
            from supabase import create_client, Client
            
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not url or not key:
                print("❌ Missing Supabase credentials")
                return False
            
            supabase: Client = create_client(url, key)
            
            # Try to query activities with our test user_id
            activities_result = supabase.table('user_activities').select('*').eq('user_id', test_user_id).execute()
            
            print(f"📊 Direct database query found {len(activities_result.data)} activities for our test user")
            
            if activities_result.data:
                print("✅ Activity was stored in database!")
                for activity in activities_result.data:
                    print(f"   - {activity.get('activity_type')} by {activity.get('agent_type')}")
            else:
                print("❌ No activities found in database for our test user")
                print("   This confirms the database insertion is failing")
            
        except Exception as e:
            print(f"❌ Error testing direct database connection: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing enhanced history service: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_history_service()
    
    if success:
        print("\n✅ Enhanced history service test completed!")
    else:
        print("\n❌ Enhanced history service test failed!")
    
    sys.exit(0 if success else 1)
