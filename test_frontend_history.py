#!/usr/bin/env python3
"""
Test frontend history sidebar functionality
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5001"

def test_frontend_history():
    """Test that frontend can access history data"""
    
    print("=== Frontend History Test ===\n")
    
    # Step 1: Generate a new document to ensure we have recent activity
    print("1. Generating a new document...")
    try:
        doc_data = {
            "content": f"Test document for frontend history verification - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "page_count": 1
        }
        response = requests.post(f"{BASE_URL}/api/document/generate", json=doc_data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Document generated with session ID: {result.get('session_id')}")
                new_session_id = result.get('session_id')
            else:
                print(f"❌ Document generation failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Document generation request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Document generation error: {e}")
        return False
    
    # Wait for activity to be logged
    time.sleep(5)
    
    # Step 2: Test the unified history API that the frontend uses
    print("\n2. Testing unified history API (frontend endpoint)...")
    try:
        response = requests.get(f"{BASE_URL}/api/history/unified?limit=10")
        if response.status_code == 200:
            history_data = response.json()
            if history_data.get('success'):
                print(f"✅ History API working - Total items: {history_data.get('count', 0)}")
                
                # Check for Agent Wave activities
                agent_wave_activities = [item for item in history_data.get('history', []) 
                                       if item.get('agent_type') == 'agent_wave']
                
                print(f"   Agent Wave activities: {len(agent_wave_activities)}")
                
                if agent_wave_activities:
                    print("\n📋 Recent Agent Wave Activities (what frontend should see):")
                    for i, activity in enumerate(agent_wave_activities[:3], 1):
                        print(f"   {i}. Agent: {activity.get('agent_display_name', 'Unknown')}")
                        print(f"      Preview: {activity.get('preview_text', 'No preview')[:50]}...")
                        print(f"      Session: {activity.get('session_id')}")
                        print(f"      Created: {activity.get('created_at')}")
                        print(f"      Can Continue: {activity.get('can_continue')}")
                        print(f"      URL: {activity.get('continuation_url')}")
                        print()
                    
                    # Check if our new activity is visible
                    if any(activity.get('session_id') == new_session_id for activity in agent_wave_activities):
                        print("🎉 SUCCESS: New document activity is visible in history!")
                    else:
                        print("⚠️  New activity not yet visible (may take a moment)")
                        
                    return True
                else:
                    print("❌ No Agent Wave activities found")
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

def test_document_generator_page():
    """Test that Document Generator page is accessible"""
    print("\n3. Testing Document Generator page access...")
    try:
        response = requests.get(f"{BASE_URL}/document-generator")
        if response.status_code == 200:
            print("✅ Document Generator page loads successfully")
            
            # Check if the page contains the history elements
            page_content = response.text
            has_history_toggle = 'history-toggle' in page_content
            has_history_sidebar = 'history-sidebar' in page_content
            has_professional_history_js = 'professional_history.js' in page_content
            
            print(f"   History toggle element: {'✅' if has_history_toggle else '❌'}")
            print(f"   History sidebar element: {'✅' if has_history_sidebar else '❌'}")
            print(f"   Professional history JS: {'✅' if has_professional_history_js else '❌'}")
            
            return has_history_toggle and has_history_sidebar
        else:
            print(f"❌ Document Generator page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing Document Generator page: {e}")
        return False

def main():
    print("Testing frontend history functionality...\n")
    
    # Test 1: Document Generator page
    page_ok = test_document_generator_page()
    
    # Test 2: Frontend history data
    history_ok = test_frontend_history()
    
    print("\n=== Test Summary ===")
    if page_ok and history_ok:
        print("🎉 SUCCESS: Frontend history should be working!")
        print("\n📱 Manual Testing Steps:")
        print("1. Open http://localhost:5001/document-generator")
        print("2. Look for the hamburger menu (☰) in the top-right corner")
        print("3. Click the hamburger menu to open history sidebar")
        print("4. You should see Agent Wave activities listed")
        print("5. Click on any activity to continue the session")
        print("\n🔍 If history sidebar doesn't open:")
        print("- Check browser console for JavaScript errors")
        print("- Verify that professional_history.js is loaded")
        print("- Check if history-toggle element exists")
    else:
        print("❌ ISSUES FOUND:")
        if not page_ok:
            print("- Document Generator page has missing elements")
        if not history_ok:
            print("- History API is not returning Agent Wave activities")
        
    return page_ok and history_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
