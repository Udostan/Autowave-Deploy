#!/usr/bin/env python3
"""
AutoWave Referral System Database Setup
Run this script to create all necessary database tables in Supabase
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_referral_database():
    """Create all referral system tables in Supabase"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')  # Use service key for admin operations
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
        print("Add these to your .env file:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_SERVICE_KEY=your-service-key")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # SQL commands to create tables
        sql_commands = [
            # 1. Create influencers table
            """
            CREATE TABLE IF NOT EXISTS public.influencers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                utm_source TEXT UNIQUE NOT NULL,
                referral_code TEXT UNIQUE NOT NULL,
                discount_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                bonus_credits INTEGER NOT NULL DEFAULT 0,
                commission_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                is_active BOOLEAN NOT NULL DEFAULT true,
                total_referrals INTEGER NOT NULL DEFAULT 0,
                total_revenue DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # 2. Create referral_visits table
            """
            CREATE TABLE IF NOT EXISTS public.referral_visits (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                influencer_id TEXT REFERENCES public.influencers(id),
                utm_source TEXT,
                utm_medium TEXT,
                utm_campaign TEXT,
                utm_content TEXT,
                utm_term TEXT,
                user_id TEXT,
                ip_address INET,
                user_agent TEXT,
                referrer_url TEXT,
                landing_page TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # 3. Create referral_conversions table
            """
            CREATE TABLE IF NOT EXISTS public.referral_conversions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                influencer_id TEXT REFERENCES public.influencers(id),
                user_id TEXT NOT NULL,
                referral_code TEXT,
                utm_source TEXT,
                utm_medium TEXT,
                utm_campaign TEXT,
                amount DECIMAL(10,2) NOT NULL,
                discount_applied DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                bonus_credits_given INTEGER NOT NULL DEFAULT 0,
                commission_earned DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                plan_name TEXT,
                billing_cycle TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # 4. Create user_referrals table
            """
            CREATE TABLE IF NOT EXISTS public.user_referrals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id TEXT NOT NULL,
                influencer_id TEXT REFERENCES public.influencers(id),
                referral_code TEXT,
                utm_source TEXT,
                utm_medium TEXT,
                utm_campaign TEXT,
                discount_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                bonus_credits INTEGER NOT NULL DEFAULT 0,
                is_converted BOOLEAN NOT NULL DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
        ]
        
        # Execute table creation commands
        for i, sql in enumerate(sql_commands, 1):
            try:
                supabase.rpc('exec_sql', {'sql': sql.strip()}).execute()
                print(f"✅ Created table {i}/4")
            except Exception as e:
                print(f"⚠️  Table {i} might already exist: {str(e)}")
        
        # Insert sample influencer data
        influencers_data = [
            {
                'id': 'matthew-berman',
                'name': 'Matthew Berman',
                'email': 'matthew@matthewberman.ai',
                'utm_source': 'MatthewBerman',
                'referral_code': 'MATTHEW20',
                'discount_percentage': 20.00,
                'bonus_credits': 100,
                'commission_rate': 10.00,
                'is_active': True
            },
            {
                'id': 'ai-explained',
                'name': 'AI Explained',
                'email': 'contact@aiexplained.com',
                'utm_source': 'AIExplained',
                'referral_code': 'AIEXPLAINED15',
                'discount_percentage': 15.00,
                'bonus_credits': 50,
                'commission_rate': 8.00,
                'is_active': True
            },
            {
                'id': 'lex-fridman',
                'name': 'Lex Fridman',
                'email': 'lex@lexfridman.com',
                'utm_source': 'LexFridman',
                'referral_code': 'LEX30',
                'discount_percentage': 30.00,
                'bonus_credits': 150,
                'commission_rate': 12.00,
                'is_active': True
            }
        ]
        
        # Insert influencer data
        try:
            result = supabase.table('influencers').upsert(influencers_data).execute()
            print(f"✅ Inserted {len(influencers_data)} influencers")
        except Exception as e:
            print(f"⚠️  Influencers might already exist: {str(e)}")
        
        # Verify tables were created
        try:
            influencers = supabase.table('influencers').select('*').execute()
            print(f"✅ Verification: Found {len(influencers.data)} influencers in database")
            
            for influencer in influencers.data:
                print(f"   - {influencer['name']}: {influencer['referral_code']} ({influencer['discount_percentage']}% off)")
        
        except Exception as e:
            print(f"❌ Error verifying tables: {str(e)}")
            return False
        
        print("\n🎉 Referral database setup complete!")
        print("\n📊 Test your referral system:")
        print("1. Visit: https://autowave.pro/?utm_source=MatthewBerman")
        print("2. Or use referral code: MATTHEW20 on pricing page")
        print("3. Check analytics in Supabase dashboard")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up AutoWave Referral Database...")
    success = setup_referral_database()
    
    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)
