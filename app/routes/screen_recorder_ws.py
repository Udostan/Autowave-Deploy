"""
Screen Recorder WebSocket Routes

This module provides WebSocket routes for the screen recorder functionality.
"""

import os
import json
import logging
import asyncio
import websockets
from flask import Blueprint, request, jsonify

from app.visual_browser.screen_recorder import websocket_handler

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
screen_recorder_ws_bp = Blueprint('screen_recorder_ws', __name__)

# WebSocket server
async def start_websocket_server(host=None, port=None):
    """
    Start the WebSocket server.

    Args:
        host: The host to bind to.
        port: The port to bind to.
    """
    # Use environment variables if available, otherwise use defaults
    host = host or os.environ.get('WEBSOCKET_HOST', '0.0.0.0')
    port = port or int(os.environ.get('WEBSOCKET_PORT', '5025'))
    try:
        logger.info(f"Starting WebSocket server on {host}:{port}")

        # Start the WebSocket server
        async with websockets.serve(websocket_handler, host, port):
            await asyncio.Future()  # Run forever
    except Exception as e:
        logger.error(f"Error starting WebSocket server: {str(e)}")

# Start the WebSocket server in a separate thread
def start_websocket_server_thread():
    """
    Start the WebSocket server in a separate thread.
    """
    try:
        import threading

        # Create a new event loop for the thread
        loop = asyncio.new_event_loop()

        # Create a thread to run the WebSocket server
        thread = threading.Thread(target=lambda: asyncio.set_event_loop(loop) or loop.run_until_complete(start_websocket_server()))
        thread.daemon = True
        thread.start()

        logger.info("WebSocket server thread started")
    except Exception as e:
        logger.error(f"Error starting WebSocket server thread: {str(e)}")

# Start the WebSocket server when this module is imported
start_websocket_server_thread()
