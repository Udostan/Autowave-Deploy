"""
Browser automation for the Visual Browser with LLM integration.
"""

import os
import time
import base64
import logging
import traceback
import json
from typing import Dict, Any, List, Optional, Tuple

# Import LLM clients
try:
    from app.llm.gemini_client import GeminiClient
    from app.llm.groq_client import GroqClient
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: LLM clients not available. Some features will be disabled.")

# Import Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrowserAutomation:
    """
    Browser automation for the Visual Browser with LLM integration.
    """

    def __init__(self, headless: bool = True, timeout: int = 30, use_llm: bool = True):
        """
        Initialize the browser automation.

        Args:
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to True.
            timeout (int, optional): Default timeout in seconds. Defaults to 30.
            use_llm (bool, optional): Whether to use LLM for intelligent browsing. Defaults to True.
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.session_id = f"visual_browser_{int(time.time())}"
        self.current_url = None
        self.history = []
        self.history_index = -1
        self.use_llm = use_llm

        # Initialize LLM clients
        if self.use_llm and LLM_AVAILABLE:
            try:
                self.gemini_client = GeminiClient()
                self.groq_client = GroqClient()
                self.llm_available = True
            except Exception as e:
                logger.error(f"Error initializing LLM clients: {str(e)}")
                self.llm_available = False
        else:
            self.llm_available = False
            if self.use_llm:
                logger.warning("LLM clients not available. Some features will be disabled.")

        logger.info(f"Browser automation initialized with session ID: {self.session_id}, LLM: {self.llm_available}")

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

            logger.info("Browser started successfully")

            return {
                'success': True,
                'message': 'Browser started successfully',
                'session_id': self.session_id
            }
        except Exception as e:
            logger.error(f"Error starting browser: {str(e)}")
            logger.error(traceback.format_exc())
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
            logger.error(traceback.format_exc())
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
                result = self.start()
                if not result['success']:
                    return result

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
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

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
            logger.error(traceback.format_exc())
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
            logger.error(traceback.format_exc())
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
            logger.error(traceback.format_exc())
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
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }

    def go_back(self) -> Dict[str, Any]:
        """
        Go back in history.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }

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
            return self.navigate(url)
        except Exception as e:
            logger.error(f"Error going back: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }

    def go_forward(self) -> Dict[str, Any]:
        """
        Go forward in history.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }

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
            return self.navigate(url)
        except Exception as e:
            logger.error(f"Error going forward: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }

    def take_screenshot(self, full_page: bool = False) -> Dict[str, Any]:
        """
        Take a screenshot of the current page.

        Args:
            full_page (bool, optional): Whether to take a screenshot of the full page. Defaults to False.

        Returns:
            Dict[str, Any]: A dictionary containing the screenshot.
        """
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }

            # Take a screenshot
            screenshot = self._take_screenshot(full_page)

            return {
                'success': True,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            logger.error(traceback.format_exc())
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
            if not self.driver:
                return ""

            # Take screenshot
            screenshot_bytes = self.driver.get_screenshot_as_png()

            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            return f"data:image/png;base64,{screenshot_base64}"
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            logger.error(traceback.format_exc())
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

    def analyze_page(self) -> Dict[str, Any]:
        """
        Analyze the current page using LLM.

        Returns:
            Dict[str, Any]: A dictionary containing the analysis results.
        """
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }

            if not self.llm_available:
                return {
                    'success': False,
                    'error': 'LLM not available'
                }

            logger.info("Analyzing page content...")

            # Get page content
            title = self.driver.title
            url = self.driver.current_url

            # Get page text content
            page_text = self.driver.execute_script('''
                return document.body.innerText;
            ''')

            # Get all links on the page
            links = self.driver.execute_script('''
                return Array.from(document.querySelectorAll('a')).map(link => ({
                    text: link.textContent.trim(),
                    href: link.href
                }));
            ''')

            # Get all form fields on the page
            forms = self.driver.execute_script('''
                return Array.from(document.querySelectorAll('form')).map(form => ({
                    id: form.id,
                    action: form.action,
                    method: form.method,
                    fields: Array.from(form.querySelectorAll('input, textarea, select')).map(field => ({
                        type: field.type || field.tagName.toLowerCase(),
                        name: field.name,
                        id: field.id,
                        placeholder: field.placeholder
                    }))
                }));
            ''')

            # Prepare prompt for LLM
            prompt = f"""
            Analyze the following webpage content:

            URL: {url}
            Title: {title}

            Page Content (excerpt):
            {page_text[:5000]}...

            Links: {json.dumps(links[:20])}

            Forms: {json.dumps(forms)}

            Please provide:
            1. A brief summary of what this page is about
            2. Key information found on the page
            3. Possible actions that can be taken on this page (e.g., clicking links, filling forms)
            4. Recommendations for what to do next

            Format your response as JSON with the following structure:
            {{
                "summary": "Brief summary of the page",
                "key_information": ["Point 1", "Point 2", ...],
                "possible_actions": ["Action 1", "Action 2", ...],
                "recommendations": ["Recommendation 1", "Recommendation 2", ...]
            }}
            """

            # Call LLM
            try:
                # Try Gemini first
                response = self.gemini_client.generate_content(prompt)
                analysis = json.loads(response)
            except Exception as e:
                logger.error(f"Error using Gemini: {str(e)}")
                try:
                    # Fall back to Groq
                    response = self.groq_client.generate_content(prompt)
                    analysis = json.loads(response)
                except Exception as e:
                    logger.error(f"Error using Groq: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error analyzing page: {str(e)}"
                    }

            # Take a screenshot
            screenshot = self._take_screenshot()

            return {
                'success': True,
                'url': url,
                'title': title,
                'analysis': analysis,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Error analyzing page: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }

    def login_to_platform(self, platform: str, username: str, password: str) -> Dict[str, Any]:
        """
        Login to a specific platform.

        Args:
            platform (str): The platform to login to ('instagram', 'twitter', etc.)
            username (str): The username
            password (str): The password

        Returns:
            Dict[str, Any]: A dictionary containing the result of the login
        """
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }

            logger.info(f"Logging in to {platform}...")

            # Platform-specific login logic
            if platform.lower() == 'instagram':
                # Navigate to Instagram
                self.driver.get('https://www.instagram.com/accounts/login/')

                # Wait for the login form
                username_input = WebDriverWait(self.driver, 10).until(
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
                            'screenshot': self._take_screenshot()
                        }
                    except:
                        login_success = False

            elif platform.lower() == 'twitter' or platform.lower() == 'x':
                # Navigate to Twitter
                self.driver.get('https://twitter.com/i/flow/login')

                # Wait for the login form
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
                )

                # Enter username
                username_input.send_keys(username)

                # Click next button
                next_button = self.driver.find_element(By.XPATH, '//div[@role="button"][.//span[text()="Next"]]')
                next_button.click()

                # Wait for password field
                password_input = WebDriverWait(self.driver, 10).until(
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
            screenshot = self._take_screenshot()

            # Update current URL
            self.current_url = self.driver.current_url

            # Add to history
            self._add_to_history(self.current_url)

            return {
                'success': login_success,
                'platform': platform,
                'username': username,
                'screenshot': screenshot,
                'url': self.current_url
            }
        except Exception as e:
            logger.error(f"Error logging in to {platform}: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'platform': platform
            }

    def execute_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Execute a natural language instruction using LLM.

        Args:
            instruction (str): The natural language instruction to execute.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the execution.
        """
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'Browser not started'
                }

            if not self.llm_available:
                return {
                    'success': False,
                    'error': 'LLM not available'
                }

            logger.info(f"Executing instruction: {instruction}")

            # Get page information
            page_info = self.get_page_info()
            if not page_info['success']:
                return page_info

            # Prepare prompt for LLM
            prompt = f"""
            You are an AI assistant that helps users browse the web. You have been given the following instruction:

            Instruction: {instruction}

            Current webpage:
            URL: {page_info['url']}
            Title: {page_info['title']}

            Available elements on the page:
            Links: {json.dumps(page_info['links'][:20])}
            Buttons: {json.dumps(page_info['buttons'][:20])}
            Inputs: {json.dumps(page_info['inputs'][:20])}

            Based on the instruction and the current webpage, determine the best action to take.
            Choose ONE of the following actions:
            1. navigate(url): Navigate to a new URL
            2. click(selector): Click on an element with the given CSS selector
            3. type(text, selector): Type text into an input field with the given CSS selector
            4. scroll(direction, distance): Scroll the page in the given direction

            Format your response as JSON with the following structure:
            {{
                "action": "action_name",
                "parameters": {{
                    "param1": "value1",
                    "param2": "value2"
                }},
                "reasoning": "Explanation of why this action was chosen"
            }}
            """

            # Call LLM
            try:
                # Try Gemini first
                response = self.gemini_client.generate_content(prompt)
                action_plan = json.loads(response)
            except Exception as e:
                logger.error(f"Error using Gemini: {str(e)}")
                try:
                    # Fall back to Groq
                    response = self.groq_client.generate_content(prompt)
                    action_plan = json.loads(response)
                except Exception as e:
                    logger.error(f"Error using Groq: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error executing instruction: {str(e)}"
                    }

            # Execute the action
            action = action_plan.get('action')
            parameters = action_plan.get('parameters', {})

            result = None

            if action == 'navigate':
                url = parameters.get('url')
                if url:
                    result = self.navigate(url)
                else:
                    return {
                        'success': False,
                        'error': 'URL is required for navigate action'
                    }
            elif action == 'click':
                selector = parameters.get('selector')
                if selector:
                    result = self.click(selector=selector)
                else:
                    return {
                        'success': False,
                        'error': 'Selector is required for click action'
                    }
            elif action == 'type':
                text = parameters.get('text')
                selector = parameters.get('selector')
                if text and selector:
                    result = self.type(text, selector)
                else:
                    return {
                        'success': False,
                        'error': 'Text and selector are required for type action'
                    }
            elif action == 'scroll':
                direction = parameters.get('direction', 'down')
                distance = parameters.get('distance', 300)
                result = self.scroll(direction, distance)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }

            if result and result['success']:
                # Add reasoning to the result
                result['reasoning'] = action_plan.get('reasoning')
                return result
            else:
                return result or {
                    'success': False,
                    'error': f'Error executing action: {action}'
                }
        except Exception as e:
            logger.error(f"Error executing instruction: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
