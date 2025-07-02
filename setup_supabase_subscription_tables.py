#!/usr/bin/env python3
"""
AutoWave Supabase Subscription Tables Setup
Creates the missing subscription_plans and user_subscriptions tables in Supabase
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

def setup_supabase_subscription_tables():
    """Create subscription tables in Supabase database"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Need service role key for admin operations

    print(f"🔍 Debug - URL: {supabase_url}")
    print(f"🔍 Debug - Service Key: {supabase_service_key[:30] if supabase_service_key else 'None'}...")
    
    if not supabase_url or not supabase_service_key:
        print("❌ Error: Missing Supabase credentials")
        print("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables")
        return False

    if supabase_url.startswith('your_') or supabase_service_key.startswith('your_') or 'your_service_role_key_here' in supabase_service_key:
        print("❌ Error: Please update Supabase credentials in .env file")
        print(f"Current service key starts with: {supabase_service_key[:20]}...")
        return False
    
    try:
        # Create Supabase client with service role key
        supabase: Client = create_client(supabase_url, supabase_service_key)
        print("✅ Connected to Supabase")
        
        # SQL to create subscription tables
        subscription_tables_sql = """
        -- 1. Subscription Plans Table
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

        -- 2. User Subscriptions Table
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

        -- 3. Credit Management Table
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

        -- 4. Credit Usage Tracking
        CREATE TABLE IF NOT EXISTS public.credit_usage (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
            agent_type TEXT NOT NULL,
            action_type TEXT NOT NULL,
            credits_consumed INTEGER NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- 5. Payment Transactions
        CREATE TABLE IF NOT EXISTS public.payment_transactions (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
            subscription_id UUID REFERENCES public.user_subscriptions(id),
            payment_gateway TEXT NOT NULL,
            gateway_transaction_id TEXT NOT NULL,
            amount_usd DECIMAL(10,2) NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            status TEXT NOT NULL,
            payment_method TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- 6. Feature Usage Tracking
        CREATE TABLE IF NOT EXISTS public.feature_usage (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
            feature_name TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            daily_limit INTEGER,
            monthly_limit INTEGER,
            last_used TIMESTAMP WITH TIME ZONE,
            reset_date TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id, feature_name, reset_date)
        );
        """
        
        # Execute table creation
        print("🔧 Creating subscription tables...")
        supabase.rpc('exec_sql', {'sql': subscription_tables_sql}).execute()
        print("✅ Subscription tables created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def insert_default_plans():
    """Insert default subscription plans"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    try:
        supabase: Client = create_client(supabase_url, supabase_service_key)
        
        # Default subscription plans (matching your working pricing)
        default_plans = [
            {
                'plan_name': 'free',
                'display_name': 'Free Plan',
                'monthly_price_usd': 0,
                'annual_price_usd': 0,
                'monthly_credits': 50,
                'features': {
                    "ai_agents": ["prime_agent", "autowave_chat", "code_wave"],
                    "daily_credits": 50,
                    "credit_type": "daily",
                    "file_upload_limit": 5,
                    "support_level": "community"
                },
                'is_active': True
            },
            {
                'plan_name': 'plus',
                'display_name': 'Plus Plan',
                'monthly_price_usd': 29,
                'annual_price_usd': 348,
                'monthly_credits': 8000,
                'features': {
                    "ai_agents": ["prime_agent", "autowave_chat", "code_wave", "agent_wave", "research_lab"],
                    "monthly_credits": 8000,
                    "credit_type": "monthly",
                    "prime_agent_tools": 12,
                    "file_upload_limit": 100,
                    "credit_rollover": True,
                    "rollover_limit": 0.5,
                    "support_level": "email"
                },
                'is_active': True
            },
            {
                'plan_name': 'pro',
                'display_name': 'Pro Plan',
                'monthly_price_usd': 99,
                'annual_price_usd': 1188,
                'monthly_credits': 200000,
                'features': {
                    "ai_agents": ["prime_agent", "autowave_chat", "code_wave", "agent_wave", "research_lab"],
                    "monthly_credits": 200000,
                    "credit_type": "monthly",
                    "prime_agent_tools": -1,
                    "file_upload_limit": -1,
                    "credit_rollover": True,
                    "rollover_limit": 0.3,
                    "real_time_browsing": True,
                    "support_level": "priority"
                },
                'is_active': True
            }
        ]
        
        print("📋 Inserting default subscription plans...")
        
        for plan in default_plans:
            try:
                # Check if plan already exists
                existing = supabase.table('subscription_plans').select('id').eq('plan_name', plan['plan_name']).execute()
                
                if existing.data:
                    print(f"   ⚠️  Plan '{plan['plan_name']}' already exists, skipping...")
                else:
                    supabase.table('subscription_plans').insert(plan).execute()
                    print(f"   ✅ Created plan: {plan['display_name']} (${plan['monthly_price_usd']}/month)")
                    
            except Exception as e:
                print(f"   ❌ Error creating plan {plan['plan_name']}: {e}")
        
        print("✅ Default subscription plans setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Error inserting default plans: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AutoWave Supabase Subscription Tables Setup")
    print("=" * 50)
    
    # Create tables
    if setup_supabase_subscription_tables():
        print("\n📋 Setting up default subscription plans...")
        if insert_default_plans():
            print("\n🎉 SUCCESS! Supabase subscription tables are ready!")
            print("\n✅ Your AutoWave app will now use Supabase instead of fallback mode")
            print("✅ Pricing system will load plans from Supabase database")
            print("✅ Apple Pay subscriptions will be stored in Supabase")
        else:
            print("\n⚠️  Tables created but failed to insert default plans")
    else:
        print("\n❌ Failed to create subscription tables")
        sys.exit(1)
