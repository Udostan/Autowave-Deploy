"""
Simple API endpoints for the Visual Browser.

This module provides a completely synchronous implementation to avoid event loop issues.
"""

import logging
import time
import json
import os
import sys
import base64
import traceback
import subprocess
import tempfile
import requests
from flask import Blueprint, request, jsonify, Response

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
visual_browser_simple_api = Blueprint('visual_browser_simple_api', __name__)

@visual_browser_simple_api.route('/proxy', methods=['GET'])
def proxy():
    """
    Proxy a URL to avoid cross-origin issues.
    """
    try:
        url = request.args.get('url')
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            })

        # Ensure URL has proper format
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url

        logger.info(f"Proxying URL: {url}")

        # For Google and other sites with strict security, use a screenshot approach
        if 'google.com' in url or 'facebook.com' in url or 'instagram.com' in url:
            logger.info(f"Using screenshot approach for {url}")
            return _proxy_with_screenshot(url)

        # Set up headers to forward - mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Chromium";v="135", "Not-A.Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.com/',
        }

        # Add cookies from request if available
        cookies = {}
        if request.cookies:
            for key, value in request.cookies.items():
                cookies[key] = value

        # Forward the request with cookies
        session = requests.Session()
        response = session.get(url, headers=headers, cookies=cookies, stream=True, timeout=15, allow_redirects=True)

        # Get content type
        content_type = response.headers.get('Content-Type', 'text/html')

        # Create response headers - these override any headers from the original response
        response_headers = {
            'Content-Type': content_type,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'X-Frame-Options': 'ALLOWALL',  # Override X-Frame-Options to allow embedding
            'Content-Security-Policy': "default-src * 'unsafe-inline' 'unsafe-eval'; frame-ancestors * 'self'",  # Allow embedding in iframes
            'X-Content-Type-Options': 'nosniff',
        }

        # Forward cookies from the response
        for cookie in response.cookies:
            response_headers[f'Set-Cookie'] = f'{cookie.name}={cookie.value}; Path={cookie.path}; Domain={request.host}'

        # If it's HTML content, we need to modify it to allow iframe embedding
        if 'text/html' in content_type.lower():
            try:
                # Try to decode with utf-8 first
                html_content = response.content.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                # If that fails, try other common encodings
                encodings = ['latin-1', 'iso-8859-1', 'windows-1252']
                for encoding in encodings:
                    try:
                        html_content = response.content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all fail, use utf-8 with replace
                    html_content = response.content.decode('utf-8', errors='replace')

            # Add base tag to handle relative URLs
            base_tag = f'<base href="{url}">'
            if '<head>' in html_content:
                html_content = html_content.replace('<head>', f'<head>{base_tag}')
            else:
                # If no head tag, add one
                html_content = f'<head>{base_tag}</head>{html_content}'

            # Add meta tags to allow iframe embedding
            meta_tags = '''
            <meta http-equiv="Content-Security-Policy" content="frame-ancestors *">
            <meta http-equiv="X-Frame-Options" content="ALLOWALL">
            '''
            if '<head>' in html_content:
                html_content = html_content.replace('<head>', f'<head>{meta_tags}')

            # Modify the HTML to disable security features that prevent iframe embedding
            # Remove existing CSP headers
            html_content = html_content.replace('<meta http-equiv="Content-Security-Policy"', '<meta http-equiv="disabled-Content-Security-Policy"')

            # Add script to disable frame busting techniques
            anti_frame_busting_script = '''
            <script>
                // Disable common frame busting techniques
                if (window.top !== window.self) {
                    // Override properties that might be used for frame busting
                    try {
                        Object.defineProperty(window, 'top', { get: function() { return window.self; } });
                        Object.defineProperty(window, 'parent', { get: function() { return window.self; } });
                        Object.defineProperty(window, 'frameElement', { get: function() { return null; } });
                    } catch(e) {}

                    // Disable location checks
                    var originalLocation = window.location;
                    Object.defineProperty(window, 'location', {
                        get: function() { return originalLocation; },
                        set: function(value) {
                            console.log('Blocked attempt to change location to: ' + value);
                            return originalLocation;
                        }
                    });
                }
            </script>
            '''

            if '</head>' in html_content:
                html_content = html_content.replace('</head>', f'{anti_frame_busting_script}</head>')
            else:
                html_content = f'{anti_frame_busting_script}{html_content}'

            # Return the modified HTML
            return Response(
                html_content,
                status=response.status_code,
                headers=response_headers
            )
        else:
            # For non-HTML content, just pass through
            return Response(
                response.iter_content(chunk_size=1024),
                status=response.status_code,
                headers=response_headers
            )
    except Exception as e:
        logger.error(f"Error proxying URL {url if 'url' in locals() else 'unknown'}: {str(e)}")
        logger.error(traceback.format_exc())

        # Return a fallback HTML page with error information
        error_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Proxy Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5; }}
                .error-container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #d32f2f; }}
                .message {{ margin-top: 20px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; }}
                .url {{ font-weight: bold; word-break: break-all; }}
                .actions {{ margin-top: 20px; }}
                .button {{ display: inline-block; padding: 8px 16px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>Proxy Error</h1>
                <p>There was an error proxying the requested URL:</p>
                <p class="url">{url if 'url' in locals() else 'Unknown URL'}</p>
                <div class="message">
                    <p><strong>Error:</strong> {str(e)}</p>
                </div>
                <div class="actions">
                    <a href="javascript:history.back()" class="button">Go Back</a>
                </div>
                <p><small>Note: This website may have security measures that prevent it from being displayed in an iframe.</small></p>
            </div>
        </body>
        </html>
        '''

        return Response(
            error_html,
            status=500,
            headers={
                'Content-Type': 'text/html',
                'Access-Control-Allow-Origin': '*'
            }
        )

def _proxy_with_screenshot(url):
    """
    Proxy a URL by taking a screenshot and returning it as HTML.
    This is used for sites with strict security that can't be embedded.
    """
    try:
        logger.info(f"Taking screenshot of {url}")

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to take a screenshot
        script = f"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1280,800")

# Add stealth settings
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Set up Chrome service
service = Service(ChromeDriverManager().install())

# Create a new Chrome driver
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Apply additional stealth settings via JavaScript
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {{
        "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        "platform": "macOS"
    }})

    # Make navigator.webdriver undefined to avoid detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}})")

    # Add random delay to mimic human behavior
    time.sleep(0.5 + (0.5 * random.random()))

    # Navigate to the URL
    driver.get("{url}")

    # Wait for page to load
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

    # Add random delay after page load to mimic human reading
    time.sleep(1.0 + (2.0 * random.random()))

    # Simulate human-like scrolling behavior
    driver.execute_script('''
        // Scroll down slowly
        let totalHeight = 0;
        let distance = 100;
        let scrolls = 3 + Math.floor(Math.random() * 3);

        for (let i = 0; i < scrolls; i++) {{
            window.scrollBy(0, distance);
            totalHeight += distance;
        }}

        // Scroll back up partially
        setTimeout(() => {{
            window.scrollTo(0, totalHeight / 2);
        }}, 100);
    ''')

    # Add another small random delay
    time.sleep(0.3 + (0.7 * random.random()))

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Print page title and URL for capture
    print("TITLE: " + driver.title)
    print("URL: " + driver.current_url)
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running screenshot script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running screenshot script: {stderr.decode('utf-8')}"
                }), 500

            # Parse the output to get title and URL
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            final_url = url

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    final_url = line[5:]

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            # Create HTML with the screenshot
            html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>{title}</title>
                <style>
                    body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
                    .screenshot-container {{ position: relative; }}
                    .screenshot {{ width: 100%; height: auto; }}
                    .overlay {{ position: absolute; top: 0; left: 0; right: 0; background-color: rgba(0,0,0,0.7); color: white; padding: 10px; display: flex; justify-content: space-between; align-items: center; }}
                    .url {{ font-weight: bold; }}
                    .info {{ font-size: 12px; color: #ccc; }}
                    .refresh-btn {{ background-color: #4CAF50; border: none; color: white; padding: 5px 10px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; margin: 0 5px; cursor: pointer; border-radius: 3px; }}
                </style>
            </head>
            <body>
                <div class="screenshot-container">
                    <img src="data:image/png;base64,{screenshot_base64}" class="screenshot" alt="Screenshot of {title}">
                    <div class="overlay">
                        <div>
                            <span class="url">{final_url}</span>
                            <span class="info">(Screenshot mode - some interactions may not work)</span>
                        </div>
                        <button class="refresh-btn" onclick="window.location.reload()">Refresh</button>
                    </div>
                </div>
            </body>
            </html>
            '''

            # Return the HTML
            return Response(
                html,
                status=200,
                headers={
                    'Content-Type': 'text/html',
                    'Access-Control-Allow-Origin': '*',
                    'X-Frame-Options': 'ALLOWALL',
                    'Content-Security-Policy': "default-src * 'unsafe-inline' 'unsafe-eval'; frame-ancestors * 'self'",
                }
            )
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error taking screenshot of {url}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@visual_browser_simple_api.route('/navigate', methods=['POST'])
def navigate():
    """
    Navigate to a URL using a completely separate process.
    """
    try:
        data = request.json or {}
        url = data.get('url')
        session_id = data.get('session_id', 'default_session')

        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            })

        # Ensure URL has proper format
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url

        logger.info(f"Navigating to {url}...")

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to take a screenshot
        script = f"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

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
    driver.get("{url}")

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Print page title and URL for capture
    print("TITLE: " + driver.title)
    print("URL: " + driver.current_url)
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running screenshot script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running screenshot script: {stderr.decode('utf-8')}",
                    'url': url
                })

            # Parse the output to get title and URL
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            final_url = url

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    final_url = line[5:]

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            result = {
                'success': True,
                'url': final_url,
                'title': title,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'session_id': session_id
            }

            logger.info(f"Successfully navigated to {url}")

            return jsonify(result)
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error navigating to {url}: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'url': url if 'url' in locals() else None
        })

