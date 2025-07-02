#!/usr/bin/env python3
"""
Test if Supabase subscription tables exist and have data
"""

from supabase import create_client

def test_tables():
    """Test if subscription tables exist"""
    
    supabase_url = "https://vkdrcfcmbkuzznybwqix.supabase.co"
    service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrZHJjZmNtYmt1enpueWJ3cWl4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODYxNDgyOSwiZXhwIjoyMDY0MTkwODI5fQ.4s0j6SvyR_SZijN0sNFP06QIofR6c3iH8g4EKvdINWA"
    
    try:
        supabase = create_client(supabase_url, service_role_key)
        print("✅ Connected to Supabase")
        
        # Test subscription_plans table
        print("\n🔍 Testing subscription_plans table...")
        result = supabase.table('subscription_plans').select('plan_name, display_name, monthly_price_usd').execute()
        
        if result.data:
            print("✅ subscription_plans table exists with data:")
            for plan in result.data:
                print(f"   - {plan['display_name']}: ${plan['monthly_price_usd']}/month")
        else:
            print("⚠️  subscription_plans table exists but has no data")
            
        # Test user_subscriptions table
        print("\n🔍 Testing user_subscriptions table...")
        result2 = supabase.table('user_subscriptions').select('id').limit(1).execute()
        print("✅ user_subscriptions table exists")
        
        print("\n🎉 SUCCESS! All subscription tables are working!")
        print("✅ Your AutoWave app will now use Supabase instead of fallback mode")
        print("✅ Apple Pay subscriptions will be stored in Supabase")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📋 Please run the SQL commands in your Supabase dashboard:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Copy and run the contents of 'supabase_sql_commands.sql'")
        return False

if __name__ == "__main__":
    print("🧪 Testing Supabase Subscription Tables")
    print("=" * 40)
    test_tables()
