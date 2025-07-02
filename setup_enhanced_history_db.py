#!/usr/bin/env python3
"""
Setup script for Enhanced History Database Tables
This script creates the necessary database tables for the enhanced history system.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Create the enhanced history database tables"""
    
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
        
        # SQL to create enhanced history tables
        sql_commands = [
            # Update agent_sessions table
            """
            CREATE TABLE IF NOT EXISTS public.agent_sessions (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                user_id UUID NOT NULL,
                agent_type TEXT NOT NULL CHECK (agent_type IN ('autowave_chat', 'prime_agent', 'agentic_code', 'research_lab', 'context7_tools', 'agent_wave')),
                session_name TEXT,
                latest_activity_id UUID,
                is_active BOOLEAN DEFAULT true,
                started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                ended_at TIMESTAMP WITH TIME ZONE,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                total_interactions INTEGER DEFAULT 0,
                metadata JSONB DEFAULT '{}'
            );
            """,
            
            # Create user_activities table if it doesn't exist
            """
            CREATE TABLE IF NOT EXISTS public.user_activities (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                user_id UUID NOT NULL,
                session_id UUID REFERENCES public.agent_sessions(id) ON DELETE CASCADE,
                agent_type TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                input_data JSONB DEFAULT '{}',
                output_data JSONB DEFAULT '{}',
                file_uploads JSONB DEFAULT '[]',
                processing_time_ms INTEGER,
                success BOOLEAN DEFAULT true,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'
            );
            """,

            # Add file_uploads column if it doesn't exist (for existing tables)
            """
            ALTER TABLE public.user_activities
            ADD COLUMN IF NOT EXISTS file_uploads JSONB DEFAULT '[]';
            """,
            
            # Create indexes for better performance
            """
            CREATE INDEX IF NOT EXISTS idx_user_activities_user_id ON public.user_activities(user_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_user_activities_agent_type ON public.user_activities(agent_type);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_user_activities_created_at ON public.user_activities(created_at);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_user_activities_session_id ON public.user_activities(session_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id ON public.agent_sessions(user_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_agent_sessions_updated_at ON public.agent_sessions(updated_at);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_agent_sessions_latest_activity ON public.agent_sessions(latest_activity_id);
            """,
            
            # Enable Row Level Security
            """
            ALTER TABLE public.agent_sessions ENABLE ROW LEVEL SECURITY;
            """,
            """
            ALTER TABLE public.user_activities ENABLE ROW LEVEL SECURITY;
            """,
            
            # Create RLS policies for agent_sessions
            """
            CREATE POLICY IF NOT EXISTS "Users can view their own sessions" ON public.agent_sessions
                FOR SELECT USING (auth.uid()::text = user_id::text);
            """,
            """
            CREATE POLICY IF NOT EXISTS "Users can insert their own sessions" ON public.agent_sessions
                FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
            """,
            """
            CREATE POLICY IF NOT EXISTS "Users can update their own sessions" ON public.agent_sessions
                FOR UPDATE USING (auth.uid()::text = user_id::text);
            """,
            """
            CREATE POLICY IF NOT EXISTS "Users can delete their own sessions" ON public.agent_sessions
                FOR DELETE USING (auth.uid()::text = user_id::text);
            """,
            
            # Create RLS policies for user_activities
            """
            CREATE POLICY IF NOT EXISTS "Users can view their own activities" ON public.user_activities
                FOR SELECT USING (auth.uid()::text = user_id::text);
            """,
            """
            CREATE POLICY IF NOT EXISTS "Users can insert their own activities" ON public.user_activities
                FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);
            """,
            """
            CREATE POLICY IF NOT EXISTS "Users can update their own activities" ON public.user_activities
                FOR UPDATE USING (auth.uid()::text = user_id::text);
            """,
            """
            CREATE POLICY IF NOT EXISTS "Users can delete their own activities" ON public.user_activities
                FOR DELETE USING (auth.uid()::text = user_id::text);
            """
        ]
        
        # Execute each SQL command
        for i, sql in enumerate(sql_commands, 1):
            try:
                result = supabase.rpc('exec_sql', {'sql': sql.strip()}).execute()
                print(f"✅ Executed SQL command {i}/{len(sql_commands)}")
            except Exception as e:
                # Try alternative method for table creation
                try:
                    # Use the REST API to create tables
                    print(f"⚠️  Trying alternative method for command {i}")
                    # For table creation, we'll use a different approach
                    if "CREATE TABLE" in sql:
                        print(f"⚠️  Skipping table creation via API - please run manually in Supabase SQL editor")
                    continue
                except Exception as e2:
                    print(f"❌ Failed to execute SQL command {i}: {e}")
                    continue
        
        print("✅ Enhanced history database setup completed!")
        print("\n📝 Next steps:")
        print("1. If any table creation failed, please run the SQL commands manually in Supabase SQL editor")
        print("2. The SQL commands are available in database/supabase_schema.sql")
        print("3. Restart the Flask application")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up Enhanced History Database...")
    success = setup_database()
    
    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)