@visual_browser_simple_api.route('/click', methods=['POST'])
def click():
    """
    Simulate clicking on an element or at specific coordinates.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id', 'default_session')
        selector = data.get('selector')
        x = data.get('x')
        y = data.get('y')

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to click and take a screenshot
        script = f"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
    # Navigate to the URL (use a default URL for testing)
    driver.get("https://www.google.com")

    # Perform the click
    actions = ActionChains(driver)

    if "{selector}":
        # Click on element with selector
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "{selector}"))
        )
        actions.move_to_element(element).click().perform()
    elif {x is not None} and {y is not None}:
        # Click at coordinates
        actions.move_by_offset({x}, {y}).click().perform()

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Print page title and URL for capture
    print("TITLE: " + driver.title)
    print("URL: " + driver.current_url)
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running click script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running click script: {stderr.decode('utf-8')}"
                })

            # Parse the output to get title and URL
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            url = "Unknown"

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    url = line[5:]

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            result = {
                'success': True,
                'url': url,
                'title': title,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'session_id': session_id
            }

            logger.info(f"Successfully clicked on element")

            return jsonify(result)
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error in click endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_simple_api.route('/type', methods=['POST'])
def type_text():
    """
    Type text into an element.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id', 'default_session')
        text = data.get('text')
        selector = data.get('selector')

        if not text:
            return jsonify({
                'success': False,
                'error': 'Text is required for typing'
            })

        if not selector:
            return jsonify({
                'success': False,
                'error': 'Selector is required for typing'
            })

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to type and take a screenshot
        script = f"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
    # Navigate to the URL (use a default URL for testing)
    driver.get("https://www.google.com")

    # Find the element and type text
    element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "{selector}"))
    )
    element.clear()
    element.send_keys("{text}")

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Print page title and URL for capture
    print("TITLE: " + driver.title)
    print("URL: " + driver.current_url)
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running type script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running type script: {stderr.decode('utf-8')}"
                })

            # Parse the output to get title and URL
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            url = "Unknown"

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    url = line[5:]

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            result = {
                'success': True,
                'url': url,
                'title': title,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'session_id': session_id
            }

            logger.info(f"Successfully typed text into element")

            return jsonify(result)
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error in type endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_simple_api.route('/scroll', methods=['POST'])
def scroll():
    """
    Scroll the page.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id', 'default_session')
        direction = data.get('direction', 'down')
        distance = data.get('distance', 300)

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to scroll and take a screenshot
        script = f"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

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
    # Navigate to the URL (use a default URL for testing)
    driver.get("https://www.google.com")

    # Scroll the page
    if "{direction}" == "up":
        driver.execute_script(f"window.scrollBy(0, -{distance});")
    else:
        driver.execute_script(f"window.scrollBy(0, {distance});")

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Print page title and URL for capture
    print("TITLE: " + driver.title)
    print("URL: " + driver.current_url)
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running scroll script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running scroll script: {stderr.decode('utf-8')}"
                })

            # Parse the output to get title and URL
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            url = "Unknown"

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    url = line[5:]

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            result = {
                'success': True,
                'url': url,
                'title': title,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'session_id': session_id
            }

            logger.info(f"Successfully scrolled page {direction}")

            return jsonify(result)
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error in scroll endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_simple_api.route('/back', methods=['POST'])
def go_back():
    """
    Go back in browser history.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id', 'default_session')

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to go back and take a screenshot
        script = f"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

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
    # Navigate to the URL (use a default URL for testing)
    driver.get("https://www.google.com")

    # Navigate to another page to have history
    driver.get("https://www.google.com/search?q=test")

    # Go back
    driver.back()

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Print page title and URL for capture
    print("TITLE: " + driver.title)
    print("URL: " + driver.current_url)
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running back script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running back script: {stderr.decode('utf-8')}"
                })

            # Parse the output to get title and URL
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            url = "Unknown"

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    url = line[5:]

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            result = {
                'success': True,
                'url': url,
                'title': title,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'session_id': session_id
            }

            logger.info(f"Successfully went back in history")

            return jsonify(result)
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error in back endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_simple_api.route('/info', methods=['POST'])
def get_info():
    """
    Get information about the current page.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id', 'default_session')

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to get page info and take a screenshot
        script = f"""
