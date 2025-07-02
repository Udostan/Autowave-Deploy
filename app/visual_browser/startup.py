"""
Startup script for the Visual Browser.

This module provides a function to start the Visual Browser WebSocket server.
"""

import logging
import threading
from app.visual_browser.websocket_server import start_websocket_server_thread
from app.visual_browser.live_browser import live_browser

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_visual_browser_services():
    """
    Start the Visual Browser services.
    """
    try:
        logger.info("Starting Visual Browser services...")
        print("Starting Visual Browser services...")

        # Start the WebSocket server
        logger.info("Starting WebSocket server thread...")
        print("Starting WebSocket server thread...")
        websocket_thread = start_websocket_server_thread()

        if websocket_thread:
            logger.info("Visual Browser WebSocket server started successfully")
            print("Visual Browser WebSocket server started successfully")
        else:
            logger.error("Failed to start Visual Browser WebSocket server")
            print("Failed to start Visual Browser WebSocket server")

        # Initialize screenshot service
        try:
            logger.info("Initializing screenshot service...")
            print("Initializing screenshot service...")
            from app.visual_browser.screenshot_service import init_screenshot_service
            screenshot_service = init_screenshot_service(live_browser)

            # Start the browser if it's not already running
            if not live_browser.is_running:
                logger.info("Starting live browser...")
                print("Starting live browser...")
                live_browser.start()

            # Start the screenshot service
            if screenshot_service:
                logger.info("Starting screenshot service...")
                print("Starting screenshot service...")
                screenshot_service.start()
                logger.info("Screenshot service started successfully")
                print("Screenshot service started successfully")
        except Exception as ss_error:
            logger.error(f"Error initializing screenshot service: {str(ss_error)}")
            print(f"Error initializing screenshot service: {str(ss_error)}")

        logger.info("Visual Browser services started")
        print("Visual Browser services started")
    except Exception as e:
        logger.error(f"Error starting Visual Browser services: {str(e)}")
        print(f"Error starting Visual Browser services: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(error_trace)
        print(error_trace)
