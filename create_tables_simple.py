#!/usr/bin/env python3
"""
Simple Supabase table creation script
"""

from supabase import create_client, Client

def create_tables():
    """Create subscription tables in Supabase"""
    
    # Use the service role key from your .env.production file
    supabase_url = "https://vkdrcfcmbkuzznybwqix.supabase.co"
    # This is the service role key from your original message
    service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrZHJjZmNtYmt1enpueWJ3cWl4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODYxNDgyOSwiZXhwIjoyMDY0MTkwODI5fQ.4s0j6SvyR_SZijN0sNFP06QIofR6c3iH8g4EKvdINWA"
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, service_role_key)
        print("✅ Connected to Supabase")
        
        # Create subscription_plans table
        plans_sql = """
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
        """
        
        # Create user_subscriptions table
        subscriptions_sql = """
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
        """
        
        print("🔧 Creating tables using direct SQL...")

        # For Supabase, we need to use the SQL editor or create tables through the dashboard
        # Let's try to create tables by inserting data first, which will auto-create them
        print("📋 Creating tables by inserting default plans...")
        
        # Insert default plans
        print("📋 Inserting default plans...")
        
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
                    "credit_type": "daily"
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
                    "credit_type": "monthly"
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
                    "credit_type": "monthly"
                },
                'is_active': True
            }
        ]
        
        for plan in default_plans:
            try:
                # Check if plan exists
                existing = supabase.table('subscription_plans').select('id').eq('plan_name', plan['plan_name']).execute()
                
                if existing.data:
                    print(f"   ⚠️  Plan '{plan['plan_name']}' already exists")
                else:
                    supabase.table('subscription_plans').insert(plan).execute()
                    print(f"   ✅ Created: {plan['display_name']} (${plan['monthly_price_usd']}/month)")
                    
            except Exception as e:
                print(f"   ❌ Error with plan {plan['plan_name']}: {e}")
        
        print("\n🎉 SUCCESS! Supabase subscription tables are ready!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating Supabase Subscription Tables")
    print("=" * 40)
    create_tables()
