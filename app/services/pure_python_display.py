"""
Pure Python Virtual Display Manager

This module provides a fallback virtual display implementation using pure Python
when Xvfb is not available. It uses PIL to create an in-memory image buffer
that can be used as a virtual display.
"""

import os
import io
import base64
import logging
import threading
import time
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class PurePythonDisplay:
    """
    A pure Python implementation of a virtual display using PIL
    """
    
    def __init__(self):
        """
        Initialize the pure Python display
        """
        self.width = 800
        self.height = 600
        self.buffer = None
        self.running = False
        self.lock = threading.Lock()
        self.last_update = time.time()
        
    def start(self, width=800, height=600):
        """
        Start the virtual display
        
        Args:
            width (int): Display width
            height (int): Display height
            
        Returns:
            bool: True if display started successfully
        """
        try:
            self.width = width
            self.height = height
            
            # Create a blank image buffer
            self.buffer = Image.new('RGB', (width, height), color='black')
            
            # Draw a welcome message
            draw = ImageDraw.Draw(self.buffer)
            
            # Draw a grid pattern
            for x in range(0, width, 50):
                draw.line([(x, 0), (x, height)], fill='#333333', width=1)
            for y in range(0, height, 50):
                draw.line([(0, y), (width, y)], fill='#333333', width=1)
            
            # Draw text
            try:
                # Try to use a system font
                font = ImageFont.truetype("Arial", 20)
            except:
                # Fall back to default font
                font = ImageFont.load_default()
                
            message = "Pure Python Virtual Display"
            text_width = draw.textlength(message, font=font)
            draw.text(
                ((width - text_width) // 2, height // 2 - 30),
                message,
                fill='white',
                font=font
            )
            
            message = "No Xvfb installed - using PIL fallback"
            text_width = draw.textlength(message, font=font)
            draw.text(
                ((width - text_width) // 2, height // 2),
                message,
                fill='white',
                font=font
            )
            
            message = "GUI output will be captured here"
            text_width = draw.textlength(message, font=font)
            draw.text(
                ((width - text_width) // 2, height // 2 + 30),
                message,
                fill='white',
                font=font
            )
            
            self.running = True
            logger.info(f"Started pure Python virtual display ({width}x{height})")
            
            # Start a thread to update the display periodically
            threading.Thread(target=self._update_thread, daemon=True).start()
            
            return True
        except Exception as e:
            logger.error(f"Error starting pure Python virtual display: {str(e)}")
            return False
    
    def _update_thread(self):
        """
        Thread to update the display periodically
        """
        while self.running:
            with self.lock:
                # Update the timestamp
                self.last_update = time.time()
                
                # Add a small animation to show the display is active
                draw = ImageDraw.Draw(self.buffer)
                timestamp = time.strftime("%H:%M:%S", time.localtime())
                draw.rectangle((10, 10, 150, 40), fill='black')
                
                try:
                    font = ImageFont.truetype("Arial", 12)
                except:
                    font = ImageFont.load_default()
                    
                draw.text((15, 15), f"Time: {timestamp}", fill='white', font=font)
            
            # Sleep for a short time
            time.sleep(1)
    
    def stop(self):
        """
        Stop the virtual display
        
        Returns:
            bool: True if display stopped successfully
        """
        self.running = False
        self.buffer = None
        logger.info("Stopped pure Python virtual display")
        return True
    
    def is_running(self):
        """
        Check if the virtual display is running
        
        Returns:
            bool: True if display is running
        """
        return self.running
    
    def get_screenshot(self):
        """
        Get a screenshot of the virtual display
        
        Returns:
            PIL.Image: Screenshot image
        """
        if not self.running or self.buffer is None:
            return None
            
        with self.lock:
            # Return a copy of the buffer
            return self.buffer.copy()
    
    def get_base64_screenshot(self):
        """
        Get a base64 encoded screenshot
        
        Returns:
            str: Base64 encoded screenshot
        """
        image = self.get_screenshot()
        if image:
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        return None
    
    def update_buffer(self, image_data):
        """
        Update the display buffer with new image data
        
        Args:
            image_data: Image data to update the buffer with
            
        Returns:
            bool: True if update was successful
        """
        if not self.running:
            return False
            
        try:
            with self.lock:
                if isinstance(image_data, Image.Image):
                    # Resize the image to fit the buffer if needed
                    if image_data.size != (self.width, self.height):
                        image_data = image_data.resize((self.width, self.height))
                    self.buffer = image_data
                elif isinstance(image_data, bytes):
                    # Try to load the image from bytes
                    image = Image.open(io.BytesIO(image_data))
                    if image.size != (self.width, self.height):
                        image = image.resize((self.width, self.height))
                    self.buffer = image
                else:
                    return False
                    
                self.last_update = time.time()
                return True
        except Exception as e:
            logger.error(f"Error updating display buffer: {str(e)}")
            return False
