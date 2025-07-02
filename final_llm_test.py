#!/usr/bin/env python3
"""
Final comprehensive test of LLM integration in Agent Wave
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5009"

def test_page_access():
    """Test that the Agent Wave page loads correctly"""
    print("=== Testing Page Access ===")
    
    try:
        response = requests.get(f"{BASE_URL}/agent-wave", timeout=10)
        if response.status_code == 200:
            print("✅ Agent Wave page loads successfully")
            print(f"   Status: {response.status_code}")
            print(f"   Content length: {len(response.text)} characters")
            
            # Check if the page contains our LLM-enabled JavaScript
            if 'simple_input_fixed.js?v=llm-tools-2024' in response.text:
                print("✅ LLM-enabled JavaScript is loaded")
            else:
                print("❌ LLM-enabled JavaScript not found")
                return False
                
            return True
        else:
            print(f"❌ Agent Wave page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing Agent Wave page: {e}")
        return False

def test_llm_apis():
    """Test all LLM API endpoints"""
    print("\n=== Testing LLM APIs ===")
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/llm-tools/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            
            all_enabled = all(
                tool['llm_enabled'] for tool in data['tools'].values()
            )
            if all_enabled:
                print("✅ All LLM tools are enabled")
            else:
                print("❌ Some LLM tools are not enabled")
                return False
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test each LLM tool
    tools_to_test = [
        {
            'name': 'Email Campaign',
            'endpoint': 'email-campaign',
            'data': {
                'topic': 'Test Campaign',
                'audience': 'test users',
                'campaign_type': 'promotional',
                'tone': 'professional'
            }
        },
        {
            'name': 'SEO Optimizer',
            'endpoint': 'seo-optimize',
            'data': {
                'content': 'Test content about AI and technology',
                'target_keywords': ['AI', 'technology'],
                'content_type': 'article'
            }
        },
        {
            'name': 'Learning Path',
            'endpoint': 'learning-path',
            'data': {
                'subject': 'Python Programming',
                'skill_level': 'beginner',
                'learning_style': 'visual',
                'time_commitment': 'moderate'
            }
        }
    ]
    
    for tool in tools_to_test:
        try:
            print(f"Testing {tool['name']}...")
            response = requests.post(
                f"{BASE_URL}/api/llm-tools/{tool['endpoint']}", 
                json=tool['data'], 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    print(f"✅ {tool['name']} API working")
                else:
                    print(f"❌ {tool['name']} API returned error: {result}")
                    return False
            else:
                print(f"❌ {tool['name']} API failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {tool['name']} API error: {e}")
            return False
    
    return True

def provide_testing_instructions():
    """Provide detailed testing instructions for the user"""
    print("\n" + "="*60)
    print("🎯 LLM INTEGRATION READY FOR TESTING!")
    print("="*60)
    
    print("\n📋 MANUAL TESTING STEPS:")
    print("1. Open http://127.0.0.1:5009/agent-wave in your browser")
    print("2. Open Developer Tools (F12) → Console tab")
    print("3. Try one of these test prompts:")
    
    test_prompts = [
        "create an email campaign for new product launch",
        "optimize this content for SEO: AI is transforming business",
        "create a learning path for Python programming",
        "generate an email marketing campaign for summer sale"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"   {i}. '{prompt}'")
    
    print("\n🔍 WHAT TO LOOK FOR IN CONSOLE:")
    print("✅ 'Checking for LLM tool detection with description: [your prompt]'")
    print("✅ 'LLM tool detection result: {tool: \"[tool-name]\", params: {...}}'")
    print("✅ '✅ Detected LLM tool request, handling with dedicated endpoint'")
    print("✅ 'Tool: [tool-name] Params: {...}'")
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("✅ Console shows LLM tool detection messages")
    print("✅ Thinking process shows 'Using advanced AI to generate high-quality content'")
    print("✅ Output shows REAL LLM-generated content (not simulated)")
    print("✅ Results include specific details like:")
    print("   • Email: Subject lines, content, performance metrics")
    print("   • SEO: Optimized content, keywords, recommendations")
    print("   • Learning: Modules, objectives, exercises, resources")
    
    print("\n❌ IF NOT WORKING:")
    print("• Console shows '❌ No LLM tool detected, using regular super-agent endpoint'")
    print("• You see simulated thinking process instead of real LLM content")
    print("• Output is generic/template-based instead of specific")
    
    print("\n🔧 TROUBLESHOOTING:")
    print("• Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)")
    print("• Clear browser cache")
    print("• Check console for JavaScript errors")
    print("• Verify the prompt matches the detection patterns")

def main():
    """Run all tests and provide instructions"""
    print("🚀 Final LLM Integration Test")
    print("="*50)
    
    # Test page access
    page_ok = test_page_access()
    
    # Test LLM APIs
    apis_ok = test_llm_apis()
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Page Access: {'✅ Working' if page_ok else '❌ Failed'}")
    print(f"LLM APIs: {'✅ Working' if apis_ok else '❌ Failed'}")
    
    if page_ok and apis_ok:
        print("\n🎉 ALL SYSTEMS GO!")
        provide_testing_instructions()
        return True
    else:
        print("\n❌ ISSUES DETECTED - Fix the problems above before testing")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
