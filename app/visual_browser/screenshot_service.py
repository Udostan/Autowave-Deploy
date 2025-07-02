"""
Screenshot Service for Visual Browser.

This module provides a service for taking screenshots of the browser and serving them to the frontend.
"""

import os
import time
import threading
import logging
import base64
from io import BytesIO
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScreenshotService:
    """
    A service for taking screenshots of the browser and serving them to the frontend.
    """
    
    def __init__(self, live_browser):
        """
        Initialize the Screenshot Service.
        
        Args:
            live_browser: The Live Browser instance.
        """
        self.live_browser = live_browser
        self.screenshot_interval = 1.0  # seconds
        self.is_running = False
        self.screenshot_thread = None
        self.latest_screenshot = None
        self.latest_screenshot_time = 0
        self.screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'screenshots')
        
        # Create screenshots directory if it doesn't exist
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
    
    def start(self):
        """
        Start the Screenshot Service.
        """
        if self.is_running:
            logger.info("Screenshot Service is already running")
            return
        
        logger.info("Starting Screenshot Service...")
        self.is_running = True
        self.screenshot_thread = threading.Thread(target=self._screenshot_loop)
        self.screenshot_thread.daemon = True
        self.screenshot_thread.start()
        logger.info("Screenshot Service started")
    
    def stop(self):
        """
        Stop the Screenshot Service.
        """
        if not self.is_running:
            logger.info("Screenshot Service is not running")
            return
        
        logger.info("Stopping Screenshot Service...")
        self.is_running = False
        if self.screenshot_thread:
            self.screenshot_thread.join(timeout=2.0)
        logger.info("Screenshot Service stopped")
    
    def _screenshot_loop(self):
        """
        Main loop for taking screenshots.
        """
        while self.is_running:
            try:
                # Check if browser is running
                if not self.live_browser.is_running or not self.live_browser.driver:
                    logger.warning("Browser is not running, skipping screenshot")
                    time.sleep(self.screenshot_interval)
                    continue
                
                # Take screenshot
                self._take_screenshot()
                
                # Sleep for interval
                time.sleep(self.screenshot_interval)
            except Exception as e:
                logger.error(f"Error in screenshot loop: {str(e)}")
                time.sleep(self.screenshot_interval)
    
    def _take_screenshot(self):
        """
        Take a screenshot of the browser.
        """
        try:
            # Take screenshot
            screenshot_data = self.live_browser.driver.get_screenshot_as_png()
            
            # Generate filename with timestamp
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Save screenshot to file
            with open(filepath, 'wb') as f:
                f.write(screenshot_data)
            
            # Update latest screenshot
            self.latest_screenshot = f"/static/screenshots/{filename}"
            self.latest_screenshot_time = timestamp
            
            # Update browser's current screenshot
            self.live_browser.current_screenshot = self.latest_screenshot
            
            logger.debug(f"Screenshot taken and saved to {filepath}")
            
            # Optimize the image for web
            self._optimize_image(filepath)
            
            return self.latest_screenshot
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return None
    
    def _optimize_image(self, filepath):
        """
        Optimize the image for web.
        
        Args:
            filepath: Path to the image file.
        """
        try:
            # Open the image
            img = Image.open(filepath)
            
            # Resize if too large
            max_width = 1280
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)
            
            # Save with optimization
            img.save(filepath, optimize=True, quality=85)
            
            logger.debug(f"Image optimized: {filepath}")
        except Exception as e:
            logger.error(f"Error optimizing image: {str(e)}")
    
    def get_latest_screenshot(self):
        """
        Get the latest screenshot.
        
        Returns:
            dict: A dictionary containing the latest screenshot information.
        """
        return {
            'screenshot': self.latest_screenshot,
            'timestamp': self.latest_screenshot_time
        }
    
    def take_screenshot_now(self):
        """
        Take a screenshot immediately.
        
        Returns:
            str: The path to the screenshot.
        """
        return self._take_screenshot()

# Create a global instance
screenshot_service = None

def init_screenshot_service(live_browser):
    """
    Initialize the Screenshot Service.
    
    Args:
        live_browser: The Live Browser instance.
    """
    global screenshot_service
    if screenshot_service is None:
        screenshot_service = ScreenshotService(live_browser)
    return screenshot_service

def get_screenshot_service():
    """
    Get the Screenshot Service instance.
    
    Returns:
        ScreenshotService: The Screenshot Service instance.
    """
    global screenshot_service
    return screenshot_service
