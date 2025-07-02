#!/usr/bin/env python3
"""
Test File Processing Capabilities
Tests that all agents can properly understand and process uploaded files.
"""

import requests
import json
import time

def test_file_processing_capabilities():
    """Test that all agents can process uploaded files properly."""
    
    print("🧪 Testing File Processing Capabilities Across All Agents")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    
    # Test file content in the universal format
    test_file_content = """
Analyze this Python code and suggest improvements

--- File: calculator.py ---
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Error: Division by zero"
    return a / b

print("Simple Calculator")
print("1. Add")
print("2. Subtract") 
print("3. Multiply")
print("4. Divide")

choice = input("Enter choice (1-4): ")
num1 = float(input("Enter first number: "))
num2 = float(input("Enter second number: "))

if choice == '1':
    print(f"Result: {add(num1, num2)}")
elif choice == '2':
    print(f"Result: {subtract(num1, num2)}")
elif choice == '3':
    print(f"Result: {multiply(num1, num2)}")
elif choice == '4':
    print(f"Result: {divide(num1, num2)}")
else:
    print("Invalid choice")
"""
    
    # Test cases for different agents
    test_cases = [
        {
            'name': 'AutoWave Chat',
            'endpoint': f'{base_url}/api/chat',
            'method': 'POST',
            'data': {
                'message': test_file_content
            },
            'expected_keywords': ['python', 'code', 'file', 'analyze', 'uploaded']
        },
        {
            'name': 'Research Lab',
            'endpoint': f'{base_url}/api/search',
            'method': 'POST',
            'data': {
                'query': test_file_content
            },
            'expected_keywords': ['python', 'code', 'analysis', 'research']
        },
        {
            'name': 'Agentic Code',
            'endpoint': f'{base_url}/api/agentic-code/process',
            'method': 'POST',
            'data': {
                'message': test_file_content,
                'current_code': '',
                'session_id': 'test_session'
            },
            'expected_keywords': ['python', 'code', 'plan', 'steps']
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n🔍 Testing {test_case['name']}...")
        
        try:
            # Make API request
            if test_case['method'] == 'POST':
                response = requests.post(
                    test_case['endpoint'],
                    json=test_case['data'],
                    timeout=30,
                    headers={'Content-Type': 'application/json'}
                )
            else:
                response = requests.get(test_case['endpoint'], timeout=30)
            
            # Check response
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    response_text = json.dumps(response_data).lower()
                    
                    # Check if response contains expected keywords
                    keyword_matches = []
                    for keyword in test_case['expected_keywords']:
                        if keyword.lower() in response_text:
                            keyword_matches.append(keyword)
                    
                    # Determine if file processing worked
                    file_processing_score = len(keyword_matches) / len(test_case['expected_keywords'])
                    
                    if file_processing_score >= 0.5:  # At least 50% of keywords found
                        status = "✅ WORKING"
                        details = f"Found {len(keyword_matches)}/{len(test_case['expected_keywords'])} expected keywords"
                    else:
                        status = "⚠️  PARTIAL"
                        details = f"Found {len(keyword_matches)}/{len(test_case['expected_keywords'])} expected keywords"
                    
                    # Check for file analysis indicators
                    file_indicators = [
                        'file analysis', 'uploaded file', 'file content', 'code analysis',
                        'python code', 'calculator.py', 'function', 'improvement'
                    ]
                    
                    file_analysis_found = any(indicator in response_text for indicator in file_indicators)
                    
                    if file_analysis_found:
                        status = "✅ ENHANCED"
                        details += " + File analysis detected"
                    
                    print(f"   {status}: {details}")
                    
                    results.append({
                        'agent': test_case['name'],
                        'status': status,
                        'score': file_processing_score,
                        'file_analysis': file_analysis_found,
                        'response_length': len(response_text)
                    })
                    
                except json.JSONDecodeError:
                    print(f"   ❌ ERROR: Invalid JSON response")
                    results.append({
                        'agent': test_case['name'],
                        'status': '❌ ERROR',
                        'error': 'Invalid JSON response'
                    })
                    
            elif response.status_code == 404:
                print(f"   ❌ ERROR: Endpoint not found (404)")
                results.append({
                    'agent': test_case['name'],
                    'status': '❌ ERROR',
                    'error': 'Endpoint not found'
                })
            else:
                print(f"   ❌ ERROR: HTTP {response.status_code}")
                results.append({
                    'agent': test_case['name'],
                    'status': '❌ ERROR',
                    'error': f'HTTP {response.status_code}'
                })
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  TIMEOUT: Request took too long (may still be processing)")
            results.append({
                'agent': test_case['name'],
                'status': '⏱️ TIMEOUT',
                'error': 'Request timeout'
            })
        except requests.exceptions.ConnectionError:
            print(f"   🔌 ERROR: Connection failed")
            results.append({
                'agent': test_case['name'],
                'status': '🔌 ERROR',
                'error': 'Connection failed'
            })
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append({
                'agent': test_case['name'],
                'status': '❌ ERROR',
                'error': str(e)
            })
    
    # Summary
    print(f"\n📊 File Processing Test Results:")
    print("=" * 60)
    
    working_agents = [r for r in results if 'WORKING' in r.get('status', '') or 'ENHANCED' in r.get('status', '')]
    partial_agents = [r for r in results if 'PARTIAL' in r.get('status', '')]
    error_agents = [r for r in results if 'ERROR' in r.get('status', '')]
    
    print(f"✅ Fully Working: {len(working_agents)}/{len(results)} agents")
    print(f"⚠️  Partially Working: {len(partial_agents)}/{len(results)} agents")
    print(f"❌ Not Working: {len(error_agents)}/{len(results)} agents")
    
    if working_agents:
        print(f"\n🎉 Agents with Enhanced File Processing:")
        for agent in working_agents:
            print(f"   • {agent['agent']}: {agent['status']}")
    
    if partial_agents:
        print(f"\n⚠️  Agents with Partial File Processing:")
        for agent in partial_agents:
            print(f"   • {agent['agent']}: {agent['status']}")
    
    if error_agents:
        print(f"\n❌ Agents with Issues:")
        for agent in error_agents:
            print(f"   • {agent['agent']}: {agent.get('error', 'Unknown error')}")
    
    # Overall assessment
    success_rate = len(working_agents) / len(results) * 100
    print(f"\n🎯 Overall File Processing Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Excellent! Most agents can process uploaded files!")
    elif success_rate >= 60:
        print("👍 Good! Majority of agents can process uploaded files!")
    elif success_rate >= 40:
        print("⚠️  Fair. Some agents can process uploaded files.")
    else:
        print("❌ Poor. Most agents cannot process uploaded files properly.")
    
    return results

if __name__ == "__main__":
    test_file_processing_capabilities()
