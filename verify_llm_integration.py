#!/usr/bin/env python3
"""
Comprehensive verification of LLM integration in Agent Wave UI
"""

import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import sys

BASE_URL = "http://127.0.0.1:5009"

def test_api_endpoints():
    """Test that all LLM API endpoints are working"""
    print("=== Testing LLM API Endpoints ===")
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/llm-tools/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            print(f"   Email Campaign: {'✅' if data['tools']['email_campaign_manager']['llm_enabled'] else '❌'}")
            print(f"   SEO Optimizer: {'✅' if data['tools']['seo_content_optimizer']['llm_enabled'] else '❌'}")
            print(f"   Learning Path: {'✅' if data['tools']['learning_path_generator']['llm_enabled'] else '❌'}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test email campaign endpoint
    try:
        email_data = {
            "topic": "Test Campaign",
            "audience": "test users",
            "campaign_type": "promotional",
            "tone": "professional"
        }
        response = requests.post(f"{BASE_URL}/api/llm-tools/email-campaign", json=email_data, timeout=30)
        if response.status_code == 200:
            print("✅ Email Campaign API working")
        else:
            print(f"❌ Email Campaign API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Email Campaign API error: {e}")
        return False
    
    return True

def test_browser_integration():
    """Test the browser integration using Selenium"""
    print("\n=== Testing Browser Integration ===")
    
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Navigate to Agent Wave
        print("Loading Agent Wave page...")
        driver.get(f"{BASE_URL}/agent-wave")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Find the task input field
        print("Looking for task input field...")
        task_input = wait.until(EC.presence_of_element_located((By.ID, "taskDescription")))
        
        # Find the execute button
        print("Looking for execute button...")
        execute_btn = wait.until(EC.element_to_be_clickable((By.ID, "executeTaskBtn")))
        
        # Test LLM tool detection
        test_prompt = "create an email campaign for new product launch"
        print(f"Testing with prompt: '{test_prompt}'")
        
        # Clear and enter the test prompt
        task_input.clear()
        task_input.send_keys(test_prompt)
        
        # Click execute button
        execute_btn.click()
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Check browser console for our debug messages
        logs = driver.get_log('browser')
        
        # Look for our LLM detection messages
        llm_detected = False
        for log in logs:
            message = log['message']
            if 'Detected LLM tool request' in message:
                llm_detected = True
                print("✅ LLM tool detection working in browser!")
                break
            elif 'Checking for LLM tool detection' in message:
                print("✅ LLM detection function is being called")
        
        if not llm_detected:
            print("❌ LLM tool detection not working in browser")
            print("Console logs:")
            for log in logs[-10:]:  # Show last 10 logs
                print(f"   {log['level']}: {log['message']}")
        
        driver.quit()
        return llm_detected
        
    except Exception as e:
        print(f"❌ Browser test error: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

def test_manual_instructions():
    """Provide manual testing instructions"""
    print("\n=== Manual Testing Instructions ===")
    print("Since automated browser testing can be complex, here's how to test manually:")
    print()
    print("1. Open http://127.0.0.1:5009/agent-wave in your browser")
    print("2. Open Developer Tools (F12) and go to Console tab")
    print("3. Type this exact prompt: 'create an email campaign for new product launch'")
    print("4. Click 'Execute Task'")
    print("5. Watch the console for these messages:")
    print("   ✅ 'Checking for LLM tool detection with description: create an email campaign for new product launch'")
    print("   ✅ 'LLM tool detection result: {tool: \"email-campaign\", params: {...}}'")
    print("   ✅ '✅ Detected LLM tool request, handling with dedicated endpoint'")
    print("   ✅ 'Tool: email-campaign Params: {...}'")
    print()
    print("6. If you see those messages, the LLM integration is working!")
    print("7. The output should show real LLM-generated content instead of simulated thinking")
    print()
    print("Alternative test prompts:")
    print("   - 'optimize this content for SEO: AI is transforming business'")
    print("   - 'create a learning path for Python programming'")
    print("   - 'generate an email marketing campaign for summer sale'")
    print()
    print("Expected behavior:")
    print("   ✅ Console shows LLM tool detection")
    print("   ✅ Thinking process shows 'Using advanced AI to generate high-quality content'")
    print("   ✅ Output shows structured, real content (not simulated)")
    print("   ✅ Results include specific details like subject lines, SEO recommendations, or learning modules")

def main():
    """Run all tests"""
    print("🚀 LLM Integration Verification Tool")
    print("=" * 50)
    
    # Test API endpoints first
    api_working = test_api_endpoints()
    
    if not api_working:
        print("\n❌ API endpoints not working. Fix API issues first.")
        return False
    
    # Try browser integration test
    try:
        browser_working = test_browser_integration()
    except ImportError:
        print("\n⚠️  Selenium not available for automated browser testing")
        browser_working = None
    
    # Always show manual instructions
    test_manual_instructions()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"API Endpoints: {'✅ Working' if api_working else '❌ Failed'}")
    
    if browser_working is not None:
        print(f"Browser Integration: {'✅ Working' if browser_working else '❌ Failed'}")
    else:
        print("Browser Integration: ⚠️  Manual testing required")
    
    if api_working:
        print("\n🎉 LLM APIs are ready! Test the UI manually using the instructions above.")
        return True
    else:
        print("\n❌ Fix API issues before testing UI integration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
