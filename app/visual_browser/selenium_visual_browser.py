"""
Visual Browser implementation using Selenium.
"""

import os
import time
import base64
import logging
from typing import Dict, Any, List, Optional, Tuple
from io import BytesIO
from urllib.parse import urlparse

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

class SeleniumVisualBrowser:
    """
    A visual browser that uses Selenium to provide visual browsing capabilities.
    """

    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize the visual browser.

        Args:
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to True.
            timeout (int, optional): Default timeout in seconds. Defaults to 30.
        """
        self.headless = headless
        self.timeout = timeout

        # Browser instance
        self.driver = None

        # Session state
        self.current_url = None
        self.session_id = f"visual_browser_{int(time.time())}"

        logger.info(f"Selenium Visual Browser initialized with session ID: {self.session_id}")

    def _apply_stealth_techniques(self):
        """
        Apply advanced stealth techniques to bypass CAPTCHA and avoid detection.
        This copies the stealth features from live_browser.py to Context 7 tools.
        """
        try:
            # Apply user agent override via CDP
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
                "platform": "macOS"
            })
            logger.info("Applied user agent override")
        except Exception as e:
            logger.warning(f"Could not set user agent via CDP: {str(e)}")

        try:
            # Apply comprehensive stealth techniques via JavaScript
            self.driver.execute_script("""
                // Advanced stealth script for Chrome 135+ (copied from live_browser.py)
                (function() {
                    // Helper function to modify navigator properties safely
                    function makeNativeString(name) {
                        return `function ${name}() { [native code] }`;
                    }

                    // 1. Hide webdriver property
                    try {
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => false,
                            configurable: true
                        });
                    } catch (e) { console.log('Failed to modify webdriver property'); }

                    // 2. Override navigator.plugins
                    try {
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5],
                            configurable: true
                        });
                    } catch (e) { console.log('Failed to modify plugins property'); }

                    // 3. Override navigator.languages
                    try {
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en'],
                            configurable: true
                        });
                    } catch (e) { console.log('Failed to modify languages property'); }

                    // 4. Override screen properties
                    try {
                        Object.defineProperty(screen, 'colorDepth', {
                            get: () => 24,
                            configurable: true
                        });
                        Object.defineProperty(screen, 'pixelDepth', {
                            get: () => 24,
                            configurable: true
                        });
                    } catch (e) { console.log('Failed to modify screen properties'); }

                    // 5. Override permissions API
                    try {
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                    } catch (e) { console.log('Failed to modify permissions API'); }

                    // 6. Hide automation indicators
                    try {
                        delete window.chrome.runtime.onConnect;
                        delete window.chrome.runtime.onMessage;
                    } catch (e) { console.log('Failed to hide chrome runtime'); }

                    // 7. Override toString methods
                    try {
                        window.navigator.webdriver = false;
                        Object.defineProperty(window.navigator, 'webdriver', {
                            get: () => false,
                        });
                    } catch (e) { console.log('Failed to override webdriver'); }
                })();
            """)
            logger.info("Applied advanced stealth JavaScript techniques")
        except Exception as e:
            logger.warning(f"Could not apply stealth JavaScript: {str(e)}")

    def start(self) -> Dict[str, Any]:
        """
        Start the browser.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            logger.info("Starting browser...")
            
            # Set up Chrome options
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")

            # Basic Chrome arguments
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1280,800")

            # ADVANCED STEALTH FEATURES (copied from live_browser.py)
            # Add comprehensive stealth arguments to avoid detection and bypass CAPTCHA
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-automation")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            # chrome_options.add_argument("--disable-images")  # Keep images enabled for Context 7 tools
            # chrome_options.add_argument("--disable-javascript")  # Keep JavaScript enabled for Context 7 tools
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-translate")
            chrome_options.add_argument("--hide-scrollbars")
            chrome_options.add_argument("--mute-audio")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")

            # Add experimental options for stealth
            try:
                # Exclude the automation switch
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

                # Disable automation extension
                chrome_options.add_experimental_option("useAutomationExtension", False)

                # Add additional preferences for better stealth
                prefs = {
                    "credentials_enable_service": False,
                    "profile.password_manager_enabled": False,
                    "profile.default_content_setting_values.notifications": 2,
                    "profile.managed_default_content_settings.images": 1,
                    "profile.default_content_setting_values.cookies": 1
                }
                chrome_options.add_experimental_option("prefs", prefs)
            except Exception as e:
                logger.warning(f"Could not add experimental options: {str(e)}")
                # Continue anyway, this is not critical
            
            # Set up Chrome service
            service = Service(ChromeDriverManager().install())
            
            # Create a new Chrome driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set default timeout
            self.driver.set_page_load_timeout(self.timeout)

            # Apply stealth techniques after browser starts
            self._apply_stealth_techniques()

            logger.info("Browser started successfully with stealth features")
            
            return {
                'success': True,
                'message': 'Browser started successfully',
                'session_id': self.session_id
            }
        except Exception as e:
            logger.error(f"Error starting browser: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def stop(self) -> Dict[str, Any]:
        """
        Stop the browser.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            logger.info("Stopping browser...")
            
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            logger.info("Browser stopped successfully")
            
            return {
                'success': True,
                'message': 'Browser stopped successfully'
            }
        except Exception as e:
            logger.error(f"Error stopping browser: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def navigate(self, url: str) -> Dict[str, Any]:
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
            
            # Start a new browser if needed
            if not self.driver:
                self.start()
            
            # Navigate to the URL
            self.driver.get(url)
            
            # Update current URL
            self.current_url = self.driver.current_url
            
            # Get page title
            title = self.driver.title
            
            # Take a screenshot
            screenshot = self.take_screenshot()
            
            logger.info(f"Successfully navigated to {url}")
            
            return {
                'success': True,
                'url': self.current_url,
                'title': title,
                'status': 200,  # Selenium doesn't provide status codes
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    def take_screenshot(self, full_page: bool = False) -> str:
        """
        Take a screenshot of the current page.

        Args:
            full_page (bool, optional): Whether to take a screenshot of the full page. Defaults to False.

        Returns:
            str: The screenshot as a base64-encoded string.
        """
        try:
            logger.info("Taking screenshot...")
            
            if not self.driver:
                return ""
            
            # Take screenshot
            screenshot_bytes = self.driver.get_screenshot_as_png()
            
            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return f"data:image/png;base64,{screenshot_base64}"
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return ""

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
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }
            
            if selector:
                logger.info(f"Clicking on element with selector: {selector}")
                
                # Wait for the element to be clickable
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                # Click the element
                element.click()
            elif x is not None and y is not None:
                logger.info(f"Clicking at coordinates: ({x}, {y})")
                
                # Execute JavaScript to click at the specified coordinates
                self.driver.execute_script(f"document.elementFromPoint({x}, {y}).click();")
            else:
                return {
                    'success': False,
                    'error': 'Either selector or coordinates (x, y) must be provided'
                }
            
            # Update current URL
            self.current_url = self.driver.current_url
            
            # Take a screenshot
            screenshot = self.take_screenshot()
            
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

    def type(self, text: str, selector: str = None) -> Dict[str, Any]:
        """
        Type text into an input field.

        Args:
            text (str): The text to type.
            selector (str, optional): The CSS selector of the input field. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the typing.
        """
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }
            
            if selector:
                logger.info(f"Typing '{text}' into element with selector: {selector}")
                
                # Wait for the element to be visible
                element = WebDriverWait(self.driver, self.timeout).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                
                # Clear the input field
                element.clear()
                
                # Type the text
                element.send_keys(text)
            else:
                logger.info(f"Typing '{text}' at current focus")
                
                # Get the active element
                active_element = self.driver.switch_to.active_element
                
                # Type the text
                active_element.send_keys(text)
            
            # Take a screenshot
            screenshot = self.take_screenshot()
            
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

    def scroll(self, direction: str = 'down', distance: int = 300) -> Dict[str, Any]:
        """
        Scroll the page.

        Args:
            direction (str, optional): The direction to scroll ('up', 'down', 'left', 'right'). Defaults to 'down'.
            distance (int, optional): The distance to scroll in pixels. Defaults to 300.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the scrolling.
        """
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }
            
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
            
            # Execute scroll
            self.driver.execute_script(f"window.scrollBy({x_scroll}, {y_scroll})")
            
            # Wait a moment for the scroll to complete
            time.sleep(0.5)
            
            # Take a screenshot
            screenshot = self.take_screenshot()
            
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

    def get_page_info(self) -> Dict[str, Any]:
        """
        Get information about the current page.

        Returns:
            Dict[str, Any]: A dictionary containing information about the current page.
        """
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }
            
            logger.info("Getting page information...")
            
            # Get page title
            title = self.driver.title
            
            # Get page URL
            url = self.driver.current_url
            
            # Take a screenshot
            screenshot = self.take_screenshot()
            
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

    def login_to_platform(self, platform: str, username: str, password: str) -> Dict[str, Any]:
        """
        Login to a specific platform.

        Args:
            platform (str): The platform to login to ('instagram', 'twitter', etc.).
            username (str): The username.
            password (str): The password.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the login.
        """
        try:
            if not self.driver:
                self.start()
            
            logger.info(f"Logging in to {platform}...")
            
            # Platform-specific login logic
            if platform.lower() == 'instagram':
                # Navigate to Instagram
                self.navigate('https://www.instagram.com/accounts/login/')
                
                # Wait for the login form
                username_input = WebDriverWait(self.driver, self.timeout).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="username"]'))
                )
                
                # Enter username
                username_input.send_keys(username)
                
                # Enter password
                password_input = self.driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
                password_input.send_keys(password)
                
                # Click login button
                login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                login_button.click()
                
                # Wait for navigation to complete
                time.sleep(5)
                
                # Check if login was successful
                try:
                    # Wait for the home feed or profile icon to appear
                    WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'svg[aria-label="Home"]'))
                    )
                    login_success = True
                except:
                    # Check for error messages
                    try:
                        error_message = self.driver.find_element(By.CSS_SELECTOR, 'p[role="alert"]').text
                        return {
                            'success': False,
                            'error': f"Login failed: {error_message}",
                            'screenshot': self.take_screenshot()
                        }
                    except:
                        login_success = False
            
            elif platform.lower() == 'twitter' or platform.lower() == 'x':
                # Navigate to Twitter
                self.navigate('https://twitter.com/i/flow/login')
                
                # Wait for the login form
                username_input = WebDriverWait(self.driver, self.timeout).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
                )
                
                # Enter username
                username_input.send_keys(username)
                
                # Click next button
                next_button = self.driver.find_element(By.XPATH, '//div[@role="button"][.//span[text()="Next"]]')
                next_button.click()
                
                # Wait for password field
                password_input = WebDriverWait(self.driver, self.timeout).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
                )
                
                # Enter password
                password_input.send_keys(password)
                
                # Click login button
                login_button = self.driver.find_element(By.XPATH, '//div[@role="button"][.//span[text()="Log in"]]')
                login_button.click()
                
                # Wait for navigation to complete
                time.sleep(5)
                
                # Check if login was successful
                try:
                    # Wait for the home timeline to appear
                    WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-testid="primaryColumn"]'))
                    )
                    login_success = True
                except:
                    login_success = False
            
            else:
                return {
                    'success': False,
                    'error': f"Login for platform '{platform}' is not implemented"
                }
            
            # Take a screenshot
            screenshot = self.take_screenshot()
            
            return {
                'success': login_success,
                'platform': platform,
                'username': username,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error logging in to {platform}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': platform
            }
