"""
API endpoints for the Visual Browser with LLM integration.

This module provides a synchronous implementation to avoid event loop issues.
"""

import logging
import time
import json
import os
import base64
import traceback
import threading
import queue
from flask import Blueprint, request, jsonify

# Import Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
visual_browser_api = Blueprint('visual_browser_api', __name__)

# Dictionary to store browser instances
browser_instances = {}

# Thread-safe queue for browser operations
operation_queue = queue.Queue()

# Function to take a screenshot of a website
def take_screenshot(url, timeout=30):
    """
    Take a screenshot of a website using Selenium.

    Args:
        url (str): The URL to take a screenshot of
        timeout (int): Timeout in seconds

    Returns:
        dict: A dictionary containing the result of the operation
    """
    try:
        logger.info(f"Taking screenshot of {url}...")

        # Ensure URL has proper format
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url

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
            # Set page load timeout
            driver.set_page_load_timeout(timeout)

            # Navigate to the URL
            driver.get(url)

            # Get page title
            title = driver.title

            # Get current URL (may have changed due to redirects)
            current_url = driver.current_url

            # Take screenshot
            screenshot_bytes = driver.get_screenshot_as_png()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            # Get all links on the page
            links = driver.execute_script('''
                return Array.from(document.querySelectorAll('a')).map(link => ({
                    text: link.textContent.trim(),
                    href: link.href,
                    visible: link.offsetParent !== null
                })).slice(0, 20);
            ''')

            # Get all images on the page
            images = driver.execute_script('''
                return Array.from(document.querySelectorAll('img')).map(img => ({
                    src: img.src,
                    alt: img.alt,
                    width: img.width,
                    height: img.height,
                    visible: img.offsetParent !== null
                })).slice(0, 10);
            ''')

            # Get all input fields on the page
            inputs = driver.execute_script('''
                return Array.from(document.querySelectorAll('input, textarea, select')).map(input => ({
                    type: input.type || input.tagName.toLowerCase(),
                    name: input.name,
                    id: input.id,
                    placeholder: input.placeholder,
                    visible: input.offsetParent !== null
                })).slice(0, 10);
            ''')

            # Get all buttons on the page
            buttons = driver.execute_script('''
                return Array.from(document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]')).map(button => ({
                    text: button.textContent.trim() || button.value,
                    type: button.type,
                    visible: button.offsetParent !== null
                })).slice(0, 10);
            ''')

            logger.info(f"Successfully took screenshot of {url}")

            return {
                'success': True,
                'url': current_url,
                'title': title,
                'links': links,
                'images': images,
                'inputs': inputs,
                'buttons': buttons,
                'screenshot': f"data:image/png;base64,{screenshot_base64}"
            }
        finally:
            # Always quit the driver to free resources
            driver.quit()
    except Exception as e:
        logger.error(f"Error taking screenshot of {url}: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e),
            'url': url
        }

@visual_browser_api.route('/status', methods=['GET'])
def get_status():
    """
    Get the status of the visual browser.
    """
    try:
        # Get all browser sessions
        sessions = []
        for session_id, browser in browser_instances.items():
            sessions.append({
                'session_id': session_id,
                'current_url': browser.current_url
            })

        return jsonify({
            'success': True,
            'sessions': sessions,
            'count': len(sessions)
        })
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error getting visual browser status'
        })

@visual_browser_api.route('/start', methods=['POST'])
def start_browser():
    """
    Start a new browser session.
    """
    try:
        data = request.json or {}
        headless = data.get('headless', True)
        use_llm = data.get('use_llm', True)

        # Create a new browser instance
        browser = BrowserAutomation(headless=headless, use_llm=use_llm)

        # Start the browser
        result = browser.start()

        if result['success']:
            # Store the browser instance
            browser_instances[browser.session_id] = browser

            logger.info(f"Started new browser session: {browser.session_id}")

            return jsonify({
                'success': True,
                'session_id': browser.session_id,
                'message': 'Browser session started successfully'
            })
        else:
            return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting browser: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_api.route('/stop', methods=['POST'])
