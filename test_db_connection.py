#!/usr/bin/env python3
"""
Test database connection for enhanced history service
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test if we can connect to the database and access tables"""
    
    try:
        from supabase import create_client, Client
        
        # Get Supabase credentials
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not url or not key:
            print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
            return False
        
        print(f"🔗 Connecting to Supabase...")
        print(f"   URL: {url}")
        print(f"   Key: {key[:20]}...")
        
        # Create Supabase client
        supabase: Client = create_client(url, key)
        print("✅ Connected to Supabase")
        
        # Test agent_sessions table
        print("\n📋 Testing agent_sessions table...")
        try:
            sessions_result = supabase.table('agent_sessions').select('*').limit(5).execute()
            print(f"✅ agent_sessions table accessible")
            print(f"   Found {len(sessions_result.data)} sessions")
            for session in sessions_result.data:
                print(f"   - {session.get('session_name', 'Unknown')} ({session.get('agent_type', 'Unknown')})")
        except Exception as e:
            print(f"❌ Error accessing agent_sessions table: {e}")
            return False
        
        # Test user_activities table
        print("\n📋 Testing user_activities table...")
        try:
            activities_result = supabase.table('user_activities').select('*').limit(5).execute()
            print(f"✅ user_activities table accessible")
            print(f"   Found {len(activities_result.data)} activities")
            for activity in activities_result.data:
                print(f"   - {activity.get('activity_type', 'Unknown')} by {activity.get('agent_type', 'Unknown')}")
        except Exception as e:
            print(f"❌ Error accessing user_activities table: {e}")
            return False
        
        # Test inserting a test activity
        print("\n🧪 Testing activity insertion...")
        try:
            test_user_id = "test_user_db_check"
            test_session_id = "test_session_db_check"
            
            # Insert test session
            session_data = {
                'id': test_session_id,
                'user_id': test_user_id,
                'agent_type': 'test_agent',
                'session_name': 'Database Test Session',
                'created_at': '2025-06-08T01:00:00.000000+00:00',
                'updated_at': '2025-06-08T01:00:00.000000+00:00',
                'is_active': True
            }
            
            session_result = supabase.table('agent_sessions').insert(session_data).execute()
            print(f"✅ Test session inserted successfully")
            
            # Insert test activity
            activity_data = {
                'user_id': test_user_id,
                'session_id': test_session_id,
                'agent_type': 'test_agent',
                'activity_type': 'test_activity',
                'input_data': {'test': 'data'},
                'output_data': {'test': 'result'},
                'success': True,
                'created_at': '2025-06-08T01:00:00.000000+00:00'
            }
            
            activity_result = supabase.table('user_activities').insert(activity_data).execute()
            print(f"✅ Test activity inserted successfully")
            
            # Clean up test data
            supabase.table('user_activities').delete().eq('user_id', test_user_id).execute()
            supabase.table('agent_sessions').delete().eq('user_id', test_user_id).execute()
            print(f"✅ Test data cleaned up")
            
        except Exception as e:
            print(f"❌ Error testing insertion: {e}")
            return False
        
        print("\n🎉 Database connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Enhanced History Database Connection...")
    success = test_database_connection()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
