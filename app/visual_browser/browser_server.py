"""
Browser Automation Server for Visual Browser.

This module provides a continuous browser automation server that can be controlled via API.
"""

import os
import time
import base64
import logging
import threading
import queue
import json
from typing import Dict, Any, List, Optional

# Import Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrowserServer:
    """
    Browser Automation Server for Visual Browser.
    """

    def __init__(self, headless: bool = False, timeout: int = 30):
        """
        Initialize the browser server.

        Args:
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to False.
            timeout (int, optional): Default timeout in seconds. Defaults to 30.
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.session_id = f"visual_browser_{int(time.time())}"
        self.current_url = None
        self.history = []
        self.history_index = -1
        self.command_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.running = False
        self.thread = None

        logger.info(f"Browser server initialized with session ID: {self.session_id}")

    def start(self):
        """
        Start the browser server.
        """
        if self.running:
            logger.info("Browser server already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()

        logger.info("Browser server started")

    def stop(self):
        """
        Stop the browser server.
        """
        if not self.running:
            logger.info("Browser server not running")
            return

        self.running = False
        self.command_queue.put(("stop", {}))

        if self.thread:
            self.thread.join(timeout=5)

        logger.info("Browser server stopped")

    def _run_server(self):
        """
        Run the browser server.
        """
        try:
            # Initialize the browser
            self._init_browser()

            # Process commands
            while self.running:
                try:
                    # Get command from queue with timeout
                    command, params = self.command_queue.get(timeout=0.1)

                    # Process command
                    if command == "stop":
                        break
                    elif command == "navigate":
                        result = self._navigate(**params)
                        self.result_queue.put(result)
                    elif command == "click":
                        result = self._click(**params)
                        self.result_queue.put(result)
                    elif command == "type":
                        result = self._type(**params)
                        self.result_queue.put(result)
                    elif command == "scroll":
                        result = self._scroll(**params)
                        self.result_queue.put(result)
                    elif command == "screenshot":
                        result = self._take_screenshot(**params)
                        self.result_queue.put(result)
                    elif command == "get_info":
                        result = self._get_page_info()
                        self.result_queue.put(result)
                    elif command == "back":
                        result = self._go_back()
                        self.result_queue.put(result)
                    elif command == "forward":
                        result = self._go_forward()
                        self.result_queue.put(result)
                    elif command == "fill_form":
                        result = self._fill_form(**params)
                        self.result_queue.put(result)
                    elif command == "hover":
                        result = self._hover(**params)
                        self.result_queue.put(result)
                    elif command == "drag_and_drop":
                        result = self._drag_and_drop(**params)
                        self.result_queue.put(result)
                    elif command == "press_key":
                        result = self._press_key(**params)
                        self.result_queue.put(result)
                    else:
                        logger.warning(f"Unknown command: {command}")
                        self.result_queue.put({
                            "success": False,
                            "error": f"Unknown command: {command}"
                        })
                except queue.Empty:
                    # No command, take a screenshot to keep the UI updated
                    if self.driver and self.current_url:
                        screenshot = self._take_screenshot()
                        # You could send this to a WebSocket here
                except Exception as e:
                    logger.error(f"Error processing command: {str(e)}")
                    self.result_queue.put({
                        "success": False,
                        "error": str(e)
                    })
        finally:
            # Clean up
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None

    def _init_browser(self):
        """
        Initialize the browser.
        """
        try:
            logger.info("Initializing browser...")

            # Set up Chrome options
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless=new")

            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1280,800")

            # Set up Chrome service
            service = Service(ChromeDriverManager().install())

            # Create a new Chrome driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Set default timeout
            self.driver.set_page_load_timeout(self.timeout)

            logger.info("Browser initialized successfully")

            return True
        except Exception as e:
            logger.error(f"Error initializing browser: {str(e)}")
            return False

    def _navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL.

        Args:
            url (str): The URL to navigate to.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the navigation.
        """
        try:
            # Ensure URL has proper format
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url

            logger.info(f"Navigating to {url}...")

            # Navigate to the URL
            self.driver.get(url)

            # Update current URL
            self.current_url = self.driver.current_url

            # Add to history
            self._add_to_history(self.current_url)

            # Get page title
            title = self.driver.title

            # Take a screenshot
            screenshot = self._take_screenshot()

            logger.info(f"Successfully navigated to {url}")

            return {
                'success': True,
                'url': self.current_url,
                'title': title,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    def _click(self, selector: str = None, x: int = None, y: int = None) -> Dict[str, Any]:
        """
        Click on an element or at specific coordinates.

        Args:
            selector (str, optional): The CSS selector of the element to click. Defaults to None.
            x (int, optional): The x-coordinate to click at. Defaults to None.
            y (int, optional): The y-coordinate to click at. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the click.
        """
        try:
            if selector:
                logger.info(f"Clicking on element with selector: {selector}")

                try:
                    # Wait for the element to be clickable
                    element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )

                    # Click the element
                    element.click()
                except Exception as e:
                    logger.error(f"Error clicking on element with selector {selector}: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error clicking on element: {str(e)}"
                    }
            elif x is not None and y is not None:
                logger.info(f"Clicking at coordinates: ({x}, {y})")

                try:
                    # Execute JavaScript to click at the specified coordinates
                    self.driver.execute_script(f"document.elementFromPoint({x}, {y}).click();")
                except Exception as e:
                    logger.error(f"Error clicking at coordinates ({x}, {y}): {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error clicking at coordinates: {str(e)}"
                    }
            else:
                return {
                    'success': False,
                    'error': 'Either selector or coordinates (x, y) must be provided'
                }

            # Check if URL changed
            current_url = self.driver.current_url
            if current_url != self.current_url:
                # Update current URL
                self.current_url = current_url

                # Add to history
                self._add_to_history(self.current_url)

            # Take a screenshot
            screenshot = self._take_screenshot()

            return {
                'success': True,
                'url': self.current_url,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error clicking: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _type(self, text: str, selector: str = None) -> Dict[str, Any]:
        """
        Type text into an input field.

        Args:
            text (str): The text to type.
            selector (str, optional): The CSS selector of the input field. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the typing.
        """
        try:
            if selector:
                logger.info(f"Typing '{text}' into element with selector: {selector}")

                try:
                    # Wait for the element to be visible
                    element = WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )

                    # Clear the input field
                    element.clear()

                    # Type the text
                    element.send_keys(text)
                except Exception as e:
                    logger.error(f"Error typing into element with selector {selector}: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error typing into element: {str(e)}"
                    }
            else:
                logger.info(f"Typing '{text}' at current focus")

                try:
                    # Get the active element
                    active_element = self.driver.switch_to.active_element

                    # Type the text
                    active_element.send_keys(text)
                except Exception as e:
                    logger.error(f"Error typing at current focus: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error typing at current focus: {str(e)}"
                    }

            # Take a screenshot
            screenshot = self._take_screenshot()

            return {
                'success': True,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error typing: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _scroll(self, direction: str = 'down', distance: int = 300) -> Dict[str, Any]:
        """
        Scroll the page.

        Args:
            direction (str, optional): The direction to scroll ('up', 'down', 'left', 'right'). Defaults to 'down'.
            distance (int, optional): The distance to scroll in pixels. Defaults to 300.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the scrolling.
        """
        try:
            logger.info(f"Scrolling {direction} by {distance} pixels")

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
                    'success': False,
                    'error': f"Invalid scroll direction: {direction}"
                }

            try:
                # Execute scroll
                self.driver.execute_script(f"window.scrollBy({x_scroll}, {y_scroll})")

                # Wait a moment for the scroll to complete
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error scrolling {direction}: {str(e)}")
                return {
                    'success': False,
                    'error': f"Error scrolling: {str(e)}"
                }

            # Take a screenshot
            screenshot = self._take_screenshot()

            return {
                'success': True,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error scrolling: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_page_info(self) -> Dict[str, Any]:
        """
        Get information about the current page.

        Returns:
            Dict[str, Any]: A dictionary containing information about the current page.
        """
        try:
            logger.info("Getting page information...")

            # Get page title
            title = self.driver.title

            # Get page URL
            url = self.driver.current_url

            # Take a screenshot
            screenshot = self._take_screenshot()

            # Get all links on the page
            links = self.driver.execute_script('''
                return Array.from(document.querySelectorAll('a')).map(link => ({
                    text: link.textContent.trim(),
                    href: link.href,
                    visible: link.offsetParent !== null
                }));
            ''')

            # Get all images on the page
            images = self.driver.execute_script('''
                return Array.from(document.querySelectorAll('img')).map(img => ({
                    src: img.src,
                    alt: img.alt,
                    width: img.width,
                    height: img.height,
                    visible: img.offsetParent !== null
                }));
            ''')

            # Get all input fields on the page
            inputs = self.driver.execute_script('''
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
            buttons = self.driver.execute_script('''
                return Array.from(document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]')).map(button => ({
                    text: button.textContent.trim() || button.value,
                    type: button.type,
                    visible: button.offsetParent !== null
                }));
            ''')

            return {
                'success': True,
                'title': title,
                'url': url,
                'links': links,
                'images': images,
                'inputs': inputs,
                'buttons': buttons,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error getting page information: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _go_back(self) -> Dict[str, Any]:
        """
        Go back in history.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if self.history_index <= 0:
                return {
                    'success': False,
                    'error': 'No history to go back to'
                }

            logger.info("Going back in history...")

            # Go back in history
            self.history_index -= 1
            url = self.history[self.history_index]

            # Navigate to the URL
            return self._navigate(url)
        except Exception as e:
            logger.error(f"Error going back: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _go_forward(self) -> Dict[str, Any]:
        """
        Go forward in history.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if self.history_index >= len(self.history) - 1:
                return {
                    'success': False,
                    'error': 'No history to go forward to'
                }

            logger.info("Going forward in history...")

            # Go forward in history
            self.history_index += 1
            url = self.history[self.history_index]

            # Navigate to the URL
            return self._navigate(url)
        except Exception as e:
            logger.error(f"Error going forward: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _take_screenshot(self, full_page: bool = False) -> str:
        """
        Take a screenshot of the current page.

        Args:
            full_page (bool, optional): Whether to take a screenshot of the full page. Defaults to False.

        Returns:
            str: The screenshot as a base64-encoded string.
        """
        try:
            # Take screenshot
            screenshot_bytes = self.driver.get_screenshot_as_png()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            return f"data:image/png;base64,{screenshot_base64}"
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return ""

    def _add_to_history(self, url: str) -> None:
        """
        Add a URL to the history.

        Args:
            url (str): The URL to add to the history.
        """
        # Remove forward history if we're not at the end
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        # Add URL to history
        self.history.append(url)
        self.history_index = len(self.history) - 1

    def _fill_form(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Fill a form with the provided data.

        Args:
            form_data (Dict[str, str]): A dictionary mapping field selectors to values.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the form filling.
        """
        try:
            logger.info(f"Filling form with {len(form_data)} fields")

            # Keep track of successful and failed fields
            successful_fields = []
            failed_fields = []

            # Fill each field
            for selector, value in form_data.items():
                try:
                    logger.info(f"Filling field with selector '{selector}' with value '{value}'")

                    # Wait for the element to be visible
                    element = WebDriverWait(self.driver, 10).until(
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
            screenshot = self._take_screenshot()

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

    def _hover(self, selector: str = None, x: int = None, y: int = None) -> Dict[str, Any]:
        """
        Hover over an element or at specific coordinates.

        Args:
            selector (str, optional): The CSS selector of the element to hover over. Defaults to None.
            x (int, optional): The x-coordinate to hover at. Defaults to None.
            y (int, optional): The y-coordinate to hover at. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the hover.
        """
        try:
            # Create an ActionChains instance
            actions = ActionChains(self.driver)

            if selector:
                logger.info(f"Hovering over element with selector: {selector}")

                try:
                    # Wait for the element to be visible
                    element = WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )

                    # Move to the element
                    actions.move_to_element(element).perform()
                except Exception as e:
                    logger.error(f"Error hovering over element with selector {selector}: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error hovering over element: {str(e)}"
                    }
            elif x is not None and y is not None:
                logger.info(f"Hovering at coordinates: ({x}, {y})")

                try:
                    # Move to the specified coordinates
                    actions.move_by_offset(x, y).perform()
                except Exception as e:
                    logger.error(f"Error hovering at coordinates ({x}, {y}): {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error hovering at coordinates: {str(e)}"
                    }
            else:
                return {
                    'success': False,
                    'error': 'Either selector or coordinates (x, y) must be provided'
                }

            # Wait a moment for any hover effects to appear
            time.sleep(0.5)

            # Take a screenshot
            screenshot = self._take_screenshot()

            return {
                'success': True,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error hovering: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _drag_and_drop(self, source_selector: str, target_selector: str) -> Dict[str, Any]:
        """
        Drag an element and drop it on another element.

        Args:
            source_selector (str): The CSS selector of the element to drag.
            target_selector (str): The CSS selector of the element to drop onto.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the drag and drop.
        """
        try:
            logger.info(f"Dragging element with selector '{source_selector}' to element with selector '{target_selector}'")

            # Wait for the source element to be visible
            source_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, source_selector))
            )

            # Wait for the target element to be visible
            target_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, target_selector))
            )

            # Create an ActionChains instance
            actions = ActionChains(self.driver)

            # Perform the drag and drop
            actions.drag_and_drop(source_element, target_element).perform()

            # Wait a moment for any effects to appear
            time.sleep(0.5)

            # Take a screenshot
            screenshot = self._take_screenshot()

            return {
                'success': True,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error dragging and dropping: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _press_key(self, key: str, selector: str = None) -> Dict[str, Any]:
        """
        Press a key on the keyboard.

        Args:
            key (str): The key to press (e.g., 'Enter', 'Tab', 'Escape').
            selector (str, optional): The CSS selector of the element to focus before pressing the key. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the key press.
        """
        try:
            # Map key names to Keys constants
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
                    element = WebDriverWait(self.driver, 10).until(
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
                    active_element = self.driver.switch_to.active_element

                    # Press the key
                    active_element.send_keys(key_to_press)
                except Exception as e:
                    logger.error(f"Error pressing key on active element: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error pressing key on active element: {str(e)}"
                    }

            # Check if URL changed
            current_url = self.driver.current_url
            if current_url != self.current_url:
                # Update current URL
                self.current_url = current_url

                # Add to history
                self._add_to_history(self.current_url)

            # Take a screenshot
            screenshot = self._take_screenshot()

            return {
                'success': True,
                'url': self.current_url,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error pressing key: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # Public API methods

    def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL.

        Args:
            url (str): The URL to navigate to.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the navigation.
        """
        self.command_queue.put(("navigate", {"url": url}))
        return self.result_queue.get(timeout=30)

    def click(self, selector: str = None, x: int = None, y: int = None) -> Dict[str, Any]:
        """
        Click on an element or at specific coordinates.

        Args:
            selector (str, optional): The CSS selector of the element to click. Defaults to None.
            x (int, optional): The x-coordinate to click at. Defaults to None.
            y (int, optional): The y-coordinate to click at. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the click.
        """
        self.command_queue.put(("click", {"selector": selector, "x": x, "y": y}))
        return self.result_queue.get(timeout=30)

    def type(self, text: str, selector: str = None) -> Dict[str, Any]:
        """
        Type text into an input field.

        Args:
            text (str): The text to type.
            selector (str, optional): The CSS selector of the input field. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the typing.
        """
        self.command_queue.put(("type", {"text": text, "selector": selector}))
        return self.result_queue.get(timeout=30)

    def scroll(self, direction: str = 'down', distance: int = 300) -> Dict[str, Any]:
        """
        Scroll the page.

        Args:
            direction (str, optional): The direction to scroll ('up', 'down', 'left', 'right'). Defaults to 'down'.
            distance (int, optional): The distance to scroll in pixels. Defaults to 300.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the scrolling.
        """
        self.command_queue.put(("scroll", {"direction": direction, "distance": distance}))
        return self.result_queue.get(timeout=30)

    def get_page_info(self) -> Dict[str, Any]:
        """
        Get information about the current page.

        Returns:
            Dict[str, Any]: A dictionary containing information about the current page.
        """
        self.command_queue.put(("get_info", {}))
        return self.result_queue.get(timeout=30)

    def go_back(self) -> Dict[str, Any]:
        """
        Go back in history.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        self.command_queue.put(("back", {}))
        return self.result_queue.get(timeout=30)

    def go_forward(self) -> Dict[str, Any]:
        """
        Go forward in history.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        self.command_queue.put(("forward", {}))
        return self.result_queue.get(timeout=30)

    def take_screenshot(self, full_page: bool = False) -> Dict[str, Any]:
        """
        Take a screenshot of the current page.

        Args:
            full_page (bool, optional): Whether to take a screenshot of the full page. Defaults to False.

        Returns:
            Dict[str, Any]: A dictionary containing the screenshot.
        """
        self.command_queue.put(("screenshot", {"full_page": full_page}))
        return self.result_queue.get(timeout=30)

    def fill_form(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Fill a form with the provided data.

        Args:
            form_data (Dict[str, str]): A dictionary mapping field selectors to values.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the form filling.
        """
        self.command_queue.put(("fill_form", {"form_data": form_data}))
        return self.result_queue.get(timeout=30)

    def hover(self, selector: str = None, x: int = None, y: int = None) -> Dict[str, Any]:
        """
        Hover over an element or at specific coordinates.

        Args:
            selector (str, optional): The CSS selector of the element to hover over. Defaults to None.
            x (int, optional): The x-coordinate to hover at. Defaults to None.
            y (int, optional): The y-coordinate to hover at. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the hover.
        """
        self.command_queue.put(("hover", {"selector": selector, "x": x, "y": y}))
        return self.result_queue.get(timeout=30)

    def drag_and_drop(self, source_selector: str, target_selector: str) -> Dict[str, Any]:
        """
        Drag an element and drop it on another element.

        Args:
            source_selector (str): The CSS selector of the element to drag.
            target_selector (str): The CSS selector of the element to drop onto.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the drag and drop.
        """
        self.command_queue.put(("drag_and_drop", {"source_selector": source_selector, "target_selector": target_selector}))
        return self.result_queue.get(timeout=30)

    def press_key(self, key: str, selector: str = None) -> Dict[str, Any]:
        """
        Press a key on the keyboard.

        Args:
            key (str): The key to press (e.g., 'Enter', 'Tab', 'Escape').
            selector (str, optional): The CSS selector of the element to focus before pressing the key. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the key press.
        """
        self.command_queue.put(("press_key", {"key": key, "selector": selector}))
        return self.result_queue.get(timeout=30)


# Global browser server instance
browser_server = None

def get_browser_server():
    """
    Get the global browser server instance.

    Returns:
        BrowserServer: The global browser server instance.
    """
    global browser_server

    if browser_server is None:
        browser_server = BrowserServer(headless=False)
        browser_server.start()

    return browser_server
