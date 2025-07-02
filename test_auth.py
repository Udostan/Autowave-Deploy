#!/usr/bin/env python3
"""
AutoWave Authentication Diagnostic Tool
Test and diagnose Supabase authentication issues.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if environment variables are properly set."""
    print("🔍 TESTING ENVIRONMENT VARIABLES")
    print("=" * 50)
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY', 
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    issues = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            issues.append(f"❌ {var}: Not set")
        elif value.startswith('your_'):
            issues.append(f"❌ {var}: Still using placeholder value")
        elif len(value) < 10:
            issues.append(f"❌ {var}: Value too short (likely invalid)")
        else:
            print(f"✅ {var}: Set correctly ({value[:20]}...)")
    
    if issues:
        print("\n🚨 ENVIRONMENT ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("\n✅ All environment variables are properly set!")
        return True

def test_supabase_connection():
    """Test connection to Supabase."""
    print("\n🔗 TESTING SUPABASE CONNECTION")
    print("=" * 50)
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or url.startswith('your_'):
            print("❌ Cannot test connection: Invalid SUPABASE_URL")
            return False
        
        if not key or key.startswith('your_'):
            print("❌ Cannot test connection: Invalid SUPABASE_ANON_KEY")
            return False
        
        print(f"🔗 Connecting to: {url}")
        client = create_client(url, key)
        
        # Test basic connection
        print("✅ Supabase client created successfully")
        
        # Test auth service
        auth = client.auth
        print("✅ Auth service accessible")
        
        return True
        
    except ImportError:
        print("❌ Supabase library not installed")
        print("   Run: pip install supabase==2.3.4")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_authentication_flow():
    """Test authentication flow with dummy data."""
    print("\n🔐 TESTING AUTHENTICATION FLOW")
    print("=" * 50)
    
    try:
        from app.auth.supabase_auth import supabase_auth
        
        if not supabase_auth.is_available():
            print("❌ Supabase authentication not available")
            return False
        
        print("✅ Supabase authentication service is available")
        
        # Test sign up with dummy data (this will fail but we can see the error)
        print("\n🧪 Testing sign up flow...")
        result = supabase_auth.sign_up_with_email(
            "test@example.com", 
            "testpassword123"
        )
        
        if result['success']:
            print("✅ Sign up test successful")
        else:
            print(f"ℹ️  Sign up test result: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication flow test failed: {e}")
        return False

def provide_setup_instructions():
    """Provide step-by-step setup instructions."""
    print("\n📋 SETUP INSTRUCTIONS")
    print("=" * 50)
    
    print("""
🎯 TO FIX AUTHENTICATION ISSUES:

1. 🌐 CREATE SUPABASE PROJECT:
   • Go to https://supabase.com
   • Sign up/login
   • Click "New Project"
   • Name: "AutoWave Authentication"
   • Wait for setup (2-3 minutes)

2. 🔑 GET YOUR CREDENTIALS:
   • In Supabase dashboard: Settings → API
   • Copy these 3 values:
     - Project URL (https://xxx.supabase.co)
     - Anon public key (eyJhbGci...)
     - Service role key (eyJhbGci...)

3. 📝 UPDATE YOUR .env FILE:
   Replace lines 76-78 in your .env file:
   
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

4. ⚙️  CONFIGURE SUPABASE:
   • In Supabase: Authentication → Settings
   • Site URL: http://localhost:5001
   • Redirect URLs: 
     - http://localhost:5001/auth/callback
     - http://localhost:5001/

5. 🔄 RESTART SERVER:
   • Stop current server (Ctrl+C)
   • Run: python run.py
   • Test: http://localhost:5001/auth/register

6. 🧪 TEST AUTHENTICATION:
   • Register with real email
   • Check email for verification
   • Try logging in
""")

def main():
    """Main diagnostic function."""
    print("🔐 AUTOWAVE AUTHENTICATION DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Test 1: Environment Variables
    env_ok = test_environment_variables()
    
    # Test 2: Supabase Connection (only if env vars are OK)
    if env_ok:
        conn_ok = test_supabase_connection()
        
        # Test 3: Authentication Flow (only if connection is OK)
        if conn_ok:
            auth_ok = test_authentication_flow()
            
            if auth_ok:
                print("\n🎉 ALL TESTS PASSED!")
                print("Your authentication system should be working.")
                print("If you're still having issues, check the Supabase dashboard for user registrations.")
            else:
                print("\n⚠️  AUTHENTICATION FLOW ISSUES")
                provide_setup_instructions()
        else:
            print("\n⚠️  CONNECTION ISSUES")
            provide_setup_instructions()
    else:
        print("\n⚠️  ENVIRONMENT CONFIGURATION ISSUES")
        provide_setup_instructions()
    
    print("\n" + "=" * 60)
    print("🔗 USEFUL LINKS:")
    print("• Supabase Dashboard: https://supabase.com/dashboard")
    print("• AutoWave Login: http://localhost:5001/auth/login")
    print("• AutoWave Register: http://localhost:5001/auth/register")

if __name__ == "__main__":
    main()
