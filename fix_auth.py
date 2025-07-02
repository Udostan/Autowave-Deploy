#!/usr/bin/env python3
"""
AutoWave Authentication Fix
Quick fix for email verification and login issues.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("🔧 AUTOWAVE AUTHENTICATION FIX")
    print("=" * 50)
    
    # Get current Supabase URL
    supabase_url = os.getenv('SUPABASE_URL')
    
    if not supabase_url or supabase_url.startswith('your_'):
        print("❌ Supabase URL not properly configured")
        return
    
    print(f"✅ Supabase URL: {supabase_url}")
    
    print("\n🔧 FIXING AUTHENTICATION ISSUES:")
    print("=" * 50)
    
    print("\n1. 📧 EMAIL VERIFICATION ISSUE:")
    print("   Problem: Verification emails redirect to wrong URL")
    print("   Solution: Configure Supabase redirect URLs")
    
    print("\n2. 🔑 LOGIN ISSUE:")
    print("   Problem: Users can't login after registration")
    print("   Solution: Fix email verification flow")
    
    print("\n🎯 STEP-BY-STEP FIX:")
    print("=" * 50)
    
    print("\n📋 STEP 1: CONFIGURE SUPABASE REDIRECT URLS")
    print("1. Go to: https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Go to: Authentication → Settings")
    print("4. Set these URLs:")
    print(f"   Site URL: http://localhost:5001")
    print(f"   Redirect URLs:")
    print(f"   • http://localhost:5001/auth/callback")
    print(f"   • http://localhost:5001/")
    print(f"   • http://localhost:5001/auth/login")
    
    print("\n📋 STEP 2: TEST EMAIL VERIFICATION")
    print("1. Start AutoWave server: python run.py")
    print("2. Register with a NEW email address")
    print("3. Check email for verification link")
    print("4. Click verification link (should work now)")
    
    print("\n📋 STEP 3: TEST LOGIN")
    print("1. After email verification, try logging in")
    print("2. Use the same email/password from registration")
    print("3. Should redirect to AutoWave homepage")
    
    print("\n🚨 IMPORTANT NOTES:")
    print("=" * 50)
    print("• If you already registered, the account might be unverified")
    print("• Try registering with a DIFFERENT email address")
    print("• Make sure AutoWave server is running on port 5001")
    print("• Check browser console for any JavaScript errors")
    
    print("\n🔗 USEFUL LINKS:")
    print("=" * 50)
    print(f"• Supabase Dashboard: https://supabase.com/dashboard")
    print(f"• AutoWave Register: http://localhost:5001/auth/register")
    print(f"• AutoWave Login: http://localhost:5001/auth/login")
    print(f"• Test Callback: http://localhost:5001/auth/callback")

if __name__ == "__main__":
    main()
