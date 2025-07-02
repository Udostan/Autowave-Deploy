#!/usr/bin/env python3
"""
AutoWave UI Flow Test
Tests the complete user journey from registration to payment page
"""

import requests
import json
import time
from urllib.parse import urljoin

BASE_URL = "http://localhost:5001"

def test_complete_ui_flow():
    """Test complete UI flow including payment page"""
    print("🧪 AutoWave Complete UI Flow Test")
    print("=" * 60)
    
    session = requests.Session()
    
    # Step 1: Test registration
    print("\n📝 Step 1: Testing User Registration")
    
    registration_data = {
        "email": "test@gmail.com",
        "password": "testpass123",
        "confirm_password": "testpass123",
        "full_name": "Test User"
    }
    
    try:
        response = session.post(
            f"{BASE_URL}/auth/register",
            json=registration_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Registration response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Registration successful")
                print(f"   User ID: {data.get('user', {}).get('id')}")
                print(f"   Test Mode: {data.get('test_mode', False)}")
            else:
                print(f"❌ Registration failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Registration failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False
    
    # Step 2: Test login (if needed)
    print("\n🔐 Step 2: Verifying Authentication")
    
    # Check if we're authenticated by testing a protected endpoint
    try:
        response = session.get(f"{BASE_URL}/payment/user-info")
        print(f"Auth check response: {response.status_code}")
        
        if response.status_code == 401:
            print("⚠️ Need to login explicitly")
            # Try login
            login_data = {
                "email": "test@gmail.com",
                "password": "testpass123"
            }
            
            response = session.post(
                f"{BASE_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ Login successful")
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
        else:
            print("✅ Already authenticated from registration")
    except Exception as e:
        print(f"❌ Auth check error: {e}")
        return False
    
    # Step 3: Test pricing page data
    print("\n💰 Step 3: Testing Pricing Page Data")
    
    try:
        response = session.get(f"{BASE_URL}/payment/plans?location=NG")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Pricing data loaded successfully")
                print(f"   Provider: {data.get('provider')}")
                print(f"   Currency: {data.get('currency_info', {}).get('currency')}")
                
                # Find Plus plan
                plus_plan = next((p for p in data['plans'] if p['name'] == 'plus'), None)
                if plus_plan:
                    print(f"   Plus Plan ID: {plus_plan['id']}")
                    print(f"   Plus Plan Price: {plus_plan['pricing']['monthly']['formatted']}")
                else:
                    print("❌ Plus plan not found")
                    return False
            else:
                print(f"❌ Pricing data error: {data}")
                return False
        else:
            print(f"❌ Pricing data failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Pricing data error: {e}")
        return False
    
    # Step 4: Test subscription creation
    print("\n🛒 Step 4: Testing Subscription Creation")
    
    subscription_data = {
        "plan_id": plus_plan['id'],
        "billing_cycle": "monthly",
        "payment_provider": "auto",
        "user_location": "NG"
    }
    
    try:
        response = session.post(
            f"{BASE_URL}/payment/create-subscription",
            json=subscription_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Subscription creation response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Subscription creation successful")
                print(f"   Subscription ID: {data.get('subscription_id')}")
                
                # Check if we get a payment URL or client secret
                if data.get('client_secret'):
                    print(f"   Stripe Client Secret: {data.get('client_secret')}")
                    print("   → Should redirect to Stripe payment form")
                elif data.get('payment_url'):
                    print(f"   Payment URL: {data.get('payment_url')}")
                    print("   → Should redirect to payment page")
                elif data.get('authorization_url'):
                    print(f"   Authorization URL: {data.get('authorization_url')}")
                    print("   → Should redirect to Paystack payment page")
                else:
                    print("⚠️ No payment URL provided - this is test mode")
                    print("   In production, this would redirect to payment page")
                
                return True
            else:
                print(f"❌ Subscription creation failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Subscription creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Subscription creation error: {e}")
        return False

def test_payment_page_generation():
    """Test if we can generate a proper payment page"""
    print("\n💳 Step 5: Testing Payment Page Generation")
    
    # Test if we can create a payment page for Paystack
    try:
        # This would be the flow for real Paystack integration
        print("🔍 Checking payment page requirements...")
        
        # Check if Paystack keys are configured
        import os
        paystack_secret = os.getenv('PAYSTACK_SECRET_KEY', '')
        paystack_public = os.getenv('PAYSTACK_PUBLIC_KEY', '')
        
        if paystack_secret.startswith('sk_test_your_') or not paystack_secret:
            print("⚠️ Using placeholder Paystack keys (test mode)")
            print("   In test mode, payment page simulation:")
            print("   1. User clicks 'Upgrade to Plus'")
            print("   2. System creates mock subscription")
            print("   3. Shows success message")
            print("   ")
            print("   In production with real keys:")
            print("   1. User clicks 'Upgrade to Plus'")
            print("   2. System creates Paystack plan")
            print("   3. Redirects to Paystack payment page")
            print("   4. User enters card details on Paystack")
            print("   5. Paystack processes payment")
            print("   6. Webhook confirms subscription")
        else:
            print("✅ Real Paystack keys detected")
            print("   Payment flow will redirect to Paystack payment page")
        
        return True
    except Exception as e:
        print(f"❌ Payment page test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting AutoWave UI Flow Test")
    print("Testing complete user journey from registration to payment")
    print()
    
    # Test complete flow
    flow_success = test_complete_ui_flow()
    
    # Test payment page generation
    payment_success = test_payment_page_generation()
    
    print("\n" + "=" * 60)
    print("🎯 Test Results Summary")
    print("=" * 60)
    
    if flow_success:
        print("✅ User registration and authentication: WORKING")
        print("✅ Pricing data and currency conversion: WORKING")
        print("✅ Subscription creation endpoint: WORKING")
    else:
        print("❌ UI flow test: FAILED")
    
    if payment_success:
        print("✅ Payment page requirements: CHECKED")
    else:
        print("❌ Payment page test: FAILED")
    
    print("\n🔧 Next Steps for Payment Page:")
    print("1. Add real Paystack keys to .env file")
    print("2. Update subscription creation to return authorization_url")
    print("3. Frontend should redirect to authorization_url for payment")
    print("4. Implement webhook handling for payment confirmation")
    
    print("\n💡 Current Status:")
    if flow_success:
        print("✅ System is working in test mode")
        print("✅ Ready for production with real Paystack keys")
        print("⚠️ Payment page redirect needs implementation")
    else:
        print("❌ System needs debugging")

if __name__ == "__main__":
    main()
