#!/usr/bin/env python3
"""
Quick File Processing Test
"""

import requests
import json

def test_agents():
    """Quick test of file processing"""
    
    print("🧪 Quick File Processing Test")
    print("=" * 40)
    
    # Simple test message with file
    test_message = "Analyze this code\n\n--- File: test.py ---\nprint('Hello')\n"
    
    agents = [
        ('AutoWave Chat', 'http://localhost:5001/api/chat', {'message': test_message}),
        ('Research Lab', 'http://localhost:5001/api/search', {'query': test_message}),
        ('Agentic Code', 'http://localhost:5001/api/agentic-code/process', {'message': test_message, 'current_code': '', 'session_id': 'test'})
    ]
    
    for name, url, data in agents:
        try:
            print(f"\n🔍 Testing {name}...")
            response = requests.post(url, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                response_text = str(result).lower()
                
                # Check for file processing indicators
                if any(word in response_text for word in ['test.py', 'python', 'code', 'file', 'hello']):
                    print(f"   ✅ {name}: File processing WORKING!")
                else:
                    print(f"   ⚠️  {name}: May not be processing files")
            else:
                print(f"   ❌ {name}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {name}: {str(e)}")
    
    print(f"\n🎯 Test Complete!")

if __name__ == "__main__":
    test_agents()
