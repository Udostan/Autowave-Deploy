#!/usr/bin/env python3
"""
Create missing database tables for AutoWave Supabase integration
This script creates the user_profiles table and other essential tables.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    print("🚀 Creating Missing AutoWave Database Tables")
    print("=" * 50)
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)
    
    print(f"🔗 Connecting to Supabase: {supabase_url}")
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase successfully")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)
    
    # SQL commands to create missing tables
    sql_commands = [
        # 1. Create user_profiles table
        """
        CREATE TABLE IF NOT EXISTS public.user_profiles (
            id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
            email TEXT NOT NULL,
            full_name TEXT,
            avatar_url TEXT,
            preferences JSONB DEFAULT '{}',
            subscription_tier TEXT DEFAULT 'free',
            total_activities INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        # 2. Create subscription_plans table
        """
        CREATE TABLE IF NOT EXISTS public.subscription_plans (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            plan_name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            monthly_price_usd DECIMAL(10,2) NOT NULL DEFAULT 0,
            annual_price_usd DECIMAL(10,2) NOT NULL DEFAULT 0,
            monthly_credits INTEGER NOT NULL DEFAULT 0,
            features JSONB NOT NULL DEFAULT '{}',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """,
        
        # 3. Create user_subscriptions table
        """
        CREATE TABLE IF NOT EXISTS public.user_subscriptions (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
            plan_id UUID REFERENCES public.subscription_plans(id),
            status TEXT NOT NULL DEFAULT 'active',
            payment_gateway TEXT NOT NULL,
            gateway_subscription_id TEXT,
            gateway_customer_id TEXT,
            current_period_start TIMESTAMP WITH TIME ZONE,
            current_period_end TIMESTAMP WITH TIME ZONE,
            cancel_at_period_end BOOLEAN DEFAULT false,
            trial_start TIMESTAMP WITH TIME ZONE,
            trial_end TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id)
        );
        """,
        
        # 4. Create user_credits table
        """
        CREATE TABLE IF NOT EXISTS public.user_credits (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
            total_credits INTEGER NOT NULL DEFAULT 0,
            used_credits INTEGER NOT NULL DEFAULT 0,
            remaining_credits INTEGER GENERATED ALWAYS AS (total_credits - used_credits) STORED,
            billing_period_start TIMESTAMP WITH TIME ZONE,
            billing_period_end TIMESTAMP WITH TIME ZONE,
            rollover_credits INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id, billing_period_start)
        );
        """,
        
        # 5. Create agent_sessions table
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
        
        # 6. Create user_activities table
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
    ]
    
    print(f"\n📊 Creating {len(sql_commands)} database tables...")
    
    # Execute each SQL command
    for i, sql in enumerate(sql_commands, 1):
        try:
            # Use the SQL editor endpoint directly
            result = supabase.postgrest.rpc('exec_sql', {'sql': sql.strip()}).execute()
            print(f"✅ Created table {i}/{len(sql_commands)}")
        except Exception as e:
            # If exec_sql doesn't work, try alternative approach
            print(f"⚠️  Table {i} creation warning: {e}")
            # Continue with next table
            continue
    
    print("\n🎯 Inserting default subscription plans...")
    
    # Insert default subscription plans
    default_plans = [
        {
            'plan_name': 'free',
            'display_name': 'Free Plan',
            'monthly_price_usd': 0,
            'annual_price_usd': 0,
            'monthly_credits': 50,
            'features': {
                'chat_messages': 50,
                'file_uploads': 5,
                'agent_access': ['autowave_chat'],
                'support': 'community'
            }
        },
        {
            'plan_name': 'plus',
            'display_name': 'Plus Plan',
            'monthly_price_usd': 15,
            'annual_price_usd': 150,
            'monthly_credits': 1000,
            'features': {
                'chat_messages': 1000,
                'file_uploads': 50,
                'agent_access': ['autowave_chat', 'prime_agent', 'context7_tools'],
                'support': 'email'
            }
        },
        {
            'plan_name': 'pro',
            'display_name': 'Pro Plan',
            'monthly_price_usd': 169,
            'annual_price_usd': 1690,
            'monthly_credits': 10000,
            'features': {
                'chat_messages': 10000,
                'file_uploads': 500,
                'agent_access': ['autowave_chat', 'prime_agent', 'context7_tools', 'agentic_code', 'research_lab', 'agent_wave'],
                'support': 'priority'
            }
        }
    ]
    
    try:
        for plan in default_plans:
            result = supabase.table('subscription_plans').upsert(plan, on_conflict='plan_name').execute()
            print(f"✅ Inserted/updated plan: {plan['plan_name']}")
    except Exception as e:
        print(f"⚠️  Warning inserting plans: {e}")
    
    print("\n🔍 Verifying table creation...")
    
    # Verify tables exist
    tables_to_check = [
        'user_profiles', 'subscription_plans', 'user_subscriptions', 
        'user_credits', 'agent_sessions', 'user_activities'
    ]
    
    for table in tables_to_check:
        try:
            result = supabase.table(table).select('*').limit(1).execute()
            print(f"✅ {table} - Table exists and accessible")
        except Exception as e:
            print(f"❌ {table} - Error: {e}")
    
    print("\n🎉 Database setup completed!")
    print("\nNext steps:")
    print("1. Check your Supabase dashboard to verify tables were created")
    print("2. Set up Row Level Security (RLS) policies if needed")
    print("3. Test the application functionality")

if __name__ == "__main__":
    main()