import sys
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

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
    # Navigate to the URL (use a default URL for testing)
    driver.get("https://www.google.com")

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Get page info
    title = driver.title
    url = driver.current_url

    # Get links
    links = []
    for link in driver.find_elements(By.TAG_NAME, "a"):
        try:
            href = link.get_attribute("href")
            text = link.text
            is_visible = link.is_displayed()
            if href:
                links.append({{"href": href, "text": text, "visible": is_visible}})
        except:
            pass

    # Get buttons
    buttons = []
    for button in driver.find_elements(By.TAG_NAME, "button"):
        try:
            text = button.text
            is_visible = button.is_displayed()
            buttons.append({{"text": text, "visible": is_visible}})
        except:
            pass

    # Get inputs
    inputs = []
    for input_elem in driver.find_elements(By.TAG_NAME, "input"):
        try:
            input_type = input_elem.get_attribute("type")
            input_id = input_elem.get_attribute("id")
            input_name = input_elem.get_attribute("name")
            input_placeholder = input_elem.get_attribute("placeholder")
            is_visible = input_elem.is_displayed()
            inputs.append({{"type": input_type, "id": input_id, "name": input_name, "placeholder": input_placeholder, "visible": is_visible}})
        except:
            pass

    # Print page info
    print("TITLE: " + title)
    print("URL: " + url)
    print("LINKS: " + json.dumps(links))
    print("BUTTONS: " + json.dumps(buttons))
    print("INPUTS: " + json.dumps(inputs))
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running info script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running info script: {stderr.decode('utf-8')}"
                })

            # Parse the output to get page info
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            url = "Unknown"
            links = []
            buttons = []
            inputs = []

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    url = line[5:]
                elif line.startswith("LINKS: "):
                    try:
                        links = json.loads(line[7:])
                    except:
                        pass
                elif line.startswith("BUTTONS: "):
                    try:
                        buttons = json.loads(line[9:])
                    except:
                        pass
                elif line.startswith("INPUTS: "):
                    try:
                        inputs = json.loads(line[8:])
                    except:
                        pass

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            result = {
                'success': True,
                'url': url,
                'title': title,
                'links': links,
                'buttons': buttons,
                'inputs': inputs,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'session_id': session_id
            }

            logger.info(f"Successfully got page info")

            return jsonify(result)
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error in info endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_simple_api.route('/fill-form', methods=['POST'])
def fill_form():
    """
    Fill a form with the provided data.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id', 'default_session')
        form_data = data.get('form_data', {})

        if not form_data:
            return jsonify({
                'success': False,
                'error': 'Form data is required'
            })

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to fill form and take a screenshot
        script = f"""
