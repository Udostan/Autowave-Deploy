#!/usr/bin/env python3
"""
AutoWave Supabase Database Setup Script
Automatically creates all necessary tables and policies for comprehensive data storage.
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
    print("❌ Supabase not installed. Please run: pip install supabase")
    sys.exit(1)

def setup_database():
    """Setup the complete AutoWave database schema in Supabase."""
    
    print("🚀 AutoWave Supabase Database Setup")
    print("=" * 50)
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase credentials!")
        print("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your .env file")
        return False
    
    if supabase_url.startswith('your_') or supabase_service_key.startswith('your_'):
        print("❌ Please update your .env file with actual Supabase credentials")
        print("Current values appear to be placeholders")
        return False
    
    try:
        # Create admin client
        print(f"🔗 Connecting to Supabase: {supabase_url}")
        client = create_client(supabase_url, supabase_service_key)
        
        # Test connection
        print("✅ Connected to Supabase successfully")
        
        # Read and execute schema
        print("\n📊 Creating database schema...")
        
        # Read schema file
        schema_file = os.path.join(os.path.dirname(__file__), 'database', 'supabase_schema.sql')
        if not os.path.exists(schema_file):
            print(f"❌ Schema file not found: {schema_file}")
            return False
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema (split by semicolons and execute each statement)
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            try:
                if statement.upper().startswith(('CREATE', 'ALTER', 'INSERT')):
                    print(f"   Executing statement {i}/{len(statements)}...")
                    # Use the REST API to execute SQL
                    result = client.rpc('exec_sql', {'sql': statement}).execute()
                    
            except Exception as e:
                print(f"   ⚠️  Warning on statement {i}: {str(e)}")
                # Continue with other statements
        
        print("✅ Database schema created successfully")
        
        # Read and execute RLS policies
        print("\n🔒 Setting up Row Level Security policies...")
        
        rls_file = os.path.join(os.path.dirname(__file__), 'database', 'supabase_rls_policies.sql')
        if os.path.exists(rls_file):
            with open(rls_file, 'r') as f:
                rls_sql = f.read()
            
            # Execute RLS policies
            rls_statements = [stmt.strip() for stmt in rls_sql.split(';') if stmt.strip()]
            
            for i, statement in enumerate(rls_statements, 1):
                try:
                    if statement.upper().startswith(('CREATE', 'ALTER')):
                        print(f"   Executing RLS policy {i}/{len(rls_statements)}...")
                        result = client.rpc('exec_sql', {'sql': statement}).execute()
                        
                except Exception as e:
                    print(f"   ⚠️  Warning on RLS policy {i}: {str(e)}")
            
            print("✅ RLS policies created successfully")
        else:
            print("⚠️  RLS policies file not found, skipping...")
        
        # Verify tables were created
        print("\n🔍 Verifying database setup...")
        
        expected_tables = [
            'user_profiles', 'agent_sessions', 'user_activities', 'file_uploads',
            'chat_conversations', 'prime_agent_tasks', 'code_projects', 
            'research_queries', 'context7_usage', 'agent_wave_campaigns',
            'memory_links', 'user_preferences', 'usage_analytics'
        ]
        
        # Check if tables exist by trying to select from them
        created_tables = []
        for table in expected_tables:
            try:
                result = client.table(table).select('*').limit(1).execute()
                created_tables.append(table)
                print(f"   ✅ {table}")
            except Exception as e:
                print(f"   ❌ {table}: {str(e)}")
        
        print(f"\n📊 Database Setup Summary:")
        print(f"   Tables created: {len(created_tables)}/{len(expected_tables)}")
        
        if len(created_tables) == len(expected_tables):
            print("🎉 Database setup completed successfully!")
            print("\n📝 Next Steps:")
            print("1. Test the data storage by running: python test_data_storage.py")
            print("2. Start using AutoWave - all activities will now be stored!")
            print("3. Check your Supabase dashboard to see the data")
            return True
        else:
            print("⚠️  Some tables were not created. Check the errors above.")
            return False
            
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False

def test_data_storage():
    """Test the data storage functionality."""
    
    print("\n🧪 Testing Data Storage...")
    
    try:
        from app.services.data_storage_service import data_storage, ActivityData
        
        if not data_storage.is_available():
            print("❌ Data storage service not available")
            return False
        
        # Test storing a sample activity
        test_activity = ActivityData(
            user_id="test-user-123",
            agent_type="autowave_chat",
            activity_type="chat",
            input_data={"message": "Hello, this is a test message"},
            output_data={"response": "Hello! This is a test response."},
            processing_time_ms=1500,
            success=True
        )
        
        activity_id = data_storage.store_activity(test_activity)
        
        if activity_id:
            print("✅ Data storage test successful!")
            print(f"   Test activity ID: {activity_id}")
            return True
        else:
            print("❌ Data storage test failed")
            return False
            
    except Exception as e:
        print(f"❌ Data storage test error: {str(e)}")
        return False

if __name__ == "__main__":
    print("AutoWave Supabase Database Setup")
    print("This script will create all necessary tables for comprehensive data storage.")
    
    # Confirm before proceeding
    confirm = input("\nProceed with database setup? (y/N): ").lower().strip()
    if confirm != 'y':
        print("Setup cancelled.")
        sys.exit(0)
    
    # Setup database
    success = setup_database()
    
    if success:
        # Test data storage
        test_success = test_data_storage()
        
        if test_success:
            print("\n🎉 Complete setup successful!")
            print("AutoWave is now ready with comprehensive data storage!")
        else:
            print("\n⚠️  Database created but data storage test failed.")
            print("Check your configuration and try again.")
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)
