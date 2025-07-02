"""
Virtual Display Manager for headless GUI applications

This module provides functionality to create and manage virtual displays
for running GUI applications in a headless environment.
"""

import os
import time
import logging
import tempfile
import subprocess
from PIL import Image
import base64
import io

# Import the pure Python display fallback
from app.services.pure_python_display import PurePythonDisplay

logger = logging.getLogger(__name__)

class VirtualDisplayManager:
    """
    Manages virtual displays for headless GUI applications
    """

    def __init__(self):
        """
        Initialize the virtual display manager
        """
        self.display_process = None
        self.display_num = None
        self.xvfb_installed = self._check_xvfb_installed()

        # Initialize the pure Python display fallback
        self.pure_python_display = None
        self.using_fallback = False

    def _check_xvfb_installed(self):
        """
        Check if Xvfb is installed on the system

        Returns:
            bool: True if Xvfb is installed, False otherwise
        """
        try:
            # Check if Xvfb is installed
            result = subprocess.run(['which', 'Xvfb'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            is_installed = result.returncode == 0

            if not is_installed:
                logger.warning("Xvfb is not installed. GUI applications will run in the local environment.")
                logger.warning("To install Xvfb:")
                logger.warning("  - On Ubuntu/Debian: sudo apt-get install xvfb")
                logger.warning("  - On macOS: brew install xquartz")
                logger.warning("  - See deployment_guide.md for more details")
            return is_installed
        except Exception as e:
            logger.warning(f"Error checking for Xvfb: {str(e)}")
            return False

    def start_display(self, width=800, height=600, depth=24):
        """
        Start a virtual display

        Args:
            width (int): Display width
            height (int): Display height
            depth (int): Color depth

        Returns:
            bool: True if display started successfully, False otherwise
        """
        # Try to start Xvfb if installed
        if self.xvfb_installed:
            # Find an available display number
            for i in range(99, 999):
                if not os.path.exists(f"/tmp/.X{i}-lock"):
                    self.display_num = i
                    break

            if self.display_num is None:
                logger.error("Could not find an available display number")
                return self._start_fallback_display(width, height)

            # Start Xvfb
            try:
                cmd = [
                    'Xvfb', f':{self.display_num}', '-screen', '0',
                    f'{width}x{height}x{depth}', '-ac', '+extension', 'GLX',
                    '+render', '-noreset'
                ]
                self.display_process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

                # Wait for display to start
                time.sleep(1)

                # Check if process is still running
                if self.display_process.poll() is not None:
                    logger.error("Xvfb process terminated unexpectedly")
                    return self._start_fallback_display(width, height)

                # Set display environment variable
                os.environ['DISPLAY'] = f':{self.display_num}'
                logger.info(f"Started virtual display :{self.display_num}")
                self.using_fallback = False
                return True
            except Exception as e:
                logger.error(f"Error starting virtual display: {str(e)}")
                return self._start_fallback_display(width, height)
        else:
            # Xvfb not installed, use fallback
            logger.warning("Xvfb not installed, using pure Python fallback display")
            return self._start_fallback_display(width, height)

    def _start_fallback_display(self, width=800, height=600):
        """
        Start a pure Python fallback display

        Args:
            width (int): Display width
            height (int): Display height

        Returns:
            bool: True if fallback display started successfully
        """
        try:
            # Create a new pure Python display
            self.pure_python_display = PurePythonDisplay()
            success = self.pure_python_display.start(width, height)

            if success:
                logger.info("Started pure Python fallback display")
                self.using_fallback = True
                return True
            else:
                logger.error("Failed to start pure Python fallback display")
                return False
        except Exception as e:
            logger.error(f"Error starting pure Python fallback display: {str(e)}")
            return False

    def stop_display(self):
        """
        Stop the virtual display

        Returns:
            bool: True if display stopped successfully, False otherwise
        """
        # If using the fallback display, stop it
        if self.using_fallback and self.pure_python_display is not None:
            try:
                success = self.pure_python_display.stop()
                self.pure_python_display = None
                self.using_fallback = False
                logger.info("Stopped pure Python fallback display")
                return success
            except Exception as e:
                logger.error(f"Error stopping pure Python fallback display: {str(e)}")
                self.pure_python_display = None
                self.using_fallback = False
                return False

        # Otherwise, stop the Xvfb display
        if self.display_process is None:
            return True

        try:
            self.display_process.terminate()
            self.display_process.wait(timeout=5)
            self.display_process = None
            self.display_num = None
            logger.info("Stopped virtual display")
            return True
        except Exception as e:
            logger.error(f"Error stopping virtual display: {str(e)}")
            try:
                self.display_process.kill()
            except:
                pass
            self.display_process = None
            self.display_num = None
            return False

    def capture_screen(self, x=0, y=0, width=800, height=600):
        """
        Capture a screenshot of the virtual display

        Args:
            x (int): X coordinate of the capture area
            y (int): Y coordinate of the capture area
            width (int): Width of the capture area
            height (int): Height of the capture area

        Returns:
            PIL.Image or None: Screenshot image or None if capture failed
        """
        # If using the fallback display, get screenshot from it
        if self.using_fallback and self.pure_python_display is not None:
            try:
                image = self.pure_python_display.get_screenshot()
                if image and (x != 0 or y != 0 or width != image.width or height != image.height):
                    image = image.crop((x, y, x + width, y + height))
                return image
            except Exception as e:
                logger.error(f"Error capturing screenshot from fallback display: {str(e)}")
                return None

        # Otherwise, capture from Xvfb display
        if not self.display_num:
            logger.warning("No virtual display running")
            return None

        try:
            # Use xwd to capture the screen
            with tempfile.NamedTemporaryFile(suffix='.xwd') as temp_file:
                subprocess.run(
                    ['xwd', '-display', f':{self.display_num}', '-root', '-out', temp_file.name],
                    check=True
                )

                # Convert xwd to png
                with tempfile.NamedTemporaryFile(suffix='.png') as png_file:
                    subprocess.run(
                        ['convert', temp_file.name, png_file.name],
                        check=True
                    )

                    # Open the image with PIL
                    image = Image.open(png_file.name)

                    # Crop if needed
                    if x != 0 or y != 0 or width != image.width or height != image.height:
                        image = image.crop((x, y, x + width, y + height))

                    return image
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return None

    def get_base64_screenshot(self, x=0, y=0, width=800, height=600):
        """
        Get a base64 encoded screenshot

        Args:
            x (int): X coordinate of the capture area
            y (int): Y coordinate of the capture area
            width (int): Width of the capture area
            height (int): Height of the capture area

        Returns:
            str or None: Base64 encoded screenshot or None if capture failed
        """
        # If using the fallback display, get base64 screenshot directly
        if self.using_fallback and self.pure_python_display is not None:
            try:
                return self.pure_python_display.get_base64_screenshot()
            except Exception as e:
                logger.error(f"Error getting base64 screenshot from fallback display: {str(e)}")
                return None

        # Otherwise, capture from Xvfb display and convert to base64
        image = self.capture_screen(x, y, width, height)
        if image:
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode()
        return None

    def is_display_running(self):
        """
        Check if the virtual display is running

        Returns:
            bool: True if display is running, False otherwise
        """
        # Check if the fallback display is running
        if self.using_fallback and self.pure_python_display is not None:
            return self.pure_python_display.is_running()

        # Otherwise, check if the Xvfb display is running
        return (self.display_process is not None and
                self.display_process.poll() is None)