import sys
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
    # Navigate to the URL (use a default URL for testing)
    driver.get("https://www.google.com")

    # Form data
    form_data = {json.dumps(form_data)}

    # Track successful and failed fields
    successful_fields = []
    failed_fields = []

    # Fill each field
    for selector, value in json.loads(form_data).items():
        try:
            # Find the element
            element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
            )

            # Determine the type of element
            tag_name = element.tag_name.lower()
            element_type = element.get_attribute('type')

            # Handle different types of form elements
            if tag_name == 'select':
                from selenium.webdriver.support.ui import Select
                select = Select(element)

                # Try to select by value, visible text, or index
                try:
                    select.select_by_value(value)
                except:
                    try:
                        select.select_by_visible_text(value)
                    except:
                        try:
                            select.select_by_index(int(value))
                        except:
                            raise Exception(f"Could not select option '{{value}}' in select element")
            elif tag_name == 'textarea' or (tag_name == 'input' and element_type not in ['checkbox', 'radio']):
                # Handle text inputs and textareas
                element.clear()
                element.send_keys(value)
            elif tag_name == 'input' and element_type == 'checkbox':
                # Handle checkboxes
                current_state = element.is_selected()
                desired_state = value.lower() in ['true', 'yes', 'on', '1', 'checked']

                if current_state != desired_state:
                    element.click()
            elif tag_name == 'input' and element_type == 'radio':
                # Handle radio buttons
                if value.lower() in ['true', 'yes', 'on', '1', 'checked']:
                    element.click()
            else:
                # Handle other elements
                element.clear()
                element.send_keys(value)

            successful_fields.append(selector)
        except Exception as e:
            failed_fields.append({{"selector": selector, "error": str(e)}})

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Print page info
    print("TITLE: " + driver.title)
    print("URL: " + driver.current_url)
    print("SUCCESSFUL_FIELDS: " + json.dumps(successful_fields))
    print("FAILED_FIELDS: " + json.dumps(failed_fields))
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running fill-form script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running fill-form script: {stderr.decode('utf-8')}"
                })

            # Parse the output to get form result
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            url = "Unknown"
            successful_fields = []
            failed_fields = []

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    url = line[5:]
                elif line.startswith("SUCCESSFUL_FIELDS: "):
                    try:
                        successful_fields = json.loads(line[18:])
                    except:
                        pass
                elif line.startswith("FAILED_FIELDS: "):
                    try:
                        failed_fields = json.loads(line[15:])
                    except:
                        pass

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            result = {
                'success': len(failed_fields) == 0,
                'url': url,
                'title': title,
                'successful_fields': successful_fields,
                'failed_fields': failed_fields,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'session_id': session_id
            }

            logger.info(f"Successfully filled form with {len(successful_fields)} fields")

            return jsonify(result)
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error in fill-form endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_simple_api.route('/hover', methods=['POST'])
def hover():
    """
    Hover over an element or at specific coordinates.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id', 'default_session')
        selector = data.get('selector')
        x = data.get('x')
        y = data.get('y')

        if not selector and (x is None or y is None):
            return jsonify({
                'success': False,
                'error': 'Either selector or coordinates (x, y) must be provided'
            })

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to hover and take a screenshot
        script = f"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

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
    # Navigate to the URL (use a default URL for testing)
    driver.get("https://www.google.com")

    # Create an ActionChains instance
    actions = ActionChains(driver)

    if "{selector}":
        # Hover over element with selector
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "{selector}"))
        )
        actions.move_to_element(element).perform()
    elif {x is not None} and {y is not None}:
        # Hover at coordinates
        actions.move_by_offset({x}, {y}).perform()

    # Wait a moment for any hover effects to appear
    time.sleep(0.5)

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Print page title and URL for capture
    print("TITLE: " + driver.title)
    print("URL: " + driver.current_url)
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running hover script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running hover script: {stderr.decode('utf-8')}"
                })

            # Parse the output to get title and URL
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            url = "Unknown"

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    url = line[5:]

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            result = {
                'success': True,
                'url': url,
                'title': title,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'session_id': session_id
            }

            logger.info(f"Successfully hovered over element")

            return jsonify(result)
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error in hover endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_simple_api.route('/press-key', methods=['POST'])
def press_key():
    """
    Press a key on the keyboard.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id', 'default_session')
        key = data.get('key')
        selector = data.get('selector')

        if not key:
            return jsonify({
                'success': False,
                'error': 'Key is required'
            })

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to press key and take a screenshot
        script = f"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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
    # Navigate to the URL (use a default URL for testing)
    driver.get("https://www.google.com")

    # Map key names to Keys constants
    key_mapping = {{
        'enter': Keys.ENTER,
        'tab': Keys.TAB,
        'escape': Keys.ESCAPE,
        'esc': Keys.ESCAPE,
        'space': Keys.SPACE,
        'backspace': Keys.BACK_SPACE,
        'delete': Keys.DELETE,
        'home': Keys.HOME,
        'end': Keys.END,
        'pageup': Keys.PAGE_UP,
        'pagedown': Keys.PAGE_DOWN,
        'up': Keys.UP,
        'down': Keys.DOWN,
        'left': Keys.LEFT,
        'right': Keys.RIGHT
    }}

    # Get the key constant
    key_lower = "{key}".lower()
    if key_lower in key_mapping:
        key_to_press = key_mapping[key_lower]
    else:
        key_to_press = "{key}"

    if "{selector}":
        # Focus the element
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "{selector}"))
        )
        element.click()

        # Press the key
        element.send_keys(key_to_press)
    else:
        # Get the active element
        active_element = driver.switch_to.active_element

        # Press the key
        active_element.send_keys(key_to_press)

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Print page title and URL for capture
    print("TITLE: " + driver.title)
    print("URL: " + driver.current_url)
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running press-key script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running press-key script: {stderr.decode('utf-8')}"
                })

            # Parse the output to get title and URL
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            url = "Unknown"

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    url = line[5:]

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            result = {
                'success': True,
                'url': url,
                'title': title,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'session_id': session_id
            }

            logger.info(f"Successfully pressed key '{key}'")

            return jsonify(result)
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error in press-key endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_simple_api.route('/forward', methods=['POST'])
def go_forward():
    """
    Go forward in browser history.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id', 'default_session')

        # Create a temporary file to store the screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_path = temp_file.name

        # Create a simple Python script to go forward and take a screenshot
        script = f"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

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
    # Navigate to the URL (use a default URL for testing)
    driver.get("https://www.google.com")

    # Navigate to another page to have history
    driver.get("https://www.google.com/search?q=test")

    # Go back and then forward
    driver.back()
    driver.forward()

    # Take screenshot
    driver.save_screenshot("{screenshot_path}")

    # Print page title and URL for capture
    print("TITLE: " + driver.title)
    print("URL: " + driver.current_url)
finally:
    # Quit the driver
    driver.quit()
"""

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as script_file:
            script_file.write(script.encode('utf-8'))
            script_path = script_file.name

        try:
            # Run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=30)

            # Check if the process was successful
            if process.returncode != 0:
                logger.error(f"Error running forward script: {stderr.decode('utf-8')}")
                return jsonify({
                    'success': False,
                    'error': f"Error running forward script: {stderr.decode('utf-8')}"
                })

            # Parse the output to get title and URL
            stdout_text = stdout.decode('utf-8')
            title = "Unknown"
            url = "Unknown"

            for line in stdout_text.splitlines():
                if line.startswith("TITLE: "):
                    title = line[7:]
                elif line.startswith("URL: "):
                    url = line[5:]

            # Read the screenshot file
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = f.read()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            result = {
                'success': True,
                'url': url,
                'title': title,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'session_id': session_id
            }

            logger.info(f"Successfully went forward in history")

            return jsonify(result)
        finally:
            # Clean up temporary files
            try:
                os.unlink(script_path)
                os.unlink(screenshot_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
    except Exception as e:
        logger.error(f"Error in forward endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })
