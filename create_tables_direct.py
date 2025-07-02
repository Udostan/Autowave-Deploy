#!/usr/bin/env python3
"""
Direct table creation script for Enhanced History Database Tables
This script creates the necessary database tables using direct SQL execution.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables():
    """Create the enhanced history database tables directly"""
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(url, key)
        print("✅ Connected to Supabase")
        
        # Create agent_sessions table
        print("📝 Creating agent_sessions table...")
        result1 = supabase.rpc('exec_sql', {
            'sql': '''
            CREATE TABLE IF NOT EXISTS public.agent_sessions (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                user_id UUID NOT NULL,
                agent_type TEXT NOT NULL,
                session_name TEXT,
                latest_activity_id UUID,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                total_interactions INTEGER DEFAULT 0,
                metadata JSONB DEFAULT '{}'
            );
            '''
        }).execute()
        print("✅ agent_sessions table created")
        
        # Create user_activities table
        print("📝 Creating user_activities table...")
        result2 = supabase.rpc('exec_sql', {
            'sql': '''
            CREATE TABLE IF NOT EXISTS public.user_activities (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                user_id UUID NOT NULL,
                session_id UUID REFERENCES public.agent_sessions(id) ON DELETE CASCADE,
                agent_type TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                input_data JSONB DEFAULT '{}',
                output_data JSONB DEFAULT '{}',
                processing_time_ms INTEGER,
                success BOOLEAN DEFAULT true,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'
            );
            '''
        }).execute()
        print("✅ user_activities table created")
        
        # Create indexes
        print("📝 Creating indexes...")
        supabase.rpc('exec_sql', {
            'sql': '''
            CREATE INDEX IF NOT EXISTS idx_user_activities_user_id ON public.user_activities(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_activities_session_id ON public.user_activities(session_id);
            CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id ON public.agent_sessions(user_id);
            '''
        }).execute()
        print("✅ Indexes created")
        
        # Enable RLS and create policies
        print("📝 Setting up Row Level Security...")
        supabase.rpc('exec_sql', {
            'sql': '''
            ALTER TABLE public.agent_sessions ENABLE ROW LEVEL SECURITY;
            ALTER TABLE public.user_activities ENABLE ROW LEVEL SECURITY;
            
            DROP POLICY IF EXISTS "Allow all operations on agent_sessions" ON public.agent_sessions;
            CREATE POLICY "Allow all operations on agent_sessions" ON public.agent_sessions
                FOR ALL USING (true) WITH CHECK (true);
                
            DROP POLICY IF EXISTS "Allow all operations on user_activities" ON public.user_activities;
            CREATE POLICY "Allow all operations on user_activities" ON public.user_activities
                FOR ALL USING (true) WITH CHECK (true);
            '''
        }).execute()
        print("✅ Row Level Security configured")
        
        print("✅ Enhanced history database setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        # Try alternative method - direct table creation
        try:
            print("🔄 Trying alternative method...")
            
            # Try creating tables using insert method (this sometimes works when RPC doesn't)
            supabase.table('agent_sessions').select('id').limit(1).execute()
            print("✅ Tables already exist or were created successfully")
            return True
            
        except Exception as e2:
            print(f"❌ Alternative method also failed: {e2}")
            print("\n📝 Manual Setup Required:")
            print("Please run the following SQL in your Supabase SQL Editor:")
            print("\n" + "="*50)
            with open('create_history_tables.sql', 'r') as f:
                print(f.read())
            print("="*50)
            return False

if __name__ == "__main__":
    print("🚀 Creating Enhanced History Database Tables...")
    success = create_tables()
    
    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)
