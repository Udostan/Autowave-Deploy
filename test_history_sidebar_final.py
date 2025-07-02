#!/usr/bin/env python3
"""
Final test for Agent Wave history sidebar functionality
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5001"

def test_history_sidebar_final():
    """Final comprehensive test of history sidebar functionality"""
    
    print("=== Final History Sidebar Test ===\n")
    
    # Test 1: Verify Document Generator page loads without errors
    print("1. Testing Document Generator page access...")
    try:
        response = requests.get(f"{BASE_URL}/document-generator")
        if response.status_code == 200:
            print("✅ Document Generator page loads successfully")
            
            # Check for required elements in the HTML
            page_content = response.text
            has_history_toggle = 'history-toggle' in page_content
            has_history_sidebar = 'history-sidebar' in page_content
            has_professional_history_js = 'professional_history.js' in page_content
            has_enhanced_history_js = 'enhanced_history.js' in page_content
            
            print(f"   History toggle element: {'✅' if has_history_toggle else '❌'}")
            print(f"   History sidebar element: {'✅' if has_history_sidebar else '❌'}")
            print(f"   Professional history JS: {'✅' if has_professional_history_js else '❌'}")
            print(f"   Enhanced history JS: {'✅' if has_enhanced_history_js else '❌'}")
            
            if not (has_history_toggle and has_history_sidebar):
                print("❌ Missing required history elements")
                return False
                
        else:
            print(f"❌ Document Generator page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing Document Generator page: {e}")
        return False
    
    # Test 2: Test history API directly
    print("\n2. Testing history API...")
    try:
        response = requests.get(f"{BASE_URL}/api/history/unified?limit=10")
        if response.status_code == 200:
            history_data = response.json()
            if history_data.get('success'):
                print(f"✅ History API working - Total items: {history_data.get('count', 0)}")
                
                # Check for Agent Wave activities
                agent_wave_activities = [item for item in history_data.get('history', []) 
                                       if item.get('agent_type') == 'agent_wave']
                
                print(f"   Agent Wave activities found: {len(agent_wave_activities)}")
                
                if agent_wave_activities:
                    print("\n📋 Agent Wave Activities (what should appear in sidebar):")
                    for i, activity in enumerate(agent_wave_activities[:3], 1):
                        print(f"   {i}. Agent: {activity.get('agent_display_name', 'Unknown')}")
                        print(f"      Preview: {activity.get('preview_text', 'No preview')}")
                        print(f"      Session: {activity.get('session_id')}")
                        print(f"      Type: {activity.get('activity_type')}")
                        print(f"      Can Continue: {activity.get('can_continue')}")
                        print(f"      URL: {activity.get('continuation_url')}")
                        print()
                    
                    return True
                else:
                    print("⚠️  No Agent Wave activities found")
                    return False
            else:
                print(f"❌ History API error: {history_data.get('error')}")
                return False
        else:
            print(f"❌ History API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ History API error: {e}")
        return False

def test_document_generation():
    """Test document generation and activity tracking"""
    print("\n3. Testing document generation and activity tracking...")
    try:
        doc_data = {
            "content": f"Final test document for history sidebar - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "page_count": 1
        }
        response = requests.post(f"{BASE_URL}/api/document/generate", json=doc_data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Document generated successfully")
                print(f"   Session ID: {result.get('session_id')}")
                print(f"   Has PDF: {bool(result.get('pdf_base64'))}")
                return result.get('session_id')
            else:
                print(f"❌ Document generation failed: {result.get('error')}")
                return None
        else:
            print(f"❌ Document generation request failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Document generation error: {e}")
        return None

def main():
    print("Testing Agent Wave history sidebar functionality...\n")
    
    # Test 1: Page and API access
    basic_tests_passed = test_history_sidebar_final()
    
    # Test 2: Document generation
    session_id = test_document_generation()
    
    # Wait for activity to be logged
    if session_id:
        print("\n4. Waiting for activity to be logged...")
        time.sleep(5)
        
        # Check if new activity appears
        try:
            response = requests.get(f"{BASE_URL}/api/history/unified?limit=5")
            if response.status_code == 200:
                history_data = response.json()
                if history_data.get('success'):
                    recent_sessions = [item.get('session_id') for item in history_data.get('history', [])]
                    if session_id in recent_sessions:
                        print("✅ New document generation activity found in history!")
                    else:
                        print("⚠️  New activity not yet visible (may take a moment)")
        except Exception as e:
            print(f"⚠️  Error checking for new activity: {e}")
    
    print("\n=== Test Summary ===")
    if basic_tests_passed:
        print("🎉 SUCCESS: History sidebar should be working!")
        print("\n📱 Manual Testing Instructions:")
        print("1. Open http://localhost:5001/document-generator")
        print("2. Generate a document using the interface")
        print("3. Click the hamburger menu (☰) in the top-right corner")
        print("4. The history sidebar should open without JavaScript errors")
        print("5. You should see 'Super Agent' activities in the history list")
        print("6. Click on any activity to continue the session")
        print("\n✅ Expected Results:")
        print("- No 'Error loading history' messages in browser console")
        print("- History sidebar opens smoothly")
        print("- Agent Wave activities are visible as 'Super Agent'")
        print("- Activities have proper preview text and timestamps")
        print("- Clicking activities redirects to /document-generator")
        
        print("\n🔧 What was fixed:")
        print("- Added null checks for DOM elements in professional_history.js")
        print("- Added proper error handling for missing history elements")
        print("- Fixed continuation URL mapping for Agent Wave")
        print("- Added comprehensive activity tracking to document generation")
        
    else:
        print("❌ ISSUES FOUND:")
        print("- History API or page elements are not working correctly")
        print("- Check server logs for errors")
        print("- Verify Supabase connection")
        
    return basic_tests_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
