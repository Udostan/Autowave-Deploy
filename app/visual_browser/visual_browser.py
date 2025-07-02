"""
Visual Browser implementation using Pyppeteer.
"""

import os
import asyncio
import base64
from typing import Dict, Any, List, Optional, Tuple
import json
import logging
import time
from urllib.parse import urlparse

# Optional pyppeteer import
try:
    import pyppeteer
    from pyppeteer import launch
    from pyppeteer.browser import Browser
    from pyppeteer.page import Page
    PYPPETEER_AVAILABLE = True
except ImportError:
    PYPPETEER_AVAILABLE = False
    pyppeteer = None
    launch = None
    Browser = None
    Page = None

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisualBrowser:
    """
    A visual browser that uses Pyppeteer to provide visual browsing capabilities.
    """

    def __init__(self, headless: bool = True, viewport: Dict[str, int] = None,
                 user_agent: str = None, timeout: int = 30000):
        """
        Initialize the visual browser.

        Args:
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to True.
            viewport (Dict[str, int], optional): The viewport dimensions. Defaults to 1280x800.
            user_agent (str, optional): The user agent string. Defaults to Chrome on macOS.
            timeout (int, optional): Default timeout in milliseconds. Defaults to 30000.
        """
        if not PYPPETEER_AVAILABLE:
            logger.warning("Pyppeteer not available. Visual browser functionality will be disabled.")
            self.available = False
            return

        self.available = True
        self.headless = headless
        self.viewport = viewport or {'width': 1280, 'height': 800}
        self.user_agent = user_agent or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        self.timeout = timeout

        # Browser and page instances
        self.browser = None
        self.page = None

        # Session state
        self.current_url = None
        self.cookies = []
        self.session_id = None

        # Create a session ID
        self.session_id = f"visual_browser_{int(time.time())}"

        logger.info(f"Visual Browser initialized with session ID: {self.session_id}")

    async def start(self) -> None:
        """
        Start the browser.

        Returns:
            None
        """
        if self.browser is not None:
            logger.info("Browser already started")
            return

        try:
            logger.info("Starting browser...")
            self.browser = await launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
                handleSIGINT=False,  # Disable signal handling to avoid issues in Flask
                handleSIGTERM=False,
                handleSIGHUP=False
            )
            self.page = await self.browser.newPage()

            # Set viewport and user agent
            await self.page.setViewport(self.viewport)
            await self.page.setUserAgent(self.user_agent)

            # Set default timeout
            self.page.setDefaultNavigationTimeout(self.timeout)

            logger.info("Browser started successfully")
        except Exception as e:
            logger.error(f"Error starting browser: {str(e)}")
            raise

    async def stop(self) -> None:
        """
        Stop the browser.

        Returns:
            None
        """
        if self.browser is None:
            logger.info("Browser not started")
            return

        try:
            logger.info("Stopping browser...")
            await self.browser.close()
            self.browser = None
            self.page = None
            logger.info("Browser stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping browser: {str(e)}")
            raise

    async def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL.

        Args:
            url (str): The URL to navigate to.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the navigation.
        """
        # Always start a new browser instance for navigation
        if self.browser is not None:
            try:
                await self.browser.close()
            except:
                pass

        self.browser = None
        self.page = None
        await self.start()

        try:
            # Ensure URL has proper format
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url

            logger.info(f"Navigating to {url}...")

            # Navigate to the URL
            response = await self.page.goto(url, {
                'waitUntil': 'networkidle0',
                'timeout': self.timeout
            })

            # Update current URL
            self.current_url = self.page.url

            # Get page title
            title = await self.page.title()

            # Take a screenshot
            screenshot = await self.take_screenshot()

            # Get cookies
            self.cookies = await self.page.cookies()

            logger.info(f"Successfully navigated to {url}")

            return {
                'success': True,
                'url': self.current_url,
                'title': title,
                'status': response.status,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    async def take_screenshot(self, full_page: bool = False) -> str:
        """
        Take a screenshot of the current page.

        Args:
            full_page (bool, optional): Whether to take a screenshot of the full page. Defaults to False.

        Returns:
            str: The screenshot as a base64-encoded string.
        """
        if self.browser is None or self.page is None:
            await self.start()

        try:
            logger.info("Taking screenshot...")
            screenshot_bytes = await self.page.screenshot({
                'fullPage': full_page,
                'type': 'jpeg',
                'quality': 80
            })

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            return f"data:image/jpeg;base64,{screenshot_base64}"
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return ""

    async def click(self, selector: str = None, x: int = None, y: int = None) -> Dict[str, Any]:
        """
        Click on an element or at specific coordinates.

        Args:
            selector (str, optional): The CSS selector of the element to click. Defaults to None.
            x (int, optional): The x-coordinate to click at. Defaults to None.
            y (int, optional): The y-coordinate to click at. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the click.
        """
        if self.browser is None or self.page is None:
            await self.start()

        try:
            if selector:
                logger.info(f"Clicking on element with selector: {selector}")
                # Wait for the element to be visible
                await self.page.waitForSelector(selector, {'visible': True, 'timeout': self.timeout})
                # Click the element
                await self.page.click(selector)
            elif x is not None and y is not None:
                logger.info(f"Clicking at coordinates: ({x}, {y})")
                # Click at the specified coordinates
                await self.page.mouse.click(x, y)
            else:
                return {
                    'success': False,
                    'error': 'Either selector or coordinates (x, y) must be provided'
                }

            # Wait for any navigation to complete
            await self.page.waitForNavigation({'waitUntil': 'networkidle0', 'timeout': self.timeout})

            # Update current URL
            self.current_url = self.page.url

            # Take a screenshot
            screenshot = await self.take_screenshot()

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

    async def type(self, text: str, selector: str = None) -> Dict[str, Any]:
        """
        Type text into an input field.

        Args:
            text (str): The text to type.
            selector (str, optional): The CSS selector of the input field. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the typing.
        """
        if self.browser is None or self.page is None:
            await self.start()

        try:
            if selector:
                logger.info(f"Typing '{text}' into element with selector: {selector}")
                # Wait for the element to be visible
                await self.page.waitForSelector(selector, {'visible': True, 'timeout': self.timeout})
                # Clear the input field
                await self.page.evaluate(f'document.querySelector("{selector}").value = ""')
                # Type the text
                await self.page.type(selector, text)
            else:
                logger.info(f"Typing '{text}' at current focus")
                # Type at the current focus
                await self.page.keyboard.type(text)

            # Take a screenshot
            screenshot = await self.take_screenshot()

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

    async def scroll(self, direction: str = 'down', distance: int = 300) -> Dict[str, Any]:
        """
        Scroll the page.

        Args:
            direction (str, optional): The direction to scroll ('up', 'down', 'left', 'right'). Defaults to 'down'.
            distance (int, optional): The distance to scroll in pixels. Defaults to 300.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the scrolling.
        """
        if self.browser is None or self.page is None:
            await self.start()

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

            # Execute scroll
            await self.page.evaluate(f'window.scrollBy({x_scroll}, {y_scroll})')

            # Wait a moment for the scroll to complete
            await asyncio.sleep(0.5)

            # Take a screenshot
            screenshot = await self.take_screenshot()

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

    async def get_elements(self, selector: str) -> Dict[str, Any]:
        """
        Get elements matching a selector.

        Args:
            selector (str): The CSS selector to match elements.

        Returns:
            Dict[str, Any]: A dictionary containing the matched elements.
        """
        if self.browser is None or self.page is None:
            await self.start()

        try:
            logger.info(f"Getting elements with selector: {selector}")

            # Get elements matching the selector
            elements = await self.page.querySelectorAll(selector)

            # Extract information about each element
            element_info = []
            for i, element in enumerate(elements):
                # Get element properties
                tag_name = await self.page.evaluate('el => el.tagName.toLowerCase()', element)
                text = await self.page.evaluate('el => el.textContent', element)

                # Get element bounding box
                box = await element.boundingBox()

                # Get element attributes
                attrs = await self.page.evaluate('''
                    el => {
                        const attrs = {};
                        for (const attr of el.attributes) {
                            attrs[attr.name] = attr.value;
                        }
                        return attrs;
                    }
                ''', element)

                element_info.append({
                    'index': i,
                    'tag': tag_name,
                    'text': text.strip() if text else '',
                    'attributes': attrs,
                    'position': box
                })

            return {
                'success': True,
                'elements': element_info,
                'count': len(element_info)
            }
        except Exception as e:
            logger.error(f"Error getting elements: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def execute_script(self, script: str) -> Dict[str, Any]:
        """
        Execute JavaScript on the page.

        Args:
            script (str): The JavaScript to execute.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the script execution.
        """
        if self.browser is None or self.page is None:
            await self.start()

        try:
            logger.info(f"Executing script: {script[:50]}...")

            # Execute the script
            result = await self.page.evaluate(script)

            # Take a screenshot
            screenshot = await self.take_screenshot()

            return {
                'success': True,
                'result': result,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def login_to_platform(self, platform: str, username: str, password: str) -> Dict[str, Any]:
        """
        Login to a specific platform.

        Args:
            platform (str): The platform to login to ('instagram', 'twitter', etc.).
            username (str): The username.
            password (str): The password.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the login.
        """
        if self.browser is None or self.page is None:
            await self.start()

        try:
            logger.info(f"Logging in to {platform}...")

            # Platform-specific login logic
            if platform.lower() == 'instagram':
                # Navigate to Instagram
                await self.navigate('https://www.instagram.com/accounts/login/')

                # Wait for the login form
                await self.page.waitForSelector('input[name="username"]', {'visible': True, 'timeout': self.timeout})

                # Enter username
                await self.page.type('input[name="username"]', username)

                # Enter password
                await self.page.type('input[name="password"]', password)

                # Click login button
                await self.page.click('button[type="submit"]')

                # Wait for navigation to complete
                try:
                    await self.page.waitForNavigation({'waitUntil': 'networkidle0', 'timeout': self.timeout})
                except:
                    # Instagram might not navigate after login, so we'll check for success another way
                    pass

                # Check if login was successful
                try:
                    # Wait for the home feed or profile icon to appear
                    await self.page.waitForSelector('svg[aria-label="Home"]', {'visible': True, 'timeout': 5000})
                    login_success = True
                except:
                    # Check for error messages
                    error_message = await self.page.evaluate('''
                        () => {
                            const errorEl = document.querySelector('p[role="alert"]');
                            return errorEl ? errorEl.textContent : null;
                        }
                    ''')

                    if error_message:
                        return {
                            'success': False,
                            'error': f"Login failed: {error_message}",
                            'screenshot': await self.take_screenshot()
                        }

                    login_success = False

            elif platform.lower() == 'twitter' or platform.lower() == 'x':
                # Navigate to Twitter
                await self.navigate('https://twitter.com/i/flow/login')

                # Wait for the login form
                await self.page.waitForSelector('input[autocomplete="username"]', {'visible': True, 'timeout': self.timeout})

                # Enter username
                await self.page.type('input[autocomplete="username"]', username)

                # Click next button
                await self.page.click('div[role="button"]:has-text("Next")')

                # Wait for password field
                await self.page.waitForSelector('input[name="password"]', {'visible': True, 'timeout': self.timeout})

                # Enter password
                await self.page.type('input[name="password"]', password)

                # Click login button
                await self.page.click('div[role="button"]:has-text("Log in")')

                # Wait for navigation to complete
                await self.page.waitForNavigation({'waitUntil': 'networkidle0', 'timeout': self.timeout})

                # Check if login was successful
                try:
                    # Wait for the home timeline to appear
                    await self.page.waitForSelector('div[data-testid="primaryColumn"]', {'visible': True, 'timeout': 5000})
                    login_success = True
                except:
                    login_success = False

            else:
                return {
                    'success': False,
                    'error': f"Login for platform '{platform}' is not implemented"
                }

            # Take a screenshot
            screenshot = await self.take_screenshot()

            # Save cookies
            self.cookies = await self.page.cookies()

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

    async def get_page_info(self) -> Dict[str, Any]:
        """
        Get information about the current page.

        Returns:
            Dict[str, Any]: A dictionary containing information about the current page.
        """
        if self.browser is None or self.page is None:
            await self.start()

        try:
            logger.info("Getting page information...")

            # Get page title
            title = await self.page.title()

            # Get page URL
            url = self.page.url

            # Get page content
            content = await self.page.content()

            # Take a screenshot
            screenshot = await self.take_screenshot()

            # Get all links on the page
            links = await self.page.evaluate('''
                () => {
                    const links = Array.from(document.querySelectorAll('a'));
                    return links.map(link => ({
                        text: link.textContent.trim(),
                        href: link.href,
                        visible: link.offsetParent !== null
                    }));
                }
            ''')

            # Get all images on the page
            images = await self.page.evaluate('''
                () => {
                    const images = Array.from(document.querySelectorAll('img'));
                    return images.map(img => ({
                        src: img.src,
                        alt: img.alt,
                        width: img.width,
                        height: img.height,
                        visible: img.offsetParent !== null
                    }));
                }
            ''')

            # Get all input fields on the page
            inputs = await self.page.evaluate('''
                () => {
                    const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
                    return inputs.map(input => ({
                        type: input.type || input.tagName.toLowerCase(),
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder,
                        value: input.value,
                        visible: input.offsetParent !== null
                    }));
                }
            ''')

            # Get all buttons on the page
            buttons = await self.page.evaluate('''
                () => {
                    const buttons = Array.from(document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]'));
                    return buttons.map(button => ({
                        text: button.textContent.trim() || button.value,
                        type: button.type,
                        visible: button.offsetParent !== null
                    }));
                }
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

# Synchronous wrapper functions for the async methods
def sync_navigate(browser, url):
    """Synchronous wrapper for navigate method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(browser.navigate(url))
        return result
    finally:
        loop.close()

