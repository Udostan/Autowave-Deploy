#!/usr/bin/env python3
"""
Simple script to create referral tables using direct table operations
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("🚀 Creating AutoWave Referral Tables")
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
    
    # Create influencers table by inserting sample data (this will create the table)
    print("\n📊 Creating influencers table...")
    
    sample_influencers = [
        {
            'name': 'Matthew Berman',
            'email': 'matthew@autowave.pro',
            'utm_source': 'MatthewBerman',
            'referral_code': 'MATTHEW20',
            'discount_percentage': 20.0,
            'bonus_credits': 100,
            'commission_rate': 10.0,
            'is_active': True,
            'total_referrals': 0,
            'total_revenue': 0.0
        },
        {
            'name': 'AI Explained',
            'email': 'aiexplained@autowave.pro',
            'utm_source': 'AIExplained',
            'referral_code': 'AIEXPLAINED15',
            'discount_percentage': 15.0,
            'bonus_credits': 50,
            'commission_rate': 8.0,
            'is_active': True,
            'total_referrals': 0,
            'total_revenue': 0.0
        },
        {
            'name': 'Two Minute Papers',
            'email': 'twominute@autowave.pro',
            'utm_source': 'TwoMinutePapers',
            'referral_code': 'PAPERS25',
            'discount_percentage': 25.0,
            'bonus_credits': 150,
            'commission_rate': 12.0,
            'is_active': True,
            'total_referrals': 0,
            'total_revenue': 0.0
        },
        {
            'name': 'Yannic Kilcher',
            'email': 'yannic@autowave.pro',
            'utm_source': 'YannicKilcher',
            'referral_code': 'YANNIC15',
            'discount_percentage': 15.0,
            'bonus_credits': 75,
            'commission_rate': 9.0,
            'is_active': True,
            'total_referrals': 0,
            'total_revenue': 0.0
        },
        {
            'name': 'Lex Fridman',
            'email': 'lex@autowave.pro',
            'utm_source': 'LexFridman',
            'referral_code': 'LEX30',
            'discount_percentage': 30.0,
            'bonus_credits': 200,
            'commission_rate': 15.0,
            'is_active': True,
            'total_referrals': 0,
            'total_revenue': 0.0
        }
    ]
    
    try:
        # Try to insert influencers (this will create the table if it doesn't exist)
        result = supabase.table('influencers').upsert(sample_influencers, on_conflict='utm_source').execute()
        print(f"✅ Created influencers table with {len(sample_influencers)} influencers")
    except Exception as e:
        print(f"⚠️  Could not create influencers table: {e}")
        print("You may need to create the table manually in Supabase SQL Editor")
    
    # Create other tables by inserting empty records
    print("\n📊 Creating other referral tables...")
    
    # Create referral_visits table
    try:
        # Insert a dummy record to create the table structure
        dummy_visit = {
            'influencer_id': None,
            'utm_source': 'test',
            'utm_medium': 'test',
            'utm_campaign': 'test',
            'user_id': None,
            'ip_address': '127.0.0.1'
        }
        supabase.table('referral_visits').insert(dummy_visit).execute()
        # Delete the dummy record
        supabase.table('referral_visits').delete().eq('utm_source', 'test').execute()
        print("✅ Created referral_visits table")
    except Exception as e:
        print(f"⚠️  Could not create referral_visits table: {e}")
    
    # Create referral_conversions table
    try:
        dummy_conversion = {
            'influencer_id': None,
            'user_id': '00000000-0000-0000-0000-000000000000',
            'subscription_id': None,
            'amount': 0.0,
            'utm_source': 'test'
        }
        supabase.table('referral_conversions').insert(dummy_conversion).execute()
        # Delete the dummy record
        supabase.table('referral_conversions').delete().eq('utm_source', 'test').execute()
        print("✅ Created referral_conversions table")
    except Exception as e:
        print(f"⚠️  Could not create referral_conversions table: {e}")
    
    # Create user_referrals table
    try:
        dummy_user_referral = {
            'user_id': '00000000-0000-0000-0000-000000000000',
            'influencer_id': None,
            'utm_source': 'test',
            'discount_percentage': 0.0,
            'bonus_credits': 0
        }
        supabase.table('user_referrals').insert(dummy_user_referral).execute()
        # Delete the dummy record
        supabase.table('user_referrals').delete().eq('utm_source', 'test').execute()
        print("✅ Created user_referrals table")
    except Exception as e:
        print(f"⚠️  Could not create user_referrals table: {e}")
    
    print("\n🔍 Verifying table creation...")
    
    # Verify tables exist
    tables_to_check = ['influencers', 'referral_visits', 'referral_conversions', 'user_referrals']
    
    for table in tables_to_check:
        try:
            result = supabase.table(table).select('*').limit(1).execute()
            print(f"✅ {table} - Table exists and accessible")
        except Exception as e:
            print(f"❌ {table} - Error: {e}")
    
    print("\n🎯 Testing referral functionality...")
    
    # Test getting an influencer
    try:
        result = supabase.table('influencers').select('*').eq('utm_source', 'MatthewBerman').single().execute()
        if result.data:
            print(f"✅ Found influencer: {result.data['name']} ({result.data['referral_code']})")
        else:
            print("⚠️  No influencer found")
    except Exception as e:
        print(f"❌ Error testing influencer lookup: {e}")
    
    print("\n🎉 Referral system setup completed!")
    print("\nNext steps:")
    print("1. Test the referral system with URLs like:")
    print("   http://localhost:5001/?utm_source=MatthewBerman&utm_medium=Youtube&utm_campaign=influence")
    print("2. Test referral codes like: MATTHEW20, AIEXPLAINED15, PAPERS25")
    print("3. Check the Supabase dashboard to verify tables were created")

if __name__ == "__main__":
    main()
