"""
Visual Browser tools for the MCP server.
"""

import os
import time
import base64
import logging
from typing import Dict, Any, List, Optional
import traceback

# Import Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisualBrowserTools:
    """
    Tools for visual browsing using Selenium.
    """
    
    def __init__(self):
        """
        Initialize the Visual Browser tools.
        """
        self.logger = logging.getLogger(__name__)
        self.browser_instances = {}
        self.logger.info("Visual Browser tools initialized")
    
    def start_browser(self, headless: bool = True) -> Dict[str, Any]:
        """
        Start a new browser session.
        
        Args:
            headless: Whether to run the browser in headless mode
            
        Returns:
            A dictionary containing the session ID and success status
        """
        try:
            self.logger.info("Starting browser...")
            
            # Set up Chrome options
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1280,800")
            
            # Set up Chrome service
            service = Service(ChromeDriverManager().install())
            
            # Create a new Chrome driver
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Generate a session ID
            session_id = f"visual_browser_{int(time.time())}"
            
            # Store the browser instance
            self.browser_instances[session_id] = {
                "driver": driver,
                "current_url": None,
                "created_at": time.time()
            }
            
            self.logger.info(f"Browser started successfully with session ID: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "Browser session started successfully"
            }
        except Exception as e:
            self.logger.error(f"Error starting browser: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop_browser(self, session_id: str = None) -> Dict[str, Any]:
        """
        Stop a browser session.
        
        Args:
            session_id: The ID of the session to stop. If None, stops all sessions.
            
        Returns:
            A dictionary containing the success status
        """
        try:
            if not session_id:
                # Stop all browser instances
                for sid, browser_data in list(self.browser_instances.items()):
                    driver = browser_data["driver"]
                    driver.quit()
                    del self.browser_instances[sid]
                    self.logger.info(f"Stopped browser session: {sid}")
                
                return {
                    "success": True,
                    "message": "All browser sessions stopped successfully"
                }
            
            # Stop the specific browser instance
            if session_id in self.browser_instances:
                driver = self.browser_instances[session_id]["driver"]
                driver.quit()
                del self.browser_instances[session_id]
                self.logger.info(f"Stopped browser session: {session_id}")
                
                return {
                    "success": True,
                    "message": f"Browser session {session_id} stopped successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Browser session {session_id} not found"
                }
        except Exception as e:
            self.logger.error(f"Error stopping browser: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def navigate(self, url: str, session_id: str = None) -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
            session_id: The ID of the session to use. If None, creates a new session.
            
        Returns:
            A dictionary containing the result of the navigation
        """
        try:
            # Ensure URL has proper format
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
            
            self.logger.info(f"Navigating to {url}...")
            
            # Get or create a browser instance
            browser_data = self._get_or_create_browser(session_id)
            if not browser_data["success"]:
                return browser_data
            
            session_id = browser_data["session_id"]
            driver = self.browser_instances[session_id]["driver"]
            
            # Navigate to the URL
            driver.get(url)
            
            # Update current URL
            self.browser_instances[session_id]["current_url"] = driver.current_url
            
            # Get page title
            title = driver.title
            
            # Take a screenshot
            screenshot = self._take_screenshot(session_id)
            
            self.logger.info(f"Successfully navigated to {url}")
            
            return {
                "success": True,
                "session_id": session_id,
                "url": driver.current_url,
                "title": title,
                "screenshot": screenshot
            }
        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "session_id": session_id
            }
    
    def click(self, session_id: str, selector: str = None, x: int = None, y: int = None) -> Dict[str, Any]:
        """
        Click on an element or at specific coordinates.
        
        Args:
            session_id: The ID of the session to use
            selector: The CSS selector of the element to click
            x: The x-coordinate to click at
            y: The y-coordinate to click at
            
        Returns:
            A dictionary containing the result of the click
        """
        try:
            if not session_id or session_id not in self.browser_instances:
                return {
                    "success": False,
                    "error": "Invalid or missing session ID"
                }
            
            driver = self.browser_instances[session_id]["driver"]
            
            if selector:
                self.logger.info(f"Clicking on element with selector: {selector}")
                
                # Wait for the element to be clickable
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                # Click the element
                element.click()
            elif x is not None and y is not None:
                self.logger.info(f"Clicking at coordinates: ({x}, {y})")
                
                # Execute JavaScript to click at the specified coordinates
                driver.execute_script(f"document.elementFromPoint({x}, {y}).click();")
            else:
                return {
                    "success": False,
                    "error": "Either selector or coordinates (x, y) must be provided"
                }
            
            # Update current URL
            self.browser_instances[session_id]["current_url"] = driver.current_url
            
            # Take a screenshot
            screenshot = self._take_screenshot(session_id)
            
            return {
                "success": True,
                "session_id": session_id,
                "url": driver.current_url,
                "screenshot": screenshot
            }
        except Exception as e:
            self.logger.error(f"Error clicking: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def type_text(self, session_id: str, text: str, selector: str = None) -> Dict[str, Any]:
        """
        Type text into an input field.
        
        Args:
            session_id: The ID of the session to use
            text: The text to type
            selector: The CSS selector of the input field
            
        Returns:
            A dictionary containing the result of the typing
        """
        try:
            if not session_id or session_id not in self.browser_instances:
                return {
                    "success": False,
                    "error": "Invalid or missing session ID"
                }
            
            driver = self.browser_instances[session_id]["driver"]
            
            if selector:
                self.logger.info(f"Typing '{text}' into element with selector: {selector}")
                
                # Wait for the element to be visible
                element = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                
                # Clear the input field
                element.clear()
                
                # Type the text
                element.send_keys(text)
            else:
                self.logger.info(f"Typing '{text}' at current focus")
                
                # Get the active element
                active_element = driver.switch_to.active_element
                
                # Type the text
                active_element.send_keys(text)
            
            # Take a screenshot
            screenshot = self._take_screenshot(session_id)
            
            return {
                "success": True,
                "session_id": session_id,
                "screenshot": screenshot
            }
        except Exception as e:
            self.logger.error(f"Error typing: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def scroll(self, session_id: str, direction: str = 'down', distance: int = 300) -> Dict[str, Any]:
        """
        Scroll the page.
        
        Args:
            session_id: The ID of the session to use
            direction: The direction to scroll ('up', 'down', 'left', 'right')
            distance: The distance to scroll in pixels
            
        Returns:
            A dictionary containing the result of the scrolling
        """
        try:
            if not session_id or session_id not in self.browser_instances:
                return {
                    "success": False,
                    "error": "Invalid or missing session ID"
                }
            
            driver = self.browser_instances[session_id]["driver"]
            
            self.logger.info(f"Scrolling {direction} by {distance} pixels")
            
            # Determine scroll parameters based on direction
            x_scroll = 0
            y_scroll = 0
            
            if direction == 'down':
                y_scroll = distance
            elif direction == 'up':
                y_scroll = -distance
            elif direction == 'right':
                x_scroll = distance
            elif direction == 'left':
                x_scroll = -distance
            else:
                return {
                    "success": False,
                    "error": f"Invalid scroll direction: {direction}"
                }
            
            # Execute scroll
            driver.execute_script(f"window.scrollBy({x_scroll}, {y_scroll})")
            
            # Wait a moment for the scroll to complete
            time.sleep(0.5)
            
            # Take a screenshot
            screenshot = self._take_screenshot(session_id)
            
            return {
                "success": True,
                "session_id": session_id,
                "screenshot": screenshot
            }
        except Exception as e:
            self.logger.error(f"Error scrolling: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def get_page_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about the current page.
        
        Args:
            session_id: The ID of the session to use
            
        Returns:
            A dictionary containing information about the current page
        """
        try:
            if not session_id or session_id not in self.browser_instances:
                return {
                    "success": False,
                    "error": "Invalid or missing session ID"
                }
            
            driver = self.browser_instances[session_id]["driver"]
            
            self.logger.info("Getting page information...")
            
            # Get page title
            title = driver.title
            
            # Get page URL
            url = driver.current_url
            
            # Take a screenshot
            screenshot = self._take_screenshot(session_id)
            
            # Get all links on the page
            links = driver.execute_script('''
                return Array.from(document.querySelectorAll('a')).map(link => ({
                    text: link.textContent.trim(),
                    href: link.href,
                    visible: link.offsetParent !== null
                }));
            ''')
            
            # Get all images on the page
            images = driver.execute_script('''
                return Array.from(document.querySelectorAll('img')).map(img => ({
                    src: img.src,
                    alt: img.alt,
                    width: img.width,
                    height: img.height,
                    visible: img.offsetParent !== null
                }));
            ''')
            
            # Get all input fields on the page
            inputs = driver.execute_script('''
                return Array.from(document.querySelectorAll('input, textarea, select')).map(input => ({
                    type: input.type || input.tagName.toLowerCase(),
                    name: input.name,
                    id: input.id,
                    placeholder: input.placeholder,
                    value: input.value,
                    visible: input.offsetParent !== null
                }));
            ''')
            
            # Get all buttons on the page
            buttons = driver.execute_script('''
                return Array.from(document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]')).map(button => ({
                    text: button.textContent.trim() || button.value,
                    type: button.type,
                    visible: button.offsetParent !== null
                }));
            ''')
            
            return {
                "success": True,
                "session_id": session_id,
                "title": title,
                "url": url,
                "links": links,
                "images": images,
                "inputs": inputs,
                "buttons": buttons,
                "screenshot": screenshot
            }
        except Exception as e:
            self.logger.error(f"Error getting page information: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def take_screenshot(self, session_id: str, full_page: bool = False) -> Dict[str, Any]:
        """
        Take a screenshot of the current page.
        
        Args:
            session_id: The ID of the session to use
            full_page: Whether to take a screenshot of the full page
            
        Returns:
            A dictionary containing the screenshot
        """
        try:
            if not session_id or session_id not in self.browser_instances:
                return {
                    "success": False,
                    "error": "Invalid or missing session ID"
                }
            
            screenshot = self._take_screenshot(session_id, full_page)
            
            return {
                "success": True,
                "session_id": session_id,
                "screenshot": screenshot
            }
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def _take_screenshot(self, session_id: str, full_page: bool = False) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            session_id: The ID of the session to use
            full_page: Whether to take a screenshot of the full page
            
        Returns:
            The screenshot as a base64-encoded string
        """
        try:
            if not session_id or session_id not in self.browser_instances:
                return ""
            
            driver = self.browser_instances[session_id]["driver"]
            
            # Take screenshot
            screenshot_bytes = driver.get_screenshot_as_png()
            
            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return f"data:image/png;base64,{screenshot_base64}"
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            return ""
    
    def _get_or_create_browser(self, session_id: str = None) -> Dict[str, Any]:
        """
        Get an existing browser instance or create a new one.
        
        Args:
            session_id: The ID of the session to use. If None, creates a new session.
            
        Returns:
            A dictionary containing the browser instance and session ID
        """
        try:
            if session_id and session_id in self.browser_instances:
                return {
                    "success": True,
                    "session_id": session_id
                }
            elif len(self.browser_instances) > 0 and not session_id:
                # Use the first available browser instance
                session_id = next(iter(self.browser_instances))
                return {
                    "success": True,
                    "session_id": session_id
                }
            else:
                # Create a new browser instance
                result = self.start_browser()
                if result["success"]:
                    return {
                        "success": True,
                        "session_id": result["session_id"]
                    }
                else:
                    return {
                        "success": False,
                        "error": result["error"]
                    }
        except Exception as e:
            self.logger.error(f"Error getting or creating browser: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