def sync_click(browser, selector=None, x=None, y=None):
    """Synchronous wrapper for click method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(browser.click(selector, x, y))
        return result
    finally:
        loop.close()

def sync_type(browser, text, selector=None):
    """Synchronous wrapper for type method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(browser.type(text, selector))
        return result
    finally:
        loop.close()

def sync_scroll(browser, direction='down', distance=300):
    """Synchronous wrapper for scroll method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(browser.scroll(direction, distance))
        return result
    finally:
        loop.close()

def sync_get_elements(browser, selector):
    """Synchronous wrapper for get_elements method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(browser.get_elements(selector))
        return result
    finally:
        loop.close()

def sync_execute_script(browser, script):
    """Synchronous wrapper for execute_script method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(browser.execute_script(script))
        return result
    finally:
        loop.close()

def sync_login_to_platform(browser, platform, username, password):
    """Synchronous wrapper for login_to_platform method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(browser.login_to_platform(platform, username, password))
        return result
    finally:
        loop.close()

def sync_get_page_info(browser):
    """Synchronous wrapper for get_page_info method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(browser.get_page_info())
        return result
    finally:
        loop.close()

def sync_start(browser):
    """Synchronous wrapper for start method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(browser.start())
    finally:
        loop.close()

def sync_stop(browser):
    """Synchronous wrapper for stop method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(browser.stop())
    finally:
        loop.close()

def sync_take_screenshot(browser, full_page=False):
    """Synchronous wrapper for take_screenshot method."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(browser.take_screenshot(full_page))
        return result
    finally:
        loop.close()
