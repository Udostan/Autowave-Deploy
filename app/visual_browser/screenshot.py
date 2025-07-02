#!/usr/bin/env python3
"""
Simple script to take a screenshot of a website using Selenium.
"""

import sys
import base64
import json
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def take_screenshot(url):
    """
    Take a screenshot of a website.

    Args:
        url (str): The URL to take a screenshot of.

    Returns:
        dict: A dictionary containing the screenshot and page information.
    """
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
        # Navigate to the URL
        driver.get(url)

        # Get page title
        title = driver.title

        # Take screenshot
        screenshot_bytes = driver.get_screenshot_as_png()

        # Convert to base64
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        result = {
            "success": True,
            "url": driver.current_url,
            "title": title,
            "screenshot": f"data:image/png;base64,{screenshot_base64}"
        }

        return result
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            "success": False,
            "error": str(e),
            "url": url
        }
    finally:
        # Quit the driver
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: python screenshot.py <url>"
        }))
        sys.exit(1)

    url = sys.argv[1]
    result = take_screenshot(url)
    print(json.dumps(result))
