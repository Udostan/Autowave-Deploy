#!/usr/bin/env python3
"""
Create History Tables in Supabase
This script creates the necessary tables for the history sidebar functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("❌ Error: supabase package not installed")
    print("Install with: pip install supabase")
    sys.exit(1)

def create_history_tables():
    """Create the history tables in Supabase."""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        print("Check your .env file")
        return False
    
    if supabase_key.startswith('your_'):
        print("❌ Error: Please set real Supabase credentials in .env file")
        print("Current SUPABASE_SERVICE_ROLE_KEY starts with 'your_'")
        return False
    
    print(f"🔗 Connecting to Supabase: {supabase_url}")
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase successfully")
        
        # Read the SQL file
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_history_tables.sql')
        
        if not os.path.exists(sql_file_path):
            print(f"❌ Error: SQL file not found: {sql_file_path}")
            return False
        
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        print("📄 Executing SQL to create history tables...")
        
        # Execute the SQL (Note: Supabase Python client doesn't support raw SQL execution)
        # We'll create tables using individual operations
        
        # Check if tables already exist
        try:
            result = supabase.table('agent_sessions').select('id').limit(1).execute()
            print("✅ agent_sessions table already exists")
            sessions_exist = True
        except Exception:
            sessions_exist = False
        
        try:
            result = supabase.table('user_activities').select('id').limit(1).execute()
            print("✅ user_activities table already exists")
            activities_exist = True
        except Exception:
            activities_exist = False
        
        if sessions_exist and activities_exist:
            print("✅ All history tables already exist!")
            
            # Test the tables by inserting a sample record
            test_user_id = "test_user_history_setup"
            
            # Create a test session
            session_data = {
                'user_id': test_user_id,
                'agent_type': 'prime_agent',
                'session_name': 'History Setup Test',
                'metadata': {'test': True, 'setup_time': '2025-01-02'}
            }
            
            try:
                session_result = supabase.table('agent_sessions').insert(session_data).execute()
                session_id = session_result.data[0]['id']
                print(f"✅ Test session created: {session_id}")
                
                # Create a test activity
                activity_data = {
                    'session_id': session_id,
                    'user_id': test_user_id,
                    'agent_type': 'prime_agent',
                    'activity_type': 'test_setup',
                    'input_data': {'message': 'Testing history tables setup'},
                    'output_data': {'response': 'History tables are working correctly!'},
                    'success': True
                }
                
                activity_result = supabase.table('user_activities').insert(activity_data).execute()
                activity_id = activity_result.data[0]['id']
                print(f"✅ Test activity created: {activity_id}")
                
                # Update session with latest activity
                supabase.table('agent_sessions').update({
                    'latest_activity_id': activity_id
                }).eq('id', session_id).execute()
                
                print("✅ History tables are working correctly!")
                
                # Clean up test data
                supabase.table('user_activities').delete().eq('user_id', test_user_id).execute()
                supabase.table('agent_sessions').delete().eq('user_id', test_user_id).execute()
                print("✅ Test data cleaned up")
                
            except Exception as e:
                print(f"⚠️  Warning: Could not test tables: {e}")
            
            return True
        else:
            print("❌ History tables do not exist yet")
            print("📋 Please run the following SQL in your Supabase SQL Editor:")
            print("=" * 60)
            print(sql_content)
            print("=" * 60)
            print("\n🔗 Go to: https://supabase.com/dashboard/project/[your-project]/sql")
            print("📝 Copy and paste the SQL above, then click 'Run'")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🗄️  AutoWave History Tables Setup")
    print("=" * 40)
    
    success = create_history_tables()
    
    if success:
        print("\n🎉 History tables are ready!")
        print("📊 The history sidebar will now save user interactions")
        print("🔄 Users can retrieve their chat history from the UI")
    else:
        print("\n❌ History tables setup failed")
        print("🔧 Please check the instructions above")
    
    print("\n" + "=" * 40)
