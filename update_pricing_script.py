#!/usr/bin/env python3
"""
Update AutoWave subscription pricing in Supabase
"""

from supabase import create_client

def update_pricing():
    """Update subscription pricing in Supabase"""
    
    supabase_url = "https://vkdrcfcmbkuzznybwqix.supabase.co"
    service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrZHJjZmNtYmt1enpueWJ3cWl4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODYxNDgyOSwiZXhwIjoyMDY0MTkwODI5fQ.4s0j6SvyR_SZijN0sNFP06QIofR6c3iH8g4EKvdINWA"
    
    try:
        supabase = create_client(supabase_url, service_role_key)
        print("✅ Connected to Supabase")
        
        # Update Plus Plan to $15/month
        print("🔧 Updating Plus Plan to $15/month...")
        result1 = supabase.table('subscription_plans').update({
            'monthly_price_usd': 15,
            'annual_price_usd': 180,  # 15 * 12
            'updated_at': 'now()'
        }).eq('plan_name', 'plus').execute()
        
        # Update Pro Plan to $169/month
        print("🔧 Updating Pro Plan to $169/month...")
        result2 = supabase.table('subscription_plans').update({
            'monthly_price_usd': 169,
            'annual_price_usd': 2028,  # 169 * 12
            'updated_at': 'now()'
        }).eq('plan_name', 'pro').execute()
        
        # Verify the updated pricing
        print("\n📋 Current pricing in Supabase:")
        result = supabase.table('subscription_plans').select('plan_name, display_name, monthly_price_usd, annual_price_usd').order('monthly_price_usd').execute()
        
        for plan in result.data:
            print(f"   - {plan['display_name']}: ${plan['monthly_price_usd']}/month (${plan['annual_price_usd']}/year)")
        
        print("\n✅ Pricing updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating pricing: {e}")
        return False

if __name__ == "__main__":
    print("💰 Updating AutoWave Subscription Pricing")
    print("=" * 40)
    update_pricing()
