"""
Browser Proxy API for the Live Browser.

This module provides API endpoints for proxying browser requests.
"""

import os
import time
import json
import logging
import traceback
import requests
from urllib.parse import urlparse, quote
from flask import Blueprint, request, jsonify, Response, stream_with_context

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Blueprint
browser_proxy_api = Blueprint('browser_proxy_api', __name__, url_prefix='/api/live-browser')

@browser_proxy_api.route('/proxy', methods=['GET'])
def proxy_request():
    """
    Proxy a browser request.
    """
    try:
        # Get URL from query parameter
        url = request.args.get('url')
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
        
        # Ensure URL has protocol
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        # Parse URL
        parsed_url = urlparse(url)
        
        # Set headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': f"{parsed_url.scheme}://{parsed_url.netloc}",
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Make request
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        
        # Get content type
        content_type = response.headers.get('Content-Type', 'text/html')
        
        # Create response
        def generate():
            for chunk in response.iter_content(chunk_size=4096):
                yield chunk
        
        # Return response
        return Response(
            stream_with_context(generate()),
            headers={
                'Content-Type': content_type,
                'Access-Control-Allow-Origin': '*',
                'X-Frame-Options': 'ALLOWALL',
                'Content-Security-Policy': "frame-ancestors 'self' *"
            }
        )
    except Exception as e:
        logger.error(f"Error in proxy endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
