#!/usr/bin/env python3
"""
Quick fix to add the missing file_uploads column to user_activities table
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Add the missing file_uploads column to user_activities table."""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
        return False
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # Add the missing column
        sql_command = """
        ALTER TABLE public.user_activities 
        ADD COLUMN IF NOT EXISTS file_uploads JSONB DEFAULT '[]';
        """
        
        print("🔧 Adding file_uploads column to user_activities table...")
        
        # Execute the SQL command
        try:
            result = supabase.rpc('exec_sql', {'sql': sql_command.strip()}).execute()
            print("✅ Successfully added file_uploads column!")
        except Exception as e:
            print(f"⚠️  RPC method failed: {e}")
            print("📝 Please run this SQL command manually in Supabase SQL editor:")
            print(sql_command)
            return False
        
        # Test the fix by checking if we can query the table
        print("🧪 Testing the fix...")
        try:
            test_result = supabase.table('user_activities').select('id, file_uploads').limit(1).execute()
            print("✅ file_uploads column is now accessible!")
            return True
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Fix completed successfully!")
        print("💡 You can now test the history system again.")
    else:
        print("\n❌ Fix failed. Please add the column manually in Supabase.")
        print("SQL: ALTER TABLE public.user_activities ADD COLUMN IF NOT EXISTS file_uploads JSONB DEFAULT '[]';")
    
    sys.exit(0 if success else 1)
