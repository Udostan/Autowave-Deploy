#!/usr/bin/env python3
"""
Login Issue Diagnostic Tool
Test the exact login flow to identify the problem.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_login_flow():
    """Test the login flow with a real email."""
    print("🔍 LOGIN ISSUE DIAGNOSTIC")
    print("=" * 50)
    
    try:
        from app.auth.supabase_auth import supabase_auth
        
        if not supabase_auth.is_available():
            print("❌ Supabase authentication not available")
            return False
        
        print("✅ Supabase authentication service is available")
        
        # Get email from user
        email = input("\n📧 Enter the email you registered with: ").strip().lower()
        password = input("🔑 Enter your password: ").strip()
        
        if not email or not password:
            print("❌ Email and password are required")
            return False
        
        print(f"\n🧪 Testing login with email: {email}")
        
        # Test sign in
        result = supabase_auth.sign_in_with_email(email, password)
        
        print(f"\n📊 Login Result:")
        print(f"Success: {result.get('success', False)}")
        
        if result.get('success'):
            print("✅ Login successful!")
            user = result.get('user', {})
            print(f"User ID: {user.get('id', 'N/A')}")
            print(f"Email: {user.get('email', 'N/A')}")
            print(f"Email Confirmed: {user.get('email_confirmed', False)}")
            print(f"Last Sign In: {user.get('last_sign_in', 'N/A')}")
        else:
            print("❌ Login failed!")
            error = result.get('error', 'Unknown error')
            print(f"Error: {error}")
            
            # Check if it's an email verification issue
            if 'email' in error.lower() and ('confirm' in error.lower() or 'verify' in error.lower()):
                print("\n💡 This looks like an email verification issue!")
                print("Solutions:")
                print("1. Check your email for a verification link")
                print("2. Click the verification link to activate your account")
                print("3. Try logging in again after verification")
            elif 'password' in error.lower() or 'invalid' in error.lower():
                print("\n💡 This looks like an incorrect password!")
                print("Solutions:")
                print("1. Double-check your password")
                print("2. Use the password reset feature if needed")
                print("3. Make sure you're using the same password you registered with")
            else:
                print(f"\n💡 Unexpected error: {error}")
                print("This might be a configuration issue.")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error during login test: {e}")
        return False

def check_supabase_settings():
    """Check Supabase configuration."""
    print("\n🔧 CHECKING SUPABASE SETTINGS")
    print("=" * 50)
    
    supabase_url = os.getenv('SUPABASE_URL')
    
    if not supabase_url or supabase_url.startswith('your_'):
        print("❌ Supabase URL not properly configured")
        return False
    
    print(f"✅ Supabase URL: {supabase_url}")
    
    print("\n📋 IMPORTANT SUPABASE SETTINGS TO CHECK:")
    print("1. Go to: https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Go to: Authentication → Settings")
    print("4. Check these settings:")
    print("   • Enable email confirmations: Should be ON")
    print("   • Site URL: http://localhost:5001")
    print("   • Redirect URLs:")
    print("     - http://localhost:5001/auth/callback")
    print("     - http://localhost:5001/")
    print("     - http://localhost:5001/auth/login")
    
    print("\n5. Go to: Authentication → Users")
    print("   • Check if your user exists")
    print("   • Check if email is confirmed (green checkmark)")
    
    return True

def main():
    """Main diagnostic function."""
    print("🔐 AUTOWAVE LOGIN ISSUE DIAGNOSTIC")
    print("=" * 60)
    
    # Check Supabase settings
    check_supabase_settings()
    
    # Test login flow
    success = test_login_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 LOGIN TEST PASSED!")
        print("Your login should be working now.")
    else:
        print("❌ LOGIN TEST FAILED!")
        print("Please follow the suggestions above to fix the issue.")
    
    print("\n🔗 USEFUL LINKS:")
    print("• Supabase Dashboard: https://supabase.com/dashboard")
    print("• AutoWave Login: http://localhost:5001/auth/login")
    print("• AutoWave Register: http://localhost:5001/auth/register")

if __name__ == "__main__":
    main()
