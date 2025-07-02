#!/usr/bin/env python3
"""
Test AutoWave Chat File Processing
"""

import requests
import json

def test_autowave_chat():
    """Test AutoWave Chat file processing"""
    
    print("🧪 Testing AutoWave Chat File Processing")
    print("=" * 50)
    
    # Test with file content
    test_message = """Analyze this Python code

--- File: calculator.py ---
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

print("Calculator ready")
"""
    
    try:
        response = requests.post(
            'http://localhost:5001/api/chat',
            json={'message': test_message},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '').lower()
            
            print("✅ AutoWave Chat Response:")
            print("-" * 30)
            print(data.get('response', 'No response'))
            print("-" * 30)
            
            # Check for file processing indicators
            file_indicators = [
                'calculator.py', 'python', 'code', 'file', 'function',
                'add', 'multiply', 'analyze', 'uploaded'
            ]
            
            found_indicators = []
            for indicator in file_indicators:
                if indicator in response_text:
                    found_indicators.append(indicator)
            
            print(f"\n📊 File Processing Analysis:")
            print(f"Found {len(found_indicators)}/{len(file_indicators)} indicators")
            print(f"Indicators found: {', '.join(found_indicators)}")
            
            if len(found_indicators) >= 3:
                print("🎉 AutoWave Chat is processing files correctly!")
                return True
            else:
                print("⚠️  AutoWave Chat may not be processing files properly")
                return False
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_autowave_chat()
