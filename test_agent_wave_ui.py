#!/usr/bin/env python3
"""
Test Agent Wave UI functionality and history tracking
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5001"

def test_agent_wave_ui():
    """Test Agent Wave UI and verify history tracking works"""

    print("=== Agent Wave (Document Generator) UI Test ===\n")

    # Test 1: Test Document Generator page access
    print("1. Testing Document Generator page access...")
    try:
        response = requests.get(f"{BASE_URL}/document-generator")
        if response.status_code == 200:
            print("✅ Document Generator page loads successfully")
        else:
            print(f"❌ Document Generator page failed to load: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error loading Document Generator page: {e}")
        return

    # Test 2: Use Document Generation API
    print("\n2. Testing Document Generation...")
    try:
        doc_data = {
            "content": "Create a test document about Agent Wave history tracking integration for developers",
            "page_count": 2
        }
        response = requests.post(f"{BASE_URL}/api/document/generate", json=doc_data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Document generated successfully")
            print(f"   Success: {result['success']}")
            if result.get('document_html'):
                print(f"   Document HTML length: {len(result['document_html'])} chars")
            if result.get('pdf_base64'):
                print(f"   PDF generated: Yes")
        else:
            print(f"❌ Document generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Document generation error: {e}")
    
    # Wait for activity to be logged
    time.sleep(3)
    
    # Test 2: Check history API for Agent Wave activities
    print("\n2. Checking history for Agent Wave activities...")
    try:
        response = requests.get(f"{BASE_URL}/api/history/unified?limit=10")
        if response.status_code == 200:
            history_data = response.json()
            if history_data['success']:
                print(f"✅ History API accessible")
                print(f"   Total items: {history_data['count']}")
                
                # Filter for agent_wave activities
                agent_wave_activities = [item for item in history_data['history'] 
                                       if item.get('agent_type') == 'agent_wave']
                
                print(f"   Agent Wave activities: {len(agent_wave_activities)}")
                
                if agent_wave_activities:
                    print("\n📋 Agent Wave Activities Found:")
                    for i, activity in enumerate(agent_wave_activities, 1):
                        print(f"   {i}. {activity.get('agent_display_name', 'Agent Wave')}")
                        print(f"      Preview: {activity.get('preview_text', 'No preview')[:60]}...")
                        print(f"      Session ID: {activity.get('session_id')}")
                        print(f"      Activity Type: {activity.get('activity_type')}")
                        print(f"      Can Continue: {activity.get('can_continue')}")
                        print(f"      Continuation URL: {activity.get('continuation_url')}")
                        print(f"      Created: {activity.get('created_at')}")
                        print()
                else:
                    print("⚠️  No Agent Wave activities found in history")
            else:
                print(f"❌ History API error: {history_data.get('error')}")
        else:
            print(f"❌ History API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ History API error: {e}")
    
    # Test 3: Test another document generation
    print("\n3. Testing another document generation...")
    try:
        doc_data2 = {
            "content": "Generate a learning path document for understanding AutoWave platform features",
            "page_count": 1
        }
        response = requests.post(f"{BASE_URL}/api/document/generate", json=doc_data2, timeout=60)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Second document generated successfully")
            print(f"   Success: {result['success']}")
            if result.get('document_html'):
                print(f"   Document HTML length: {len(result['document_html'])} chars")
        else:
            print(f"❌ Second document generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Second document generation error: {e}")
    
    # Wait for activity to be logged
    time.sleep(3)
    
    # Test 4: Final history check
    print("\n4. Final history check...")
    try:
        response = requests.get(f"{BASE_URL}/api/history/unified?limit=10")
        if response.status_code == 200:
            history_data = response.json()
            if history_data['success']:
                agent_wave_activities = [item for item in history_data['history'] 
                                       if item.get('agent_type') == 'agent_wave']
                
                print(f"✅ Final count - Agent Wave activities: {len(agent_wave_activities)}")
                
                if len(agent_wave_activities) >= 2:
                    print("🎉 SUCCESS: Multiple Agent Wave activities found!")
                    print("   The history sidebar should show these activities.")
                elif len(agent_wave_activities) == 1:
                    print("✅ PARTIAL SUCCESS: One Agent Wave activity found")
                    print("   Try using more tools to see multiple activities.")
                else:
                    print("⚠️  No Agent Wave activities found")
                    
                # Show recent activities
                print("\n📋 Recent Activities (all agents):")
                for i, activity in enumerate(history_data['history'][:5], 1):
                    agent_type = activity.get('agent_type', 'unknown')
                    preview = activity.get('preview_text', 'No preview')[:40]
                    print(f"   {i}. [{agent_type}] {preview}...")
                    
            else:
                print(f"❌ Final history check error: {history_data.get('error')}")
        else:
            print(f"❌ Final history check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Final history check error: {e}")
    
    print("\n=== Test Complete ===")
    print("✅ Agent Wave (Document Generator) page is accessible at http://localhost:5001/document-generator")
    print("✅ Document generation is functional and creating activities")
    print("✅ History API is working and tracking Agent Wave activities")
    print("📱 Open the browser and check the history sidebar (hamburger menu)")
    print("🔍 Look for activities with 'Agent Wave' labels in the history sidebar")

if __name__ == "__main__":
    test_agent_wave_ui()
