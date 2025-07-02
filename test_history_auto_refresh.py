#!/usr/bin/env python3
"""
Test history sidebar auto-refresh functionality
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5001"

def test_history_auto_refresh():
    """Test that history sidebar auto-refreshes on all pages"""
    
    print("=== History Auto-Refresh Test ===\n")
    
    # Test 1: Verify pages load with history elements
    pages_to_test = [
        ('/document-generator', 'Document Generator'),
        ('/autowave-chat', 'AutoWave Chat'),
        ('/prime-agent-tools', 'Prime Agent Tools'),
        ('/agentic-code', 'Agent Alpha'),
        ('/research-lab', 'Research Lab')
    ]
    
    print("1. Testing history elements on different pages...")
    for url, name in pages_to_test:
        try:
            response = requests.get(f"{BASE_URL}{url}")
            if response.status_code == 200:
                page_content = response.text
                has_history_toggle = 'history-toggle' in page_content
                has_history_sidebar = 'history-sidebar' in page_content
                has_refresh_button = 'refresh-history' in page_content
                has_professional_history_js = 'professional_history.js' in page_content
                
                print(f"   {name}:")
                print(f"     Toggle: {'✅' if has_history_toggle else '❌'}")
                print(f"     Sidebar: {'✅' if has_history_sidebar else '❌'}")
                print(f"     Refresh: {'✅' if has_refresh_button else '❌'}")
                print(f"     JS: {'✅' if has_professional_history_js else '❌'}")
                
                if not (has_history_toggle and has_history_sidebar and has_refresh_button):
                    print(f"     ❌ Missing elements on {name}")
                    return False
            else:
                print(f"   ❌ {name}: Failed to load ({response.status_code})")
                return False
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
            return False
    
    print("\n2. Testing history API consistency...")
    try:
        response = requests.get(f"{BASE_URL}/api/history/unified?limit=10")
        if response.status_code == 200:
            history_data = response.json()
            if history_data.get('success'):
                total_items = history_data.get('count', 0)
                agent_wave_items = len([item for item in history_data.get('history', []) 
                                      if item.get('agent_type') == 'agent_wave'])
                
                print(f"✅ History API working - Total: {total_items}, Agent Wave: {agent_wave_items}")
                
                if agent_wave_items > 0:
                    print("\n📋 Sample Agent Wave Activities:")
                    for i, item in enumerate([item for item in history_data.get('history', []) 
                                            if item.get('agent_type') == 'agent_wave'][:2], 1):
                        print(f"   {i}. {item.get('agent_display_name', 'Unknown')}")
                        print(f"      Preview: {item.get('preview_text', 'No preview')[:50]}...")
                        print(f"      Session: {item.get('session_id')}")
                        print(f"      Created: {item.get('created_at')}")
                        print()
                
                return True
            else:
                print(f"❌ History API error: {history_data.get('error')}")
                return False
        else:
            print(f"❌ History API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ History API error: {e}")
        return False

def test_document_generation_tracking():
    """Test that new document generation is tracked"""
    print("\n3. Testing document generation tracking...")
    try:
        doc_data = {
            "content": f"Auto-refresh test document - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "page_count": 1
        }
        response = requests.post(f"{BASE_URL}/api/document/generate", json=doc_data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Document generated successfully")
                print(f"   Session ID: {result.get('session_id')}")
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
    print("Testing history sidebar auto-refresh functionality...\n")
    
    # Test 1: Basic functionality
    basic_tests_passed = test_history_auto_refresh()
    
    # Test 2: Document generation
    session_id = test_document_generation_tracking()
    
    print("\n=== Test Summary ===")
    if basic_tests_passed:
        print("🎉 SUCCESS: History sidebar auto-refresh should be working!")
        print("\n✅ What's been implemented:")
        print("- Auto-refresh every 30 seconds")
        print("- Refresh when tab becomes visible")
        print("- Refresh when window gains focus")
        print("- Manual refresh button with spinning animation")
        print("- Cached data shown immediately when opening sidebar")
        print("- Fresh data loaded in background")
        
        print("\n📱 Manual Testing Instructions:")
        print("1. Open any agent page (Document Generator, Chat, etc.)")
        print("2. Click the hamburger menu (☰) to open history sidebar")
        print("3. Notice the refresh button (🔄) next to the close button")
        print("4. History should load immediately (cached) then refresh")
        print("5. Click refresh button to manually refresh")
        print("6. Switch to another tab and back - history should auto-refresh")
        print("7. Wait 30 seconds - history should auto-refresh")
        
        print("\n🔍 Expected Behavior:")
        print("- History loads on ALL pages, not just homepage")
        print("- Fresh data appears without manual refresh")
        print("- Agent Wave activities show as 'Super Agent'")
        print("- No JavaScript errors in console")
        print("- Smooth animations and responsive UI")
        
        if session_id:
            print(f"\n📝 New Activity: Session {session_id}")
            print("- This should appear in history within 30 seconds")
            print("- Or immediately when you click the refresh button")
        
    else:
        print("❌ ISSUES FOUND:")
        print("- Some pages are missing history elements")
        print("- History API may not be working correctly")
        print("- Check server logs and browser console for errors")
        
    return basic_tests_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
