#!/usr/bin/env python3
"""
Test script for the Visual Browser.
"""

import time
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def test_visual_browser():
    """
    Test the Visual Browser functionality.
    """
    print("Starting Visual Browser test...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,800")
    
    # Set up Chrome service
    service = Service(ChromeDriverManager().install())
    
    # Create a new Chrome driver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Navigate to a URL
        print("Navigating to amazon.com...")
        driver.get("https://www.amazon.com")
        
        # Get page title
        title = driver.title
        print(f"Page title: {title}")
        
        # Take screenshot
        screenshot_bytes = driver.get_screenshot_as_png()
        
        # Convert to base64
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # Save screenshot to file
        with open("amazon_screenshot.png", "wb") as f:
            f.write(screenshot_bytes)
        
        print(f"Screenshot saved to amazon_screenshot.png")
        
        # Get all links on the page
        links = driver.execute_script('''
            return Array.from(document.querySelectorAll('a')).map(link => ({
                text: link.textContent.trim(),
                href: link.href
            })).slice(0, 5);
        ''')
        
        print("First 5 links on the page:")
        for link in links:
            print(f"- {link['text']}: {link['href']}")
        
        print("Test completed successfully!")
    finally:
        # Quit the driver
        driver.quit()

if __name__ == "__main__":
    test_visual_browser()
