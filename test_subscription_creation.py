#!/usr/bin/env python3
"""
Test subscription creation with proper service role authentication
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.subscription_service import SubscriptionService

def test_subscription_creation():
    """Test creating a subscription with service role key"""
    
    print("🧪 Testing Subscription Creation...")
    
    # Initialize subscription service
    subscription_service = SubscriptionService()
    
    if not subscription_service.use_supabase:
        print("❌ Supabase not available, using fallback mode")
        return
    
    print("✅ Supabase connection established")
    
    # Test user ID (you can replace with a real user ID from your auth.users table)
    test_user_id = "049c32df-a61f-599e-8d7f-0d0763855950"
    
    try:
        # Try to create a free subscription
        print(f"📝 Creating free subscription for user: {test_user_id}")
        
        result = subscription_service.create_subscription(
            user_id=test_user_id,
            plan_name="free",
            payment_gateway="manual"
        )
        
        if result:
            print("✅ Subscription created successfully!")
            print(f"   Subscription ID: {result.get('id', 'N/A')}")
            print(f"   Plan: {result.get('plan_name', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
        else:
            print("❌ Failed to create subscription")
            
    except Exception as e:
        print(f"❌ Error creating subscription: {e}")
        
    # Test fetching subscription plans
    try:
        print("\n📋 Fetching subscription plans...")
        plans = subscription_service.get_subscription_plans()
        
        if plans:
            print("✅ Plans fetched successfully:")
            for plan in plans:
                print(f"   - {plan.get('display_name', 'N/A')}: ${plan.get('monthly_price_usd', 0)}/month")
        else:
            print("❌ No plans found")
            
    except Exception as e:
        print(f"❌ Error fetching plans: {e}")

if __name__ == "__main__":
    test_subscription_creation()
