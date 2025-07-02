"""
Browser Manager Service for Visual Browser.

This module provides a service for managing browser instances for the Visual Browser.
It maintains persistent browser sessions and provides methods for interacting with them.
"""

import os
import time
import logging
import threading
import base64
from typing import Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.visual_browser.selenium_visual_browser import SeleniumVisualBrowser

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrowserManager:
    """
    A service for managing browser instances for the Visual Browser.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Create a singleton instance of the BrowserManager.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BrowserManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """
        Initialize the browser manager.
        """
        if self._initialized:
            return
        
        self._initialized = True
        self.browsers: Dict[str, SeleniumVisualBrowser] = {}
        self.last_activity: Dict[str, float] = {}
        self.cleanup_thread = threading.Thread(target=self._cleanup_inactive_browsers, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("Browser Manager initialized")

    def get_browser(self, session_id: str) -> SeleniumVisualBrowser:
        """
        Get a browser instance for the given session ID.
        
        Args:
            session_id (str): The session ID.
            
        Returns:
            SeleniumVisualBrowser: The browser instance.
        """
        with self._lock:
            # Create a new browser if one doesn't exist for this session
            if session_id not in self.browsers:
                logger.info(f"Creating new browser for session {session_id}")
                browser = SeleniumVisualBrowser(headless=False, timeout=30)
                browser.start()
                self.browsers[session_id] = browser
            
            # Update last activity time
            self.last_activity[session_id] = time.time()
            
            return self.browsers[session_id]

    def close_browser(self, session_id: str) -> Dict[str, Any]:
        """
        Close a browser instance.
        
        Args:
            session_id (str): The session ID.
            
        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        with self._lock:
            if session_id in self.browsers:
                logger.info(f"Closing browser for session {session_id}")
                browser = self.browsers[session_id]
                result = browser.stop()
                del self.browsers[session_id]
                if session_id in self.last_activity:
                    del self.last_activity[session_id]
                return result
            else:
                return {
                    'success': False,
                    'error': f"No browser found for session {session_id}"
                }

    def _cleanup_inactive_browsers(self):
        """
        Periodically clean up inactive browser instances.
        """
        # Timeout in seconds (30 minutes)
        timeout = 30 * 60
        
        while True:
            try:
                # Sleep for a while before checking
                time.sleep(60)
                
                current_time = time.time()
                sessions_to_close = []
                
                # Find inactive sessions
                with self._lock:
                    for session_id, last_time in self.last_activity.items():
                        if current_time - last_time > timeout:
                            sessions_to_close.append(session_id)
                
                # Close inactive sessions
                for session_id in sessions_to_close:
                    logger.info(f"Closing inactive browser for session {session_id}")
                    self.close_browser(session_id)
            except Exception as e:
                logger.error(f"Error in cleanup thread: {str(e)}")

    def navigate(self, session_id: str, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            session_id (str): The session ID.
            url (str): The URL to navigate to.
            
        Returns:
            Dict[str, Any]: A dictionary containing the result of the navigation.
        """
        browser = self.get_browser(session_id)
        return browser.navigate(url)

    def click(self, session_id: str, selector: str = None, x: int = None, y: int = None) -> Dict[str, Any]:
        """
        Click on an element or at specific coordinates.
        
        Args:
            session_id (str): The session ID.
            selector (str, optional): The CSS selector of the element to click. Defaults to None.
            x (int, optional): The x-coordinate to click at. Defaults to None.
            y (int, optional): The y-coordinate to click at. Defaults to None.
            
        Returns:
            Dict[str, Any]: A dictionary containing the result of the click.
        """
        browser = self.get_browser(session_id)
        return browser.click(selector, x, y)

    def type(self, session_id: str, text: str, selector: str = None) -> Dict[str, Any]:
        """
        Type text into an input field.
        
        Args:
            session_id (str): The session ID.
            text (str): The text to type.
            selector (str, optional): The CSS selector of the input field. Defaults to None.
            
        Returns:
            Dict[str, Any]: A dictionary containing the result of the typing.
        """
        browser = self.get_browser(session_id)
        return browser.type(text, selector)

    def scroll(self, session_id: str, direction: str = 'down', distance: int = 300) -> Dict[str, Any]:
        """
        Scroll the page.
        
        Args:
            session_id (str): The session ID.
            direction (str, optional): The direction to scroll ('up', 'down', 'left', 'right'). Defaults to 'down'.
            distance (int, optional): The distance to scroll in pixels. Defaults to 300.
            
        Returns:
            Dict[str, Any]: A dictionary containing the result of the scrolling.
        """
        browser = self.get_browser(session_id)
        return browser.scroll(direction, distance)

    def get_page_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about the current page.
        
        Args:
            session_id (str): The session ID.
            
        Returns:
            Dict[str, Any]: A dictionary containing information about the current page.
        """
        browser = self.get_browser(session_id)
        return browser.get_page_info()

    def take_screenshot(self, session_id: str, full_page: bool = False) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            session_id (str): The session ID.
            full_page (bool, optional): Whether to take a screenshot of the full page. Defaults to False.
            
        Returns:
            str: The screenshot as a base64-encoded string.
        """
        browser = self.get_browser(session_id)
        return browser.take_screenshot(full_page)

    def go_back(self, session_id: str) -> Dict[str, Any]:
        """
        Go back in the browser history.
        
        Args:
            session_id (str): The session ID.
            
        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            browser = self.get_browser(session_id)
            if not browser.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }
            
            logger.info(f"Going back in history for session {session_id}")
            
            # Go back in history
            browser.driver.back()
            
            # Update current URL
            browser.current_url = browser.driver.current_url
            
            # Take a screenshot
            screenshot = browser.take_screenshot()
            
            return {
                'success': True,
                'url': browser.current_url,
                'title': browser.driver.title,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error going back: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def go_forward(self, session_id: str) -> Dict[str, Any]:
        """
        Go forward in the browser history.
        
        Args:
            session_id (str): The session ID.
            
        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            browser = self.get_browser(session_id)
            if not browser.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }
            
            logger.info(f"Going forward in history for session {session_id}")
            
            # Go forward in history
            browser.driver.forward()
            
            # Update current URL
            browser.current_url = browser.driver.current_url
            
            # Take a screenshot
            screenshot = browser.take_screenshot()
            
            return {
                'success': True,
                'url': browser.current_url,
                'title': browser.driver.title,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error going forward: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def refresh(self, session_id: str) -> Dict[str, Any]:
        """
        Refresh the current page.
        
        Args:
            session_id (str): The session ID.
            
        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            browser = self.get_browser(session_id)
            if not browser.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }
            
            logger.info(f"Refreshing page for session {session_id}")
            
            # Refresh the page
            browser.driver.refresh()
            
            # Update current URL
            browser.current_url = browser.driver.current_url
            
            # Take a screenshot
            screenshot = browser.take_screenshot()
            
            return {
                'success': True,
                'url': browser.current_url,
                'title': browser.driver.title,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error refreshing page: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def fill_form(self, session_id: str, form_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Fill a form with the provided data.
        
        Args:
            session_id (str): The session ID.
            form_data (Dict[str, str]): A dictionary mapping field selectors to values.
            
        Returns:
            Dict[str, Any]: A dictionary containing the result of the form filling.
        """
        try:
            browser = self.get_browser(session_id)
            if not browser.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }
            
            logger.info(f"Filling form with {len(form_data)} fields for session {session_id}")
            
            # Keep track of successful and failed fields
            successful_fields = []
            failed_fields = []
            
            # Fill each field
            for selector, value in form_data.items():
                try:
                    logger.info(f"Filling field with selector '{selector}' with value '{value}'")
                    
                    # Wait for the element to be visible
                    element = WebDriverWait(browser.driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    # Determine the type of element
                    tag_name = element.tag_name.lower()
                    element_type = element.get_attribute('type')
                    
                    # Handle different types of form elements
                    if tag_name == 'select':
                        # Handle select elements
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
                                    raise Exception(f"Could not select option '{value}' in select element")
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
                    logger.error(f"Error filling field with selector '{selector}': {str(e)}")
                    failed_fields.append({
                        'selector': selector,
                        'error': str(e)
                    })
            
            # Take a screenshot
            screenshot = browser.take_screenshot()
            
            return {
                'success': len(failed_fields) == 0,
                'screenshot': screenshot,
                'successful_fields': successful_fields,
                'failed_fields': failed_fields
            }
        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def press_key(self, session_id: str, key: str, selector: str = None) -> Dict[str, Any]:
        """
        Press a key on the keyboard.
        
        Args:
            session_id (str): The session ID.
            key (str): The key to press (e.g., 'Enter', 'Tab', 'Escape').
            selector (str, optional): The CSS selector of the element to focus before pressing the key. Defaults to None.
            
        Returns:
            Dict[str, Any]: A dictionary containing the result of the key press.
        """
        try:
            browser = self.get_browser(session_id)
            if not browser.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }
            
            # Map key names to Keys constants
            from selenium.webdriver.common.keys import Keys
            key_mapping = {
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
                'right': Keys.RIGHT,
                'f1': Keys.F1,
                'f2': Keys.F2,
                'f3': Keys.F3,
                'f4': Keys.F4,
                'f5': Keys.F5,
                'f6': Keys.F6,
                'f7': Keys.F7,
                'f8': Keys.F8,
                'f9': Keys.F9,
                'f10': Keys.F10,
                'f11': Keys.F11,
                'f12': Keys.F12
            }
            
            # Get the key constant
            key_lower = key.lower()
            if key_lower in key_mapping:
                key_to_press = key_mapping[key_lower]
            else:
                key_to_press = key
            
            if selector:
                logger.info(f"Pressing key '{key}' on element with selector: {selector}")
                
                try:
                    # Wait for the element to be visible
                    element = WebDriverWait(browser.driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    # Focus the element
                    element.click()
                    
                    # Press the key
                    element.send_keys(key_to_press)
                except Exception as e:
                    logger.error(f"Error pressing key on element with selector {selector}: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error pressing key on element: {str(e)}"
                    }
            else:
                logger.info(f"Pressing key '{key}' on active element")
                
                try:
                    # Get the active element
                    active_element = browser.driver.switch_to.active_element
                    
                    # Press the key
                    active_element.send_keys(key_to_press)
                except Exception as e:
                    logger.error(f"Error pressing key on active element: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error pressing key on active element: {str(e)}"
                    }
            
            # Update current URL if it changed
            current_url = browser.driver.current_url
            if current_url != browser.current_url:
                browser.current_url = current_url
            
            # Take a screenshot
            screenshot = browser.take_screenshot()
            
            return {
                'success': True,
                'url': browser.current_url,
                'title': browser.driver.title,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error pressing key: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Create a singleton instance
browser_manager = BrowserManager()
