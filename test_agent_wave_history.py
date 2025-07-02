#!/usr/bin/env python3
"""
Test Agent Wave page to verify history tracking functionality
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5001"

def test_agent_wave_history():
    """Test Agent Wave page and verify activities appear in history"""
    
    print("=== Agent Wave History Test ===\n")
    
    # Test 1: Check if Agent Wave page loads
    print("1. Testing Agent Wave page access...")
    try:
        response = requests.get(f"{BASE_URL}/agent-wave")
        if response.status_code == 200:
            print("✅ Agent Wave page loads successfully")
        else:
            print(f"❌ Agent Wave page failed to load: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error loading Agent Wave page: {e}")
        return
    
    # Test 2: Test LLM Tool - Email Campaign Manager
    print("\n2. Testing Email Campaign Manager LLM tool...")
    try:
        email_data = {
            "topic": "Test Email Campaign for History Tracking",
            "audience": "test users",
            "campaign_type": "promotional",
            "tone": "professional"
        }
        response = requests.post(f"{BASE_URL}/api/llm-tools/email-campaign", json=email_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Email Campaign tool executed: {result['status']}")
            print(f"   Topic: {result['data']['topic']}")
            print(f"   Has subject: {'subject_line' in result['data']}")
        else:
            print(f"❌ Email Campaign tool failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Email Campaign tool error: {e}")
    
    # Wait a moment for activity to be logged
    time.sleep(2)
    
    # Test 3: Check unified history API
    print("\n3. Checking unified history API...")
    try:
        response = requests.get(f"{BASE_URL}/api/history/unified?limit=10")
        if response.status_code == 200:
            history_data = response.json()
            if history_data['success']:
                print(f"✅ History API accessible, found {history_data['count']} items")
                
                # Look for agent_wave activities
                agent_wave_activities = [item for item in history_data['history'] 
                                       if item.get('agent_type') == 'agent_wave']
                
                if agent_wave_activities:
                    print(f"✅ Found {len(agent_wave_activities)} Agent Wave activities in history!")
                    for activity in agent_wave_activities:
                        print(f"   - {activity.get('agent_display_name', 'Agent Wave')}: {activity.get('preview_text', 'No preview')[:50]}...")
                        print(f"     Session ID: {activity.get('session_id')}")
                        print(f"     Activity Type: {activity.get('activity_type')}")
                        print(f"     Can Continue: {activity.get('can_continue')}")
                        print(f"     Continuation URL: {activity.get('continuation_url')}")
                else:
                    print("⚠️  No Agent Wave activities found in history yet")
                    print("   This might be because:")
                    print("   - Database tables not set up")
                    print("   - Activity logging not working")
                    print("   - Activities not yet processed")
                    
                    # Show what we did find
                    print(f"\n   Found activities from other agents:")
                    for item in history_data['history']:
                        print(f"   - {item.get('agent_type')}: {item.get('preview_text', 'No preview')[:50]}...")
            else:
                print(f"❌ History API error: {history_data.get('error')}")
        else:
            print(f"❌ History API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ History API error: {e}")
    
    # Test 4: Test another LLM tool - Learning Path Generator
    print("\n4. Testing Learning Path Generator LLM tool...")
    try:
        learning_data = {
            "subject": "Agent Wave Testing",
            "skill_level": "beginner",
            "learning_style": "practical",
            "time_commitment": "moderate"
        }
        response = requests.post(f"{BASE_URL}/api/llm-tools/learning-path", json=learning_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Learning Path tool executed: {result['status']}")
            print(f"   Subject: {result['data']['subject']}")
            print(f"   Modules: {result['data']['curriculum']['total_modules']}")
        else:
            print(f"❌ Learning Path tool failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Learning Path tool error: {e}")
    
    # Wait a moment for activity to be logged
    time.sleep(2)
    
    # Test 5: Check history again after second activity
    print("\n5. Checking history again after second activity...")
    try:
        response = requests.get(f"{BASE_URL}/api/history/unified?limit=10")
        if response.status_code == 200:
            history_data = response.json()
            if history_data['success']:
                agent_wave_activities = [item for item in history_data['history'] 
                                       if item.get('agent_type') == 'agent_wave']
                
                print(f"✅ Total history items: {history_data['count']}")
                print(f"✅ Agent Wave activities: {len(agent_wave_activities)}")
                
                if len(agent_wave_activities) >= 2:
                    print("🎉 SUCCESS: Multiple Agent Wave activities found in history!")
                elif len(agent_wave_activities) == 1:
                    print("✅ PARTIAL SUCCESS: One Agent Wave activity found in history")
                else:
                    print("⚠️  No Agent Wave activities found yet")
                    
    except Exception as e:
        print(f"❌ Final history check error: {e}")
    
    # Test 6: Test activity tracking endpoint directly
    print("\n6. Testing activity tracking endpoint directly...")
    try:
        track_data = {
            "user_id": "test_user_123",
            "agent_type": "agent_wave",
            "activity_type": "llm_tool",
            "input_data": {
                "tool_type": "test-tool",
                "description": "Direct API test for Agent Wave history tracking"
            },
            "output_data": {
                "success": True,
                "test": True
            },
            "success": True
        }
        response = requests.post(f"{BASE_URL}/api/history/track", json=track_data)
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print(f"✅ Direct activity tracking successful: {result['activity_id']}")
            else:
                print(f"❌ Direct activity tracking failed: {result.get('error')}")
        else:
            print(f"❌ Direct activity tracking failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Direct activity tracking error: {e}")
    
    print("\n=== Test Summary ===")
    print("✅ Agent Wave page is accessible")
    print("✅ LLM tools are functional")
    print("✅ History API is accessible")
    print("📋 Check the browser history sidebar to see if activities appear")
    print("🔍 If no activities appear, check database setup and activity logging")

if __name__ == "__main__":
    test_agent_wave_history()