def stop_browser():
    """
    Stop a browser session.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')

        if not session_id:
            # If no session ID is provided, stop all browser instances
            for sid, browser in list(browser_instances.items()):
                browser.stop()
                del browser_instances[sid]
                logger.info(f"Stopped browser session: {sid}")

            return jsonify({
                'success': True,
                'message': 'All browser sessions stopped successfully'
            })

        # Stop the specific browser instance
        if session_id in browser_instances:
            browser = browser_instances[session_id]
            result = browser.stop()

            if result['success']:
                del browser_instances[session_id]
                logger.info(f"Stopped browser session: {session_id}")

                return jsonify({
                    'success': True,
                    'message': f'Browser session {session_id} stopped successfully'
                })
            else:
                return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': f'Browser session {session_id} not found'
            })
    except Exception as e:
        logger.error(f"Error stopping browser: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_api.route('/navigate', methods=['POST'])
def navigate():
    """
    Navigate to a URL.

    This endpoint uses a synchronous approach to avoid event loop issues.
    """
    try:
        data = request.json or {}
        url = data.get('url')
        session_id = data.get('session_id')

        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            })

        # Use our synchronous screenshot function
        result = take_screenshot(url)

        # Add session_id to the result
        if result['success'] and session_id:
            result['session_id'] = session_id

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in navigate endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'url': url if 'url' in locals() else None,
            'session_id': session_id if 'session_id' in locals() else None
        })

@visual_browser_api.route('/click', methods=['POST'])
def click():
    """
    Simulate clicking on an element or at specific coordinates.

    Note: This is a simplified implementation that just returns the current page.
    In a real implementation, we would need to maintain session state.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        selector = data.get('selector')
        x = data.get('x')
        y = data.get('y')
        url = data.get('url')

        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required for clicking'
            })

        # For now, just return the current page
        # In a real implementation, we would click and then get the new state
        result = take_screenshot(url)

        # Add session_id to the result
        if result['success'] and session_id:
            result['session_id'] = session_id

            # Add click information for debugging
            result['click_info'] = {
                'selector': selector,
                'x': x,
                'y': y
            }

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in click endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'session_id': session_id if 'session_id' in locals() else None
        })

@visual_browser_api.route('/type', methods=['POST'])
def type_text():
    """
    Simulate typing text into an input field.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        text = data.get('text')
        selector = data.get('selector')

        if not session_id or session_id not in browser_instances:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing session ID'
            })

        if not text:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            })

        browser = browser_instances[session_id]

        # Type the text
        result = browser.type(text, selector)

        # Add session_id to the result
        result['session_id'] = session_id

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error typing: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'session_id': session_id if 'session_id' in locals() else None
        })

@visual_browser_api.route('/scroll', methods=['POST'])
def scroll():
    """
    Simulate scrolling the page.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        direction = data.get('direction', 'down')
        distance = data.get('distance', 300)

        if not session_id or session_id not in browser_instances:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing session ID'
            })

        browser = browser_instances[session_id]

        # Scroll the page
        result = browser.scroll(direction, distance)

        # Add session_id to the result
        result['session_id'] = session_id

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error scrolling: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'session_id': session_id if 'session_id' in locals() else None
        })

@visual_browser_api.route('/info', methods=['POST'])
def get_info():
    """
    Get information about the current page.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')

        if not session_id or session_id not in browser_instances:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing session ID'
            })

        browser = browser_instances[session_id]

        # Get page information
        result = browser.get_page_info()

        # Add session_id to the result
        result['session_id'] = session_id

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting page information: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'session_id': session_id if 'session_id' in locals() else None
        })

@visual_browser_api.route('/back', methods=['POST'])
def go_back():
    """
    Go back in history.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')

        if not session_id or session_id not in browser_instances:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing session ID'
            })

        browser = browser_instances[session_id]

        # Go back in history
        result = browser.go_back()

        # Add session_id to the result
        result['session_id'] = session_id

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error going back: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'session_id': session_id if 'session_id' in locals() else None
        })

@visual_browser_api.route('/forward', methods=['POST'])
def go_forward():
    """
    Go forward in history.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')

        if not session_id or session_id not in browser_instances:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing session ID'
            })

        browser = browser_instances[session_id]

        # Go forward in history
        result = browser.go_forward()

        # Add session_id to the result
        result['session_id'] = session_id

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error going forward: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'session_id': session_id if 'session_id' in locals() else None
        })

@visual_browser_api.route('/screenshot', methods=['POST'])
def take_screenshot():
    """
    Get the current screenshot.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        full_page = data.get('full_page', False)

        if not session_id or session_id not in browser_instances:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing session ID'
            })

        browser = browser_instances[session_id]

        # Take a screenshot
        result = browser.take_screenshot(full_page)

        # Add session_id to the result
        result['session_id'] = session_id

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'session_id': session_id if 'session_id' in locals() else None
        })

@visual_browser_api.route('/analyze', methods=['POST'])
def analyze_page():
    """
    Analyze the current page using LLM.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')

        if not session_id or session_id not in browser_instances:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing session ID'
            })

        browser = browser_instances[session_id]

        # Analyze the page
        result = browser.analyze_page()

        # Add session_id to the result
        result['session_id'] = session_id

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error analyzing page: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'session_id': session_id if 'session_id' in locals() else None
        })

@visual_browser_api.route('/execute', methods=['POST'])
def execute_instruction():
    """
    Execute a natural language instruction using LLM.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        instruction = data.get('instruction')

        if not session_id or session_id not in browser_instances:
            return jsonify({
                'success': False,
                'error': 'Invalid or missing session ID'
            })

        if not instruction:
            return jsonify({
                'success': False,
                'error': 'Instruction is required'
            })

        browser = browser_instances[session_id]

        # Execute the instruction
        result = browser.execute_instruction(instruction)

        # Add session_id to the result
        result['session_id'] = session_id

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error executing instruction: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'session_id': session_id if 'session_id' in locals() else None
        })
