#!/usr/bin/env python3
"""
Test script to verify that screenshots are being captured and displayed correctly.
"""

import os
import sys
import base64
from app.utils.web_browser import WebBrowser

def test_screenshots():
    """Test that screenshots are being captured correctly."""
    print("Testing screenshot functionality...")
    
    # Create a web browser with advanced browser enabled
    browser = WebBrowser(
        cache_dir="test_cache",
        cache_expiry=3600,
        use_advanced_browser=True,
        max_cache_size=100,
        browser_type='auto'
    )
    
    # Test basic browsing with screenshots
    print("\nTesting screenshot capture...")
    result = browser.browse("https://www.example.com")
    
    # Check if screenshot was captured
    if result.get('screenshot'):
        print(f"Screenshot captured successfully! Size: {len(result['screenshot'])} bytes")
        
        # Save the screenshot to a file for visual inspection
        screenshot_data = result['screenshot']
        screenshot_bytes = base64.b64decode(screenshot_data)
        
        with open('test_screenshot.png', 'wb') as f:
            f.write(screenshot_bytes)
        
        print(f"Screenshot saved to test_screenshot.png")
        
        # Verify the screenshot file exists and has content
        if os.path.exists('test_screenshot.png') and os.path.getsize('test_screenshot.png') > 0:
            print("Screenshot file created successfully!")
        else:
            print("ERROR: Screenshot file was not created or is empty!")
    else:
        print("ERROR: No screenshot was captured!")
        print(f"Result keys: {result.keys()}")
    
    # Clean up
    browser._cleanup_advanced_browser()
    print("\nTest completed!")

if __name__ == "__main__":
    test_screenshots()
