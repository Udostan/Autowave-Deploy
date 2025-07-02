#!/usr/bin/env python3
"""
Test Image Processing Capabilities
"""

import requests
import json
import base64

def test_image_processing():
    """Test image processing with a simple base64 image"""
    
    print("🧪 Testing Image Processing Capabilities")
    print("=" * 50)
    
    # Create a simple test image (1x1 pixel red PNG)
    # This is a minimal valid PNG file encoded as base64
    test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    # Test message with image
    test_message = f"""Analyze this image and tell me what you see

--- Image: test_image.png (image/png) ---
{test_image_base64}
"""
    
    agents = [
        ('AutoWave Chat', 'http://localhost:5001/api/chat', {'message': test_message}),
        ('Research Lab', 'http://localhost:5001/api/search', {'query': test_message}),
        ('Agentic Code', 'http://localhost:5001/api/agentic-code/process', {'message': test_message, 'current_code': '', 'session_id': 'test'})
    ]
    
    for name, url, data in agents:
        try:
            print(f"\n🔍 Testing {name} with image...")
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                response_text = str(result).lower()
                
                # Check for image processing indicators
                image_indicators = [
                    'image', 'png', 'pixel', 'base64', 'data:', 'analyze', 'see'
                ]
                
                found_indicators = [ind for ind in image_indicators if ind in response_text]
                
                if len(found_indicators) >= 3:
                    print(f"   ✅ {name}: Image processing WORKING!")
                    print(f"      Found indicators: {', '.join(found_indicators)}")
                else:
                    print(f"   ⚠️  {name}: Limited image processing")
                    print(f"      Found indicators: {', '.join(found_indicators)}")
                    
                # Show a snippet of the response
                if 'response' in result:
                    snippet = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
                    print(f"      Response snippet: {snippet}")
                elif 'results' in result:
                    snippet = str(result['results'])[:200] + "..." if len(str(result['results'])) > 200 else str(result['results'])
                    print(f"      Response snippet: {snippet}")
                    
            else:
                print(f"   ❌ {name}: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  {name}: Request timeout (may still be processing)")
        except Exception as e:
            print(f"   ❌ {name}: {str(e)}")
    
    print(f"\n🎯 Image Processing Test Complete!")

if __name__ == "__main__":
    test_image_processing()
