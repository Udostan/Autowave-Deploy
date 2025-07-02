"""
API endpoints for the Visual Browser with live browsing.

This module provides API endpoints for controlling the browser server.
"""

import logging
import time
import json
import os
from flask import Blueprint, request, jsonify

# Import the browser server
from app.visual_browser.browser_server import get_browser_server

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
visual_browser_live_api = Blueprint('visual_browser_live_api', __name__)

@visual_browser_live_api.route('/status', methods=['GET'])
def get_status():
    """
    Get the status of the visual browser.
    """
    try:
        # Get browser server
        browser_server = get_browser_server()
        
        return jsonify({
            'success': True,
            'running': browser_server.running,
            'current_url': browser_server.current_url,
            'session_id': browser_server.session_id
        })
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error getting visual browser status'
        })

@visual_browser_live_api.route('/navigate', methods=['POST'])
def navigate():
    """
    Navigate to a URL.
    """
    try:
        data = request.json or {}
        url = data.get('url')

        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            })

        # Get browser server
        browser_server = get_browser_server()
        
        # Navigate to URL
        result = browser_server.navigate(url)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error navigating: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_live_api.route('/click', methods=['POST'])
def click():
    """
    Click on an element or at specific coordinates.
    """
    try:
        data = request.json or {}
        selector = data.get('selector')
        x = data.get('x')
        y = data.get('y')
        
        if not selector and (x is None or y is None):
            return jsonify({
                'success': False,
                'error': 'Either selector or coordinates (x, y) must be provided'
            })
        
        # Get browser server
        browser_server = get_browser_server()
        
        # Click on element or at coordinates
        result = browser_server.click(selector, x, y)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error clicking: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_live_api.route('/type', methods=['POST'])
def type_text():
    """
    Type text into an input field.
    """
    try:
        data = request.json or {}
        text = data.get('text')
        selector = data.get('selector')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            })
        
        # Get browser server
        browser_server = get_browser_server()
        
        # Type text
        result = browser_server.type(text, selector)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error typing: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_live_api.route('/scroll', methods=['POST'])
def scroll():
    """
    Scroll the page.
    """
    try:
        data = request.json or {}
        direction = data.get('direction', 'down')
        distance = data.get('distance', 300)
        
        # Get browser server
        browser_server = get_browser_server()
        
        # Scroll
        result = browser_server.scroll(direction, distance)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error scrolling: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_live_api.route('/back', methods=['POST'])
def go_back():
    """
    Go back in history.
    """
    try:
        # Get browser server
        browser_server = get_browser_server()
        
        # Go back
        result = browser_server.go_back()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error going back: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_live_api.route('/forward', methods=['POST'])
def go_forward():
    """
    Go forward in history.
    """
    try:
        # Get browser server
        browser_server = get_browser_server()
        
        # Go forward
        result = browser_server.go_forward()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error going forward: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_live_api.route('/info', methods=['POST'])
def get_info():
    """
    Get information about the current page.
    """
    try:
        # Get browser server
        browser_server = get_browser_server()
        
        # Get page information
        result = browser_server.get_page_info()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting page information: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@visual_browser_live_api.route('/screenshot', methods=['POST'])
def take_screenshot():
    """
    Take a screenshot of the current page.
    """
    try:
        data = request.json or {}
        full_page = data.get('full_page', False)
        
        # Get browser server
        browser_server = get_browser_server()
        
        # Take screenshot
        result = browser_server.take_screenshot(full_page)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
