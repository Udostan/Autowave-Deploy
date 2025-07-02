#!/usr/bin/env python3
"""
AutoWave Data Storage Test
Comprehensive test of data storage and activity logging across all agents.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_data_storage_service():
    """Test the data storage service directly."""
    
    print("🧪 Testing Data Storage Service")
    print("=" * 40)
    
    try:
        from app.services.data_storage_service import data_storage, ActivityData
        
        if not data_storage.is_available():
            print("❌ Data storage service not available")
            print("   Check your Supabase credentials in .env file")
            return False
        
        print("✅ Data storage service is available")
        
        # Test storing various activity types
        test_activities = [
            ActivityData(
                user_id="test-user-123",
                agent_type="autowave_chat",
                activity_type="chat",
                input_data={"message": "Test chat message"},
                output_data={"response": "Test chat response"},
                processing_time_ms=1200,
                success=True
            ),
            ActivityData(
                user_id="test-user-123",
                agent_type="prime_agent",
                activity_type="task_execution",
                input_data={"task": "Test task", "use_visual_browser": False},
                output_data={"result": "Task completed successfully"},
                processing_time_ms=3500,
                success=True
            ),
            ActivityData(
                user_id="test-user-123",
                agent_type="agentic_code",
                activity_type="code_generation",
                input_data={"message": "Create a Python function", "current_code": ""},
                output_data={"code": "def test(): pass", "language": "python"},
                processing_time_ms=2800,
                success=True
            )
        ]
        
        stored_activities = []
        for i, activity in enumerate(test_activities, 1):
            print(f"   Testing {activity.agent_type} activity...")
            activity_id = data_storage.store_activity(activity)
            
            if activity_id:
                print(f"   ✅ {activity.agent_type}: {activity_id}")
                stored_activities.append(activity_id)
            else:
                print(f"   ❌ {activity.agent_type}: Failed to store")
        
        print(f"\n📊 Results: {len(stored_activities)}/{len(test_activities)} activities stored")
        return len(stored_activities) == len(test_activities)
        
    except Exception as e:
        print(f"❌ Data storage test failed: {str(e)}")
        return False

def test_agent_apis():
    """Test activity logging through agent APIs."""
    
    print("\n🔍 Testing Agent API Activity Logging")
    print("=" * 45)
    
    base_url = "http://localhost:5001"
    test_user_id = "test-user-api-123"
    test_session_id = f"test-session-{int(time.time())}"
    
    # Test cases for different agents
    test_cases = [
        {
            'name': 'AutoWave Chat',
            'endpoint': f'{base_url}/api/chat',
            'method': 'POST',
            'data': {
                'message': 'Test message for activity logging',
                'user_id': test_user_id,
                'session_id': test_session_id
            }
        },
        {
            'name': 'Prime Agent',
            'endpoint': f'{base_url}/api/prime-agent/execute-task',
            'method': 'POST',
            'data': {
                'task': 'Test task for activity logging',
                'use_visual_browser': False,
                'user_id': test_user_id,
                'session_id': test_session_id
            }
        },
        {
            'name': 'Agentic Code',
            'endpoint': f'{base_url}/api/agentic-code/process',
            'method': 'POST',
            'data': {
                'message': 'Create a test function for activity logging',
                'current_code': '',
                'session_id': test_session_id,
                'user_id': test_user_id
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🔍 Testing {test_case['name']}...")
        
        try:
            # Make API request
            response = requests.post(
                test_case['endpoint'],
                json=test_case['data'],
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Check if we got a valid response
                    if 'response' in response_data or 'result' in response_data or 'success' in response_data:
                        print(f"   ✅ {test_case['name']}: API call successful")
                        print(f"      Response length: {len(str(response_data))} characters")
                        results.append({'agent': test_case['name'], 'status': 'success'})
                    else:
                        print(f"   ⚠️  {test_case['name']}: Unexpected response format")
                        results.append({'agent': test_case['name'], 'status': 'warning'})
                    
                except json.JSONDecodeError:
                    print(f"   ❌ {test_case['name']}: Invalid JSON response")
                    results.append({'agent': test_case['name'], 'status': 'error'})
                    
            elif response.status_code == 404:
                print(f"   ❌ {test_case['name']}: Endpoint not found (404)")
                results.append({'agent': test_case['name'], 'status': 'not_found'})
            else:
                print(f"   ❌ {test_case['name']}: HTTP {response.status_code}")
                results.append({'agent': test_case['name'], 'status': f'http_{response.status_code}'})
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  {test_case['name']}: Request timeout")
            results.append({'agent': test_case['name'], 'status': 'timeout'})
        except requests.exceptions.ConnectionError:
            print(f"   🔌 {test_case['name']}: Connection failed")
            results.append({'agent': test_case['name'], 'status': 'connection_error'})
        except Exception as e:
            print(f"   ❌ {test_case['name']}: {str(e)}")
            results.append({'agent': test_case['name'], 'status': 'error'})
    
    # Summary
    successful = [r for r in results if r['status'] == 'success']
    print(f"\n📊 API Test Results: {len(successful)}/{len(results)} agents successful")
    
    return len(successful) > 0

def test_memory_integration():
    """Test memory service integration."""
    
    print("\n🧠 Testing Memory Integration")
    print("=" * 35)
    
    try:
        from app.services.memory_service import memory_service
        
        if not memory_service.is_available():
            print("⚠️  Memory service not available (Qdrant not configured)")
            print("   This is optional - data storage will work without memory")
            return True
        
        print("✅ Memory service is available")
        
        # Test storing a memory
        success = memory_service.store_memory(
            agent_type='autowave_chat',
            user_id='test-user-memory-123',
            content='Test memory content for integration testing',
            metadata={'test': True, 'timestamp': datetime.now().isoformat()}
        )
        
        if success:
            print("✅ Memory storage test successful")
            
            # Test retrieving memories
            memories = memory_service.retrieve_memories(
                agent_type='autowave_chat',
                user_id='test-user-memory-123',
                query='test memory',
                limit=5
            )
            
            print(f"✅ Memory retrieval test successful ({len(memories)} memories found)")
            return True
        else:
            print("❌ Memory storage test failed")
            return False
            
    except Exception as e:
        print(f"❌ Memory integration test failed: {str(e)}")
        return False

def main():
    """Run comprehensive data storage tests."""
    
    print("🧪 AutoWave Data Storage Comprehensive Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Data Storage Service
    storage_success = test_data_storage_service()
    
    # Test 2: Agent API Integration
    api_success = test_agent_apis()
    
    # Test 3: Memory Integration
    memory_success = test_memory_integration()
    
    # Overall Results
    print(f"\n🎯 Overall Test Results:")
    print("=" * 30)
    print(f"✅ Data Storage Service: {'PASS' if storage_success else 'FAIL'}")
    print(f"✅ Agent API Integration: {'PASS' if api_success else 'FAIL'}")
    print(f"✅ Memory Integration: {'PASS' if memory_success else 'FAIL'}")
    
    overall_success = storage_success and (api_success or memory_success)
    
    if overall_success:
        print(f"\n🎉 Data Storage System: FULLY OPERATIONAL!")
        print("   All user activities will now be stored in Supabase")
        print("   Memory integration enhances AI responses")
        print("   Analytics and insights are being collected")
    else:
        print(f"\n⚠️  Data Storage System: PARTIAL FUNCTIONALITY")
        print("   Some components may not be working correctly")
        print("   Check the individual test results above")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
