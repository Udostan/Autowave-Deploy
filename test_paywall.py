#!/usr/bin/env python3
"""
AutoWave Paywall Testing Script
Tests the paywall functionality for admin users
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"  # Change this to your deployment URL
ADMIN_EMAILS = [
    "reffynestan@gmail.com",
    "autowave101@gmail.com"
]

class PaywallTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_admin_setup(self):
        """Test admin setup functionality"""
        print("🔧 Testing Admin Setup...")
        
        for email in ADMIN_EMAILS:
            try:
                response = self.session.post(
                    f"{self.base_url}/admin/setup",
                    json={"admin_email": email},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"✅ Admin setup successful for {email}")
                        print(f"   Admins processed: {len(data.get('admins_processed', []))}")
                        if data.get('errors'):
                            print(f"   Errors: {data['errors']}")
                    else:
                        print(f"❌ Admin setup failed for {email}: {data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ HTTP Error {response.status_code} for {email}")
                    
            except Exception as e:
                print(f"❌ Exception testing admin setup for {email}: {str(e)}")
        
        print()
    
    def test_subscription_plans(self):
        """Test subscription plans API"""
        print("📋 Testing Subscription Plans...")
        
        try:
            response = self.session.get(f"{self.base_url}/payment/plans")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    plans = data.get('plans', [])
                    print(f"✅ Found {len(plans)} subscription plans:")
                    
                    for plan in plans:
                        print(f"   - {plan['display_name']}: ${plan['monthly_price']}/month")
                        print(f"     Credits: {plan['monthly_credits']}")
                        print(f"     Features: {len(plan.get('features', {}))}")
                else:
                    print(f"❌ Failed to get plans: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception testing subscription plans: {str(e)}")
        
        print()
    
    def test_paywall_endpoints(self):
        """Test paywall-protected endpoints"""
        print("🛡️ Testing Paywall Endpoints...")
        
        # Test endpoints that should be protected
        protected_endpoints = [
            ("/api/agentic-code/process", "POST", {"message": "test"}),
            ("/api/agentic-code/execute", "POST", {"code": "print('test')"}),
            ("/payment/user-info", "GET", None),
            ("/admin/status", "GET", None),
        ]
        
        for endpoint, method, data in protected_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json=data,
                        headers={"Content-Type": "application/json"}
                    )
                
                print(f"   {method} {endpoint}: {response.status_code}")
                
                if response.status_code == 401:
                    print(f"     ✅ Correctly requires authentication")
                elif response.status_code == 402:
                    print(f"     ✅ Correctly requires subscription/credits")
                elif response.status_code == 200:
                    print(f"     ⚠️  Endpoint accessible (may need authentication)")
                else:
                    print(f"     ❓ Unexpected status code")
                    
            except Exception as e:
                print(f"     ❌ Exception: {str(e)}")
        
        print()
    
    def test_credit_system(self):
        """Test credit system functionality"""
        print("💳 Testing Credit System...")
        
        # This would require authentication, so we'll test the structure
        try:
            response = self.session.get(f"{self.base_url}/payment/user-info")
            
            if response.status_code == 401:
                print("✅ Credit system correctly requires authentication")
            elif response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    user_info = data.get('user_info', {})
                    credits = user_info.get('credits', {})
                    print(f"✅ Credit system accessible")
                    print(f"   Plan: {user_info.get('display_name', 'Unknown')}")
                    print(f"   Credits: {credits.get('remaining', 0)}/{credits.get('total', 0)}")
                else:
                    print(f"❌ Credit system error: {data.get('error', 'Unknown')}")
            else:
                print(f"❌ HTTP Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception testing credit system: {str(e)}")
        
        print()
    
    def test_database_schema(self):
        """Test if database schema is properly set up"""
        print("🗄️ Testing Database Schema...")
        
        # Test if subscription plans exist
        try:
            response = self.session.get(f"{self.base_url}/payment/plans")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    plans = data.get('plans', [])
                    
                    expected_plans = ['free', 'plus', 'pro', 'enterprise']
                    found_plans = [plan['name'] for plan in plans]
                    
                    print(f"✅ Database schema appears to be set up")
                    print(f"   Expected plans: {expected_plans}")
                    print(f"   Found plans: {found_plans}")
                    
                    missing_plans = set(expected_plans) - set(found_plans)
                    if missing_plans:
                        print(f"   ⚠️  Missing plans: {missing_plans}")
                    else:
                        print(f"   ✅ All expected plans found")
                else:
                    print(f"❌ Database schema issue: {data.get('error', 'Unknown')}")
            else:
                print(f"❌ Cannot access database (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"❌ Exception testing database schema: {str(e)}")
        
        print()
    
    def test_pricing_page(self):
        """Test pricing page functionality"""
        print("💰 Testing Pricing Page...")
        
        try:
            response = self.session.get(f"{self.base_url}/pricing")
            
            if response.status_code == 200:
                print("✅ Pricing page accessible")
                
                # Check if the page contains expected elements
                content = response.text
                
                checks = [
                    ("Free Plan", "Free plan section"),
                    ("Plus Plan", "Plus plan section"),
                    ("Pro Plan", "Pro plan section"),
                    ("Enterprise", "Enterprise plan section"),
                    ("upgradeToPlan", "JavaScript upgrade function"),
                    ("monthly-tab", "Monthly/Annual toggle"),
                ]
                
                for check_text, description in checks:
                    if check_text in content:
                        print(f"   ✅ {description} found")
                    else:
                        print(f"   ❌ {description} missing")
                        
            elif response.status_code == 302:
                print("⚠️  Pricing page redirects (probably to login)")
            else:
                print(f"❌ HTTP Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception testing pricing page: {str(e)}")
        
        print()
    
    def run_all_tests(self):
        """Run all paywall tests"""
        print("🧪 AutoWave Paywall Testing Suite")
        print("=" * 50)
        print(f"Testing URL: {self.base_url}")
        print(f"Admin Emails: {', '.join(ADMIN_EMAILS)}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        self.test_database_schema()
        self.test_subscription_plans()
        self.test_admin_setup()
        self.test_pricing_page()
        self.test_paywall_endpoints()
        self.test_credit_system()
        
        print("🎯 Testing Complete!")
        print("=" * 50)
        print()
        print("📋 Next Steps:")
        print("1. If admin setup failed, make sure the database schema is applied")
        print("2. If endpoints are accessible without auth, check decorator implementation")
        print("3. Test with actual user authentication for full functionality")
        print("4. Set up payment gateway credentials for payment testing")

def main():
    """Main testing function"""
    # Get base URL from command line or environment
    base_url = sys.argv[1] if len(sys.argv) > 1 else os.getenv('TEST_URL', BASE_URL)
    
    print(f"🚀 Starting AutoWave Paywall Tests")
    print(f"Target URL: {base_url}")
    print()
    
    # Create tester and run tests
    tester = PaywallTester(base_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main()
