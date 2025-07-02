"""
Lightweight web browser utility for Agen911.
This module provides a simple web browser that can fetch and parse web pages.
"""

import os
import time
import hashlib
import json
import requests
import random
import base64
import re
import concurrent.futures
from typing import Dict, Any, Optional, List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus

# Try to import selenium for advanced browsing
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Try to import playwright for advanced browsing
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class WebBrowser:
    """
    A lightweight web browser that can fetch and parse web pages.
    """

    def __init__(self, cache_dir='./cache', cache_expiry=86400, use_advanced_browser=False, max_cache_size=500, browser_type='auto'):
        """
        Initialize the web browser.

        Args:
            cache_dir (str, optional): Directory to store cache files. Defaults to None.
            cache_expiry (int, optional): Cache expiry time in seconds. Defaults to 3600 (1 hour).
            use_advanced_browser (bool, optional): Whether to use advanced browser capabilities. Defaults to False.
            max_cache_size (int, optional): Maximum number of items to keep in memory cache. Defaults to 100.
            browser_type (str, optional): Type of browser to use. Can be 'auto', 'playwright', or 'selenium'. Defaults to 'auto'.
        """
        # Initialize session
        self.session = requests.Session()

        # Configure user agent for better compatibility
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        self.session.headers.update({'User-Agent': user_agent})

        # State tracking
        self.current_url = None
        self.current_page_content = None
        self.current_soup = None

        # Advanced browser settings
        self.use_advanced_browser = use_advanced_browser
        self.browser_type = browser_type.lower() if browser_type else 'auto'
        self.selenium_driver = None
        self.playwright = None
        self.playwright_browser = None
        self.playwright_context = None
        self.playwright_page = None
        self.screenshot_data = None

        # Validate browser_type
        if self.browser_type not in ['auto', 'playwright', 'selenium']:
            print(f"WARNING: Invalid browser_type '{browser_type}'. Using 'auto' instead.")
            self.browser_type = 'auto'

        # Initialize advanced browser if requested and available
        if self.use_advanced_browser:
            self._init_advanced_browser()

        # Initialize cache with LRU tracking
        self.cache = {}
        self.cache_dir = cache_dir
        self.cache_enabled = cache_dir is not None
        self.cache_expiry = cache_expiry
        self.max_cache_size = max_cache_size
        self.cache_access_times = {}  # Track when each cache item was last accessed
        self.cache_hits = 0
        self.cache_misses = 0

        # Create cache directory if it doesn't exist
        if self.cache_enabled and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _init_advanced_browser(self):
        """
        Initialize advanced browser capabilities if available.
        """
        # Initialize based on browser_type preference
        if self.browser_type == 'playwright' or self.browser_type == 'auto':
            # Try to initialize Playwright if it's explicitly requested or auto mode
            if PLAYWRIGHT_AVAILABLE:
                try:
                    self.playwright = sync_playwright().start()
                    self.playwright_browser = self.playwright.chromium.launch(
                        headless=True,  # Run headless for server environments
                    )
                    self.playwright_context = self.playwright_browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                    )
                    self.playwright_page = self.playwright_context.new_page()
                    print("Initialized Playwright browser")
                    return
                except Exception as e:
                    print(f"Failed to initialize Playwright: {str(e)}")
                    # Close any open resources
                    if self.playwright_page:
                        self.playwright_page.close()
                    if self.playwright_context:
                        self.playwright_context.close()
                    if self.playwright_browser:
                        self.playwright_browser.close()
                    if self.playwright:
                        self.playwright.stop()

                    # Reset variables
                    self.playwright = None
                    self.playwright_browser = None
                    self.playwright_context = None
                    self.playwright_page = None

                    # If browser_type is explicitly set to playwright and it failed, don't try selenium
                    if self.browser_type == 'playwright':
                        print("Playwright was explicitly requested but failed to initialize.")
                        self.use_advanced_browser = False
                        return
            elif self.browser_type == 'playwright':
                # Playwright was explicitly requested but not available
                print("Playwright was explicitly requested but is not available. Install it with 'pip install playwright'.")
                self.use_advanced_browser = False
                return

        # Try Selenium if it's explicitly requested or if we're in auto mode and Playwright failed
        if self.browser_type == 'selenium' or (self.browser_type == 'auto' and not self.playwright_page):
            if SELENIUM_AVAILABLE:
                try:
                    options = Options()
                    options.add_argument('--headless')
                    options.add_argument('--disable-gpu')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--disable-extensions')
                    options.add_argument('--window-size=1280,800')
                    options.add_argument(f'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')

                    self.selenium_driver = webdriver.Chrome(options=options)
                    print("Initialized Selenium browser")
                    return
                except Exception as e:
                    print(f"Failed to initialize Selenium: {str(e)}")
                    if self.selenium_driver:
                        self.selenium_driver.quit()
                    self.selenium_driver = None

                    # If browser_type is explicitly set to selenium and it failed, don't fall back
                    if self.browser_type == 'selenium':
                        print("Selenium was explicitly requested but failed to initialize.")
                        self.use_advanced_browser = False
                        return
            elif self.browser_type == 'selenium':
                # Selenium was explicitly requested but not available
                print("Selenium was explicitly requested but is not available. Install it with 'pip install selenium'.")
                self.use_advanced_browser = False
                return

        # If we get here, neither Playwright nor Selenium could be initialized
        print("Advanced browser capabilities are not available. Using requests-based browsing.")
        self.use_advanced_browser = False

    def _cleanup_advanced_browser(self):
        """
        Clean up advanced browser resources.
        """
        if self.playwright_page:
            try:
                self.playwright_page.close()
            except:
                pass

        if self.playwright_context:
            try:
                self.playwright_context.close()
            except:
                pass

        if self.playwright_browser:
            try:
                self.playwright_browser.close()
            except:
                pass

        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass

        if self.selenium_driver:
            try:
                self.selenium_driver.quit()
            except:
                pass

        # Reset variables
        self.playwright = None
        self.playwright_browser = None
        self.playwright_context = None
        self.playwright_page = None
        self.selenium_driver = None

    def __del__(self):
        """
        Clean up resources when the object is deleted.
        """
        self._cleanup_advanced_browser()

    def browse(self, url, timeout=10, headers=None, cookies=None, use_cache=True):
        """
        Browse to a URL and return the page content.

        Args:
            url (str): The URL to browse to.
            timeout (int, optional): Request timeout in seconds. Defaults to 30.
            headers (dict, optional): Additional headers to send. Defaults to None.
            cookies (dict, optional): Cookies to send. Defaults to None.
            use_cache (bool, optional): Whether to use the cache. Defaults to True.

        Returns:
            dict: A dictionary containing the page title, content, and URL.
        """
        try:
            print(f"DEBUG: WebBrowser.browse() called with URL: {url}")

            # Ensure URL has proper format (this is a backup check in case SuperAgent didn't fix it)
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
                print(f"DEBUG: Added https:// prefix to URL: {url}")
            # Fix double https:// issue
            elif url.startswith('https://https://') or url.startswith('http://http://'):
                url = url.replace('https://https://', 'https://')
                url = url.replace('http://http://', 'http://')
                print(f"DEBUG: Fixed double protocol in URL: {url}")

            # Check cache first if enabled
            cache_key = self._get_cache_key(url)
            cached_data = None
            if use_cache:
                cached_data = self._get_from_cache(cache_key)

            if cached_data:
                # Update current state from cache
                self.current_url = url
                self.current_page_content = cached_data.get("content", "")
                self.current_soup = BeautifulSoup(cached_data.get("html", ""), 'html.parser')
                self.screenshot_data = cached_data.get("screenshot")

                print(f"DEBUG: Using cached data for {url}")
                return cached_data

            # Use advanced browser if available
            if self.use_advanced_browser:
                advanced_result = self._browse_with_advanced_browser(url, timeout)
                if advanced_result:
                    return advanced_result

            print(f"DEBUG: Sending HTTP request to {url}")

            # Prepare headers
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)

            # Send request
            try:
                response = self.session.get(url, timeout=timeout, headers=request_headers, cookies=cookies)
                response.raise_for_status()
                print(f"DEBUG: HTTP request successful, status code: {response.status_code}")
            except Exception as request_error:
                print(f"DEBUG: HTTP request failed: {str(request_error)}")
                raise request_error

            # Parse with BeautifulSoup
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                print(f"DEBUG: BeautifulSoup parsing successful")
            except Exception as soup_error:
                print(f"DEBUG: BeautifulSoup parsing failed: {str(soup_error)}")
                raise soup_error

            # Extract title
            title = soup.title.string if soup.title else "No title"
            print(f"DEBUG: Page title: {title}")

            # Remove script and style elements for text content
            for script in soup(["script", "style"]):
                script.extract()

            # Get text content
            text_content = soup.get_text(separator=' ', strip=True)
            print(f"DEBUG: Extracted text content length: {len(text_content)}")

            # Store current state
            self.current_url = url
            self.current_page_content = text_content
            self.current_soup = soup

            # Extract images
            images = []
            try:
                # Find all img tags with src attribute
                img_tags = soup.find_all('img', src=True)

                # Filter out small icons, spacers, etc.
                for img in img_tags:
                    src = img.get('src')
                    # Convert relative URLs to absolute
                    if src and not src.startswith(('http://', 'https://', 'data:')):
                        src = urljoin(url, src)

                    # Skip data URLs and very small images
                    if src and not src.startswith('data:'):
                        # Get alt text and dimensions if available
                        alt = img.get('alt', '')
                        width = img.get('width', 0)
                        height = img.get('height', 0)

                        # Try to determine if this is a substantial image
                        # Skip very small images that are likely icons
                        if (width and height and int(width) > 100 and int(height) > 100) or \
                           (not width and not height and ('jpg' in src.lower() or 'jpeg' in src.lower() or 'png' in src.lower())):
                            images.append({
                                "src": src,
                                "alt": alt,
                                "width": width,
                                "height": height
                            })

                            # Limit to 15 images to avoid overloading
                            if len(images) >= 15:
                                break
            except Exception as img_error:
                print(f"DEBUG: Error extracting images: {str(img_error)}")

            # Prepare result
            result = {
                "title": title,
                "content": text_content[:5000] + ("..." if len(text_content) > 5000 else ""),
                "url": url,
                "html": response.text,
                "images": images,
                "success": True
            }

            # Save to cache
            self._save_to_cache(cache_key, result)
            print(f"DEBUG: Successfully browsed to {url}")

            return result

        except Exception as e:
            print(f"DEBUG: Error in WebBrowser.browse(): {str(e)}")
            print(f"DEBUG: Error type: {type(e).__name__}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return {
                "error": f"Error browsing to {url}: {str(e)}",
                "success": False
            }

    def navigate_to_url(self, url, timeout=30):
        """
        Navigate to a URL using the advanced browser.

        Args:
            url (str): The URL to navigate to
            timeout (int, optional): Timeout in seconds. Defaults to 30.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure URL has proper format
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url

            # Use advanced browser if available
            if self.use_advanced_browser:
                if self.playwright_page:
                    self.playwright_page.goto(url, timeout=timeout * 1000)  # Playwright uses milliseconds
                    return True
                elif self.selenium_driver:
                    self.selenium_driver.get(url)
                    return True

            # Fallback to regular browsing
            result = self.browse(url, timeout=timeout)
            return result.get('success', False)
        except Exception as e:
            print(f"Error navigating to URL: {str(e)}")
            return False

    def get_page_content(self):
        """
        Get the content of the current page.

        Returns:
            str: The page content
        """
        try:
            if self.use_advanced_browser:
                if self.playwright_page:
                    return self.playwright_page.content()
                elif self.selenium_driver:
                    return self.selenium_driver.page_source

            # Fallback to current page content
            return self.current_page_content or ""
        except Exception as e:
            print(f"Error getting page content: {str(e)}")
            return ""

    def take_screenshot(self, filename_prefix):
        """
        Take a screenshot of the current page.

        Args:
            filename_prefix (str): Prefix for the screenshot filename

        Returns:
            str: Path to the screenshot file, or None if failed
        """
        try:
            # Create screenshots directory if it doesn't exist
            screenshots_dir = os.path.join(os.getcwd(), 'static', 'screenshots')
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)

            # Generate filename
            timestamp = int(time.time())
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)

            # Take screenshot with advanced browser
            if self.use_advanced_browser:
                if self.playwright_page:
                    self.playwright_page.screenshot(path=filepath)
                    return f"/static/screenshots/{filename}"
                elif self.selenium_driver:
                    self.selenium_driver.save_screenshot(filepath)
                    return f"/static/screenshots/{filename}"

            # No screenshot capability available
            return None
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            return None

    def analyze_page(self):
        """
        Analyze the current page and extract key information.

        Returns:
            dict: A dictionary containing the analysis results.
        """
        if not self.current_soup or not self.current_url:
            return {"error": "No page currently loaded", "success": False}

        try:
            soup = self.current_soup

            # Extract forms
            forms = []
            for idx, form in enumerate(soup.find_all('form')):
                form_details = self._extract_form_details(form)
                form_details["id"] = idx  # Add an ID for reference
                forms.append(form_details)

            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Convert relative URLs to absolute
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(self.current_url, href)

                links.append({
                    "text": link.get_text(strip=True),
                    "href": href
                })

            # Extract headings for structure
            headings = []
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                headings.append({
                    "level": int(heading.name[1]),
                    "text": heading.get_text(strip=True)
                })

            return {
                "url": self.current_url,
                "title": soup.title.string if soup.title else "No title",
                "forms": forms,
                "links": links[:50],  # Limit to 50 links
                "headings": headings,
                "success": True
            }

        except Exception as e:
            return {"error": f"Error analyzing webpage: {str(e)}", "success": False}

    def submit_form(self, form_id, form_data):
        """
        Submit a form on the current page.

        Args:
            form_id (int): The ID of the form to submit.
            form_data (dict): The data to submit with the form.

        Returns:
            dict: A dictionary containing the response.
        """
        if not self.current_soup or not self.current_url:
            return {"error": "No page currently loaded", "success": False}

        try:
            # Try to use advanced browser if available
            if self.use_advanced_browser and (self.playwright_page or self.selenium_driver):
                return self._submit_form_with_advanced_browser(form_id, form_data)

            # Fallback to regular form submission
            # Find all forms
            forms = self.current_soup.find_all('form')

            # Check if form_id is valid
            if form_id >= len(forms):
                return {"error": f"Form ID {form_id} not found", "success": False}

            # Get the form
            form = forms[form_id]

            # Extract form details
            form_details = self._extract_form_details(form)

            # Prepare the data to be submitted
            data = {}
            for input_item in form_details["inputs"]:
                input_name = input_item["name"]
                if input_name:
                    # If the input name is in the form_data, use that value
                    if input_name in form_data:
                        data[input_name] = form_data[input_name]
                    # Otherwise use the default value
                    else:
                        data[input_name] = input_item["value"]

            # Submit the form
            if form_details["method"] == "post":
                response = self.session.post(form_details["action"], data=data, timeout=30)
            else:  # GET
                response = self.session.get(form_details["action"], params=data, timeout=30)

            response.raise_for_status()

            # Parse the response
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = soup.title.string if soup.title else "No title"

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text content
            text_content = soup.get_text(separator=' ', strip=True)

            # Update current state
            self.current_url = response.url
            self.current_page_content = text_content
            self.current_soup = soup

            return {
                "title": title,
                "content": text_content[:5000] + ("..." if len(text_content) > 5000 else ""),
                "url": response.url,
                "success": True
            }

        except Exception as e:
            return {"error": f"Error submitting form: {str(e)}", "success": False}

    def _submit_form_with_advanced_browser(self, form_id, form_data):
        """
        Submit a form using the advanced browser (Playwright or Selenium).

        Args:
            form_id (int): The ID of the form to submit.
            form_data (dict): The data to submit with the form.

        Returns:
            dict: A dictionary containing the response.
        """
        try:
            # Find all forms
            forms = self.current_soup.find_all('form')

            # Check if form_id is valid
            if form_id >= len(forms):
                return {"error": f"Form ID {form_id} not found", "success": False}

            # Get the form
            form = forms[form_id]

            # Extract form details
            form_details = self._extract_form_details(form)

            # Try with Playwright first
            if self.playwright_page:
                try:
                    print(f"DEBUG: Using Playwright to submit form")

                    # Fill in form fields
                    for input_item in form_details["inputs"]:
                        input_name = input_item["name"]
                        input_type = input_item["input_type"]

                        if not input_name:
                            continue

                        # Get the value to fill
                        value = form_data.get(input_name, input_item["value"])

                        # Skip submit buttons
                        if input_type == "submit":
                            continue

                        # Handle different input types
                        if input_type == "checkbox" or input_type == "radio":
                            if value:
                                # Check the box/radio button
                                self.playwright_page.check(f"[name='{input_name}']")
                        elif input_item["type"] == "select":
                            # Select dropdown option
                            self.playwright_page.select_option(f"select[name='{input_name}']", value=value)
                        else:
                            # Fill text inputs
                            self.playwright_page.fill(f"[name='{input_name}']", value)

                    # Submit the form
                    if form.get("id"):
                        self.playwright_page.click(f"#{form.get('id')} [type='submit']")
                    else:
                        # Try to find the submit button within the form
                        self.playwright_page.click("form [type='submit']")

                    # Wait for navigation to complete
                    self.playwright_page.wait_for_load_state('networkidle')

                    # Get the updated page content
                    html_content = self.playwright_page.content()

                    # Parse the content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Extract title
                    title = soup.title.string if soup.title else "No title"

                    # Remove script and style elements for text content
                    for script in soup(["script", "style"]):
                        script.extract()

                    # Get text content
                    text_content = soup.get_text(separator=' ', strip=True)

                    # Take a screenshot
                    try:
                        screenshot_bytes = self.playwright_page.screenshot()
                        screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
                        self.screenshot_data = screenshot_data
                    except Exception as screenshot_error:
                        print(f"DEBUG: Failed to take screenshot: {str(screenshot_error)}")
                        screenshot_data = None

                    # Update current state
                    self.current_url = self.playwright_page.url
                    self.current_page_content = text_content
                    self.current_soup = soup

                    # Extract images using the enhanced method
                    images = self._extract_images_from_soup(soup)

                    # Prepare result
                    result = {
                        "title": title,
                        "content": text_content[:5000] + ("..." if len(text_content) > 5000 else ""),
                        "url": self.current_url,
                        "html": html_content,
                        "images": images,
                        "success": True
                    }

                    # Add screenshot if available
                    if screenshot_data:
                        result["screenshot"] = screenshot_data

                    return result

                except Exception as e:
                    print(f"DEBUG: Playwright form submission error: {str(e)}")
                    # Fall through to Selenium

            # Try with Selenium if Playwright failed or is not available
            if self.selenium_driver:
                try:
                    print(f"DEBUG: Using Selenium to submit form")

                    # Fill in form fields
                    for input_item in form_details["inputs"]:
                        input_name = input_item["name"]
                        input_type = input_item["input_type"]

                        if not input_name:
                            continue

                        # Get the value to fill
                        value = form_data.get(input_name, input_item["value"])

                        # Skip submit buttons
                        if input_type == "submit":
                            continue

                        try:
                            # Find the element
                            element = self.selenium_driver.find_element("name", input_name)

                            # Handle different input types
                            if input_type == "checkbox" or input_type == "radio":
                                if value and not element.is_selected():
                                    element.click()
                            elif input_item["type"] == "select":
                                from selenium.webdriver.support.ui import Select
                                select = Select(element)
                                select.select_by_value(value)
                            else:
                                # Clear and fill text inputs
                                element.clear()
                                element.send_keys(value)
                        except Exception as elem_error:
                            print(f"DEBUG: Error interacting with element {input_name}: {str(elem_error)}")

                    # Submit the form
                    try:
                        # Try to find the submit button within the form
                        submit_button = self.selenium_driver.find_element("css selector", "form [type='submit']")
                        submit_button.click()
                    except Exception:
                        # If no submit button found, submit the form directly
                        form_element = self.selenium_driver.find_elements("tag name", "form")[form_id]
                        form_element.submit()

                    # Wait for page to load
                    time.sleep(2)  # Simple wait for page to load

                    # Get the updated page content
                    html_content = self.selenium_driver.page_source

                    # Parse the content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Extract title
                    title = soup.title.string if soup.title else "No title"

                    # Remove script and style elements for text content
                    for script in soup(["script", "style"]):
                        script.extract()

                    # Get text content
                    text_content = soup.get_text(separator=' ', strip=True)

                    # Take a screenshot
                    try:
                        screenshot_bytes = self.selenium_driver.get_screenshot_as_png()
                        screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
                        self.screenshot_data = screenshot_data
                    except Exception as screenshot_error:
                        print(f"DEBUG: Failed to take screenshot: {str(screenshot_error)}")
                        screenshot_data = None

                    # Update current state
                    self.current_url = self.selenium_driver.current_url
                    self.current_page_content = text_content
                    self.current_soup = soup

                    # Extract images using the enhanced method
                    images = self._extract_images_from_soup(soup)

                    # Prepare result
                    result = {
                        "title": title,
                        "content": text_content[:5000] + ("..." if len(text_content) > 5000 else ""),
                        "url": self.current_url,
                        "html": html_content,
                        "images": images,
                        "success": True
                    }

                    # Add screenshot if available
                    if screenshot_data:
                        result["screenshot"] = screenshot_data

                    return result

                except Exception as e:
                    print(f"DEBUG: Selenium form submission error: {str(e)}")
                    # Fall through to regular form submission
        except Exception as e:
            print(f"DEBUG: Advanced browser form submission error: {str(e)}")

        # If we get here, both Playwright and Selenium failed, so return an error
        return {"error": "Failed to submit form with advanced browser", "success": False}

    def follow_link(self, link_index):
        """
        Follow a link on the current page.

        Args:
            link_index (int): The index of the link to follow.

        Returns:
            dict: A dictionary containing the response.
        """
        if not self.current_soup or not self.current_url:
            return {"error": "No page currently loaded", "success": False}

        try:
            # Try to use advanced browser if available
            if self.use_advanced_browser and (self.playwright_page or self.selenium_driver):
                return self._follow_link_with_advanced_browser(link_index)

            # Fallback to regular link following
            # Find all links
            links = self.current_soup.find_all('a', href=True)

            # Check if link_index is valid
            if link_index >= len(links):
                return {"error": f"Link index {link_index} not found", "success": False}

            # Get the link
            link = links[link_index]
            href = link['href']

            # Convert relative URLs to absolute
            if not href.startswith(('http://', 'https://')):
                href = urljoin(self.current_url, href)

            # Follow the link
            return self.browse(href)

        except Exception as e:
            return {"error": f"Error following link: {str(e)}", "success": False}

    def _follow_link_with_advanced_browser(self, link_index):
        """
        Follow a link using the advanced browser (Playwright or Selenium).

        Args:
            link_index (int): The index of the link to follow.

        Returns:
            dict: A dictionary containing the response.
        """
        try:
            # Find all links
            links = self.current_soup.find_all('a', href=True)

            # Check if link_index is valid
            if link_index >= len(links):
                return {"error": f"Link index {link_index} not found", "success": False}

            # Get the link
            link = links[link_index]
            href = link['href']

            # Convert relative URLs to absolute
            if not href.startswith(('http://', 'https://')):
                href = urljoin(self.current_url, href)

            # Try with Playwright first
            if self.playwright_page:
                try:
                    print(f"DEBUG: Using Playwright to follow link to {href}")

                    # Click the link
                    self.playwright_page.click(f"a[href='{link['href']}']")

                    # Wait for navigation to complete
                    self.playwright_page.wait_for_load_state('networkidle')

                    # Get the updated page content
                    html_content = self.playwright_page.content()

                    # Parse the content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Extract title
                    title = soup.title.string if soup.title else "No title"

                    # Remove script and style elements for text content
                    for script in soup(["script", "style"]):
                        script.extract()

                    # Get text content
                    text_content = soup.get_text(separator=' ', strip=True)

                    # Take a screenshot
                    try:
                        screenshot_bytes = self.playwright_page.screenshot()
                        screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
                        self.screenshot_data = screenshot_data
                    except Exception as screenshot_error:
                        print(f"DEBUG: Failed to take screenshot: {str(screenshot_error)}")
                        screenshot_data = None

                    # Update current state
                    self.current_url = self.playwright_page.url
                    self.current_page_content = text_content
                    self.current_soup = soup

                    # Extract images using the enhanced method
                    images = self._extract_images_from_soup(soup)

                    # Prepare result
                    result = {
                        "title": title,
                        "content": text_content[:5000] + ("..." if len(text_content) > 5000 else ""),
                        "url": self.current_url,
                        "html": html_content,
                        "images": images,
                        "success": True
                    }

                    # Add screenshot if available
                    if screenshot_data:
                        result["screenshot"] = screenshot_data

                    return result

                except Exception as e:
                    print(f"DEBUG: Playwright link following error: {str(e)}")
                    # Fall through to Selenium

            # Try with Selenium if Playwright failed or is not available
            if self.selenium_driver:
                try:
                    print(f"DEBUG: Using Selenium to follow link to {href}")

                    # Find and click the link
                    try:
                        # Try to find the link by href
                        link_element = self.selenium_driver.find_element("css selector", f"a[href='{link['href']}']")
                        link_element.click()
                    except Exception:
                        # If not found, navigate directly to the URL
                        self.selenium_driver.get(href)

                    # Wait for page to load
                    time.sleep(2)  # Simple wait for page to load

                    # Get the updated page content
                    html_content = self.selenium_driver.page_source

                    # Parse the content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Extract title
                    title = soup.title.string if soup.title else "No title"

                    # Remove script and style elements for text content
                    for script in soup(["script", "style"]):
                        script.extract()

                    # Get text content
                    text_content = soup.get_text(separator=' ', strip=True)

                    # Take a screenshot
                    try:
                        screenshot_bytes = self.selenium_driver.get_screenshot_as_png()
                        screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
                        self.screenshot_data = screenshot_data
                    except Exception as screenshot_error:
                        print(f"DEBUG: Failed to take screenshot: {str(screenshot_error)}")
                        screenshot_data = None

                    # Update current state
                    self.current_url = self.selenium_driver.current_url
                    self.current_page_content = text_content
                    self.current_soup = soup

                    # Extract images using the enhanced method
                    images = self._extract_images_from_soup(soup)

                    # Prepare result
                    result = {
                        "title": title,
                        "content": text_content[:5000] + ("..." if len(text_content) > 5000 else ""),
                        "url": self.current_url,
                        "html": html_content,
                        "images": images,
                        "success": True
                    }

                    # Add screenshot if available
                    if screenshot_data:
                        result["screenshot"] = screenshot_data

                    return result

                except Exception as e:
                    print(f"DEBUG: Selenium link following error: {str(e)}")
                    # Fall through to regular link following
        except Exception as e:
            print(f"DEBUG: Advanced browser link following error: {str(e)}")

        # If we get here, both Playwright and Selenium failed, so return an error
        return {"error": "Failed to follow link with advanced browser", "success": False}

    def click_element(self, selector, selector_type="css"):
        """
        Click on an element in the current page.

        Args:
            selector (str): The selector to use to find the element.
            selector_type (str): The type of selector to use. Can be 'css', 'xpath', or 'text'.

        Returns:
            dict: A dictionary containing the response.
        """
        if not self.use_advanced_browser or (not self.playwright_page and not self.selenium_driver):
            return {"error": "Advanced browser is required for clicking elements", "success": False}

        if not self.current_soup or not self.current_url:
            return {"error": "No page currently loaded", "success": False}

        try:
            # Try with Playwright first
            if self.playwright_page:
                try:
                    print(f"DEBUG: Using Playwright to click element with selector: {selector}")

                    # Click the element based on selector type
                    if selector_type == "css":
                        self.playwright_page.click(selector)
                    elif selector_type == "xpath":
                        self.playwright_page.click(f"xpath={selector}")
                    elif selector_type == "text":
                        self.playwright_page.click(f"text={selector}")
                    else:
                        return {"error": f"Invalid selector type: {selector_type}", "success": False}

                    # Wait for navigation to complete
                    self.playwright_page.wait_for_load_state('networkidle')

                    # Get the updated page content
                    html_content = self.playwright_page.content()

                    # Parse the content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Extract title
                    title = soup.title.string if soup.title else "No title"

                    # Remove script and style elements for text content
                    for script in soup(["script", "style"]):
                        script.extract()

                    # Get text content
                    text_content = soup.get_text(separator=' ', strip=True)

                    # Take a screenshot
                    try:
                        print(f"DEBUG: Taking screenshot of {self.playwright_page.url}")
                        screenshot_bytes = self.playwright_page.screenshot()
                        screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
                        self.screenshot_data = screenshot_data
                        print(f"DEBUG: Screenshot taken successfully, size: {len(screenshot_data)} bytes")
                        # Save a copy of the screenshot to disk for debugging
                        debug_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug_screenshot.png')
                        with open(debug_path, 'wb') as f:
                            f.write(screenshot_bytes)
                        print(f"DEBUG: Saved debug screenshot to {debug_path}")
                    except Exception as screenshot_error:
                        print(f"DEBUG: Failed to take screenshot: {str(screenshot_error)}")
                        screenshot_data = None

                    # Update current state
                    self.current_url = self.playwright_page.url
                    self.current_page_content = text_content
                    self.current_soup = soup

                    # Extract images using the enhanced method
                    images = self._extract_images_from_soup(soup)

                    # Prepare result
                    result = {
                        "title": title,
                        "content": text_content[:5000] + ("..." if len(text_content) > 5000 else ""),
                        "url": self.current_url,
                        "html": html_content,
                        "images": images,
                        "success": True
                    }

                    # Add screenshot if available
                    if screenshot_data:
                        result["screenshot"] = screenshot_data

                    return result

                except Exception as e:
                    print(f"DEBUG: Playwright element clicking error: {str(e)}")
                    # Fall through to Selenium

            # Try with Selenium if Playwright failed or is not available
            if self.selenium_driver:
                try:
                    print(f"DEBUG: Using Selenium to click element with selector: {selector}")

                    # Find and click the element based on selector type
                    if selector_type == "css":
                        element = self.selenium_driver.find_element("css selector", selector)
                    elif selector_type == "xpath":
                        element = self.selenium_driver.find_element("xpath", selector)
                    elif selector_type == "text":
                        # For text, we need to use XPath
                        element = self.selenium_driver.find_element("xpath", f"//*[contains(text(), '{selector}')]")
                    else:
                        return {"error": f"Invalid selector type: {selector_type}", "success": False}

                    # Click the element
                    element.click()

                    # Wait for page to load
                    time.sleep(2)  # Simple wait for page to load

                    # Get the updated page content
                    html_content = self.selenium_driver.page_source

                    # Parse the content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Extract title
                    title = soup.title.string if soup.title else "No title"

                    # Remove script and style elements for text content
                    for script in soup(["script", "style"]):
                        script.extract()

                    # Get text content
                    text_content = soup.get_text(separator=' ', strip=True)

                    # Take a screenshot
                    try:
                        screenshot_bytes = self.selenium_driver.get_screenshot_as_png()
                        screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
                        self.screenshot_data = screenshot_data
                    except Exception as screenshot_error:
                        print(f"DEBUG: Failed to take screenshot: {str(screenshot_error)}")
                        screenshot_data = None

                    # Update current state
                    self.current_url = self.selenium_driver.current_url
                    self.current_page_content = text_content
                    self.current_soup = soup

                    # Extract images using the enhanced method
                    images = self._extract_images_from_soup(soup)

                    # Prepare result
                    result = {
                        "title": title,
                        "content": text_content[:5000] + ("..." if len(text_content) > 5000 else ""),
                        "url": self.current_url,
                        "html": html_content,
                        "images": images,
                        "success": True
                    }

                    # Add screenshot if available
                    if screenshot_data:
                        result["screenshot"] = screenshot_data

                    return result

                except Exception as e:
                    print(f"DEBUG: Selenium element clicking error: {str(e)}")
                    # Fall through to error
        except Exception as e:
            print(f"DEBUG: Advanced browser element clicking error: {str(e)}")

        # If we get here, both Playwright and Selenium failed, so return an error
        return {"error": "Failed to click element with advanced browser", "success": False}

    def _extract_form_details(self, form):
        """
        Extract details from a form element.

        Args:
            form: BeautifulSoup form element.

        Returns:
            dict: A dictionary containing form details.
        """
        details = {}

        # Get the form action (URL)
        action = form.get("action")
        if action:
            # If action is a relative URL, make it absolute
            if not action.startswith(('http://', 'https://')):
                action = urljoin(self.current_url, action)
        else:
            # If no action is specified, use the current URL
            action = self.current_url

        # Get the form method (POST, GET, etc.)
        method = form.get("method", "get").lower()

        # Get form inputs
        inputs = []
        for input_tag in form.find_all(["input", "textarea", "select"]):
            input_type = input_tag.get("type", "text")
            input_name = input_tag.get("name")
            input_value = input_tag.get("value", "")

            # Handle select elements
            if input_tag.name == "select":
                selected_option = input_tag.find("option", selected=True)
                if selected_option:
                    input_value = selected_option.get("value", "")

            inputs.append({
                "type": input_tag.name,
                "input_type": input_type,
                "name": input_name,
                "value": input_value
            })

        # Set the form details
        details["action"] = action
        details["method"] = method
        details["inputs"] = inputs

        return details

    def _browse_with_advanced_browser(self, url, timeout=10):
        """
        Browse to a URL using the advanced browser (Playwright or Selenium).

        Args:
            url (str): The URL to browse to.
            timeout (int, optional): Timeout in seconds. Defaults to 30.

        Returns:
            dict: A dictionary containing the page content, URL, and status.
        """
        screenshot_data = None

        try:
            # Try with Playwright first
            if self.playwright_page:
                try:
                    print(f"DEBUG: Using Playwright to browse to {url}")
                    # Navigate to the URL
                    self.playwright_page.goto(url, timeout=timeout * 1000)  # Playwright uses milliseconds

                    # Wait for the page to load completely
                    self.playwright_page.wait_for_load_state('networkidle')

                    # Get the current URL (may have changed due to redirects)
                    self.current_url = self.playwright_page.url

                    # Get the page content
                    html_content = self.playwright_page.content()

                    # Parse the content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Extract title
                    title = soup.title.string if soup.title else "No title"

                    # Remove script and style elements for text content
                    for script in soup(["script", "style"]):
                        script.extract()

                    # Get text content
                    text_content = soup.get_text(separator=' ', strip=True)

                    # Take a screenshot
                    try:
                        screenshot_bytes = self.playwright_page.screenshot()
                        screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
                        self.screenshot_data = screenshot_data
                    except Exception as screenshot_error:
                        print(f"DEBUG: Failed to take screenshot: {str(screenshot_error)}")

                    # Store current state
                    self.current_url = self.playwright_page.url
                    self.current_page_content = text_content
                    self.current_soup = soup

                    # Extract images
                    images = []
                    try:
                        # Find all img tags with src attribute
                        img_tags = soup.find_all('img', src=True)
                        print(f"DEBUG: Found {len(img_tags)} image tags on the page")

                        # Find all picture elements with source tags
                        picture_tags = soup.find_all('picture')
                        for picture in picture_tags:
                            sources = picture.find_all('source', srcset=True)
                            for source in sources:
                                srcset = source.get('srcset', '')
                                if srcset:
                                    # Extract the first URL from srcset (highest quality)
                                    srcset_parts = srcset.split(',')[0].strip().split(' ')[0]
                                    if srcset_parts:
                                        img = soup.new_tag('img')
                                        img['src'] = srcset_parts
                                        img['alt'] = source.get('alt', 'Image from picture element')
                                        img_tags.append(img)

                        # Find background images in style attributes
                        elements_with_style = soup.find_all(attrs={'style': True})
                        for element in elements_with_style:
                            style = element.get('style', '')
                            if 'background-image' in style:
                                # Extract URL from background-image: url('...')
                                match = re.search(r"background-image:\s*url\(['\"]?([^'\"\)]+)['\"]?\)", style)
                                if match:
                                    img = soup.new_tag('img')
                                    img['src'] = match.group(1)
                                    img['alt'] = 'Background image'
                                    img_tags.append(img)

                        # Process all image sources
                        for img in img_tags:
                            src = img.get('src')
                            # Convert relative URLs to absolute
                            if src and not src.startswith(('http://', 'https://', 'data:')):
                                src = urljoin(self.current_url, src)

                            # Skip data URLs, SVGs, and very small images
                            if src and not src.startswith('data:') and not src.endswith('.svg'):
                                # Get alt text and dimensions if available
                                alt = img.get('alt', '')
                                width = img.get('width', 0)
                                height = img.get('height', 0)

                                # Try to determine image quality and relevance
                                is_relevant = False

                                # Check dimensions if available
                                if width and height:
                                    try:
                                        w, h = int(width), int(height)
                                        # Larger images are more likely to be content-relevant
                                        if w >= 200 and h >= 200:
                                            is_relevant = True
                                        # Medium-sized images might be relevant
                                        elif w >= 100 and h >= 100:
                                            # Check if the image has a descriptive alt text
                                            if alt and len(alt) > 10:
                                                is_relevant = True
                                    except (ValueError, TypeError):
                                        pass

                                # Check file extension for common image formats
                                if not is_relevant:
                                    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
                                    if any(src.lower().endswith(ext) for ext in image_extensions):
                                        is_relevant = True

                                # Check if image is in a relevant container
                                if not is_relevant:
                                    parent = img.parent
                                    if parent:
                                        # Images in articles, figures, or main content are likely relevant
                                        if parent.name in ['figure', 'article', 'main', 'section'] or \
                                           parent.get('class') and any(c for c in parent.get('class') if 'content' in c.lower()):
                                            is_relevant = True

                                # Add relevant images to the results
                                if is_relevant:
                                    images.append({
                                        "src": src,
                                        "alt": alt,
                                        "width": width,
                                        "height": height
                                    })
                                    print(f"DEBUG: Added image to results: {src[:100]}...")

                                    # Limit to 10 images to avoid overloading
                                    if len(images) >= 10:
                                        break

                        # Sort images by size (larger first) if dimensions are available
                        images.sort(key=lambda img:
                            -1 * int(img.get('width', 0)) * int(img.get('height', 0))
                            if img.get('width') and img.get('height') else 0
                        )

                        print(f"DEBUG: Extracted {len(images)} images from the page")
                    except Exception as img_error:
                        print(f"DEBUG: Error extracting images: {str(img_error)}")

                    # Prepare result
                    result = {
                        "title": title,
                        "content": text_content[:5000] + ("..." if len(text_content) > 5000 else ""),
                        "url": self.current_url,
                        "html": html_content,
                        "images": images,
                        "success": True
                    }

                    # Add screenshot if available
                    if screenshot_data:
                        result["screenshot"] = screenshot_data

                    # Cache the response
                    if self.cache_enabled:
                        cache_key = self._get_cache_key(url)
                        self._save_to_cache(cache_key, result)

                    print(f"DEBUG: Successfully browsed to {url} with Playwright")
                    return result
                except Exception as e:
                    print(f"DEBUG: Playwright error: {str(e)}")
                    # Fall through to Selenium

            # Try with Selenium if Playwright failed or is not available
            if self.selenium_driver:
                try:
                    print(f"DEBUG: Using Selenium to browse to {url}")
                    # Navigate to the URL
                    self.selenium_driver.get(url)

                    # Wait for the page to load
                    time.sleep(2)  # Simple wait for page to load

                    # Get the current URL
                    self.current_url = self.selenium_driver.current_url

                    # Get the page content
                    html_content = self.selenium_driver.page_source

                    # Parse the content with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # Extract title
                    title = soup.title.string if soup.title else "No title"

                    # Remove script and style elements for text content
                    for script in soup(["script", "style"]):
                        script.extract()

                    # Get text content
                    text_content = soup.get_text(separator=' ', strip=True)

                    # Take a screenshot
                    try:
                        screenshot_bytes = self.selenium_driver.get_screenshot_as_png()
                        screenshot_data = base64.b64encode(screenshot_bytes).decode('utf-8')
                        self.screenshot_data = screenshot_data
                    except Exception as screenshot_error:
                        print(f"DEBUG: Failed to take screenshot: {str(screenshot_error)}")

                    # Store current state
                    self.current_url = self.selenium_driver.current_url
                    self.current_page_content = text_content
                    self.current_soup = soup

                    # Extract images
                    images = []
                    try:
                        import re  # Add import for regex pattern matching

                        # Find all img tags with src attribute
                        img_tags = soup.find_all('img', src=True)
                        print(f"DEBUG: Found {len(img_tags)} image tags on the page")

                        # Find all picture elements with source tags
                        picture_tags = soup.find_all('picture')
                        for picture in picture_tags:
                            sources = picture.find_all('source', srcset=True)
                            for source in sources:
                                srcset = source.get('srcset', '')
                                if srcset:
                                    # Extract the first URL from srcset (highest quality)
                                    srcset_parts = srcset.split(',')[0].strip().split(' ')[0]
                                    if srcset_parts:
                                        img = soup.new_tag('img')
                                        img['src'] = srcset_parts
                                        img['alt'] = source.get('alt', 'Image from picture element')
                                        img_tags.append(img)

                        # Find background images in style attributes
                        elements_with_style = soup.find_all(attrs={'style': True})
                        for element in elements_with_style:
                            style = element.get('style', '')
                            if 'background-image' in style:
                                # Extract URL from background-image: url('...')
                                match = re.search(r"background-image:\s*url\(['\"]?([^'\"\)]+)['\"]?\)", style)
                                if match:
                                    img = soup.new_tag('img')
                                    img['src'] = match.group(1)
                                    img['alt'] = 'Background image'
                                    img_tags.append(img)

                        # Process all image sources
                        for img in img_tags:
                            src = img.get('src')
                            # Convert relative URLs to absolute
                            if src and not src.startswith(('http://', 'https://', 'data:')):
                                src = urljoin(self.current_url, src)

                            # Skip data URLs, SVGs, and very small images
                            if src and not src.startswith('data:') and not src.endswith('.svg'):
                                # Get alt text and dimensions if available
                                alt = img.get('alt', '')
                                width = img.get('width', 0)
                                height = img.get('height', 0)

                                # Try to determine image quality and relevance
                                is_relevant = False

                                # Check dimensions if available
                                if width and height:
                                    try:
                                        w, h = int(width), int(height)
                                        # Larger images are more likely to be content-relevant
                                        if w >= 200 and h >= 200:
                                            is_relevant = True
                                        # Medium-sized images might be relevant
                                        elif w >= 100 and h >= 100:
                                            # Check if the image has a descriptive alt text
                                            if alt and len(alt) > 10:
                                                is_relevant = True
                                    except (ValueError, TypeError):
                                        pass

                                # Check file extension for common image formats
                                if not is_relevant:
                                    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
                                    if any(src.lower().endswith(ext) for ext in image_extensions):
                                        is_relevant = True

                                # Check if image is in a relevant container
                                if not is_relevant:
                                    parent = img.parent
                                    if parent:
                                        # Images in articles, figures, or main content are likely relevant
                                        if parent.name in ['figure', 'article', 'main', 'section'] or \
                                           (parent.get('class') and any(c for c in parent.get('class') if 'content' in c.lower())):
                                            is_relevant = True

                                # Add relevant images to the results
                                if is_relevant:
                                    images.append({
                                        "src": src,
                                        "alt": alt,
                                        "width": width,
                                        "height": height
                                    })
                                    print(f"DEBUG: Added image to results: {src[:100]}...")

                                    # Limit to 10 images to avoid overloading
                                    if len(images) >= 10:
                                        break

                        # Sort images by size (larger first) if dimensions are available
                        images.sort(key=lambda img:
                            -1 * int(img.get('width', 0)) * int(img.get('height', 0))
                            if img.get('width') and img.get('height') else 0
                        )
                    except Exception as img_error:
                        print(f"DEBUG: Error extracting images: {str(img_error)}")

                    # Prepare result
                    result = {
                        "title": title,
                        "content": text_content[:5000] + ("..." if len(text_content) > 5000 else ""),
                        "url": self.current_url,
                        "html": html_content,
                        "images": images,
                        "success": True
                    }

                    # Add screenshot if available
                    if screenshot_data:
                        result["screenshot"] = screenshot_data

                    # Cache the response
                    if self.cache_enabled:
                        cache_key = self._get_cache_key(url)
                        self._save_to_cache(cache_key, result)

                    print(f"DEBUG: Successfully browsed to {url} with Selenium")
                    return result
                except Exception as e:
                    print(f"DEBUG: Selenium error: {str(e)}")
                    # Fall through to requests
        except Exception as e:
            print(f"DEBUG: Advanced browser error: {str(e)}")

        # If we get here, both Playwright and Selenium failed, so fall back to requests
        print(f"DEBUG: Falling back to requests-based browsing for {url}")
        return None  # Signal to the caller to use the regular browse method

    def _get_cache_key(self, url):
        """
        Generate a cache key for a URL.

        Args:
            url (str): The URL to generate a cache key for.

        Returns:
            str: The cache key.
        """
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cache_path(self, cache_key):
        """
        Get the file path for a cache key.

        Args:
            cache_key (str): The cache key.

        Returns:
            str: The file path.
        """
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def _save_to_cache(self, cache_key, data):
        """
        Save data to the cache.

        Args:
            cache_key (str): The cache key.
            data (dict): The data to cache.
        """
        if not self.cache_enabled:
            return

        try:
            # Add timestamp for expiry checking
            current_time = time.time()
            cache_data = {
                "timestamp": current_time,
                "data": data
            }

            # Update access time for LRU tracking
            self.cache_access_times[cache_key] = current_time

            # Check if we need to evict items from memory cache (LRU policy)
            if len(self.cache) >= self.max_cache_size:
                # Find the least recently used item
                oldest_key = min(self.cache_access_times.items(), key=lambda x: x[1])[0]
                # Remove it from memory cache
                if oldest_key in self.cache:
                    del self.cache[oldest_key]
                    del self.cache_access_times[oldest_key]
                    print(f"Evicted least recently used item from cache: {oldest_key}")

            # Save to memory cache
            self.cache[cache_key] = cache_data

            # Save to disk cache
            cache_path = self._get_cache_path(cache_key)
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)

            print(f"Saved data to cache: {cache_key}")
        except Exception as e:
            print(f"Error saving to cache: {str(e)}")

    def _get_from_cache(self, cache_key):
        """
        Get data from the cache.

        Args:
            cache_key (str): The cache key.

        Returns:
            dict or None: The cached data or None if not found or expired.
        """
        if not self.cache_enabled:
            return None

        current_time = time.time()

        # Check memory cache first
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            # Check if cache is expired
            if current_time - cache_data["timestamp"] < self.cache_expiry:
                # Update access time for LRU tracking
                self.cache_access_times[cache_key] = current_time
                self.cache_hits += 1
                print(f"Cache hit (memory): {cache_key} (hits: {self.cache_hits}, misses: {self.cache_misses})")
                return cache_data["data"]

        # Check disk cache
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

                # Check if cache is expired
                if current_time - cache_data["timestamp"] < self.cache_expiry:
                    # Update memory cache
                    self.cache[cache_key] = cache_data
                    # Update access time for LRU tracking
                    self.cache_access_times[cache_key] = current_time

                    # Check if we need to evict items from memory cache (LRU policy)
                    if len(self.cache) > self.max_cache_size:
                        # Find the least recently used item
                        oldest_key = min(self.cache_access_times.items(), key=lambda x: x[1])[0]
                        # Remove it from memory cache
                        if oldest_key in self.cache:
                            del self.cache[oldest_key]
                            del self.cache_access_times[oldest_key]
                            print(f"Evicted least recently used item from cache: {oldest_key}")

                    self.cache_hits += 1
                    print(f"Cache hit (disk): {cache_key} (hits: {self.cache_hits}, misses: {self.cache_misses})")
                    return cache_data["data"]
                else:
                    # Cache is expired, remove the file
                    try:
                        os.remove(cache_path)
                        print(f"Removed expired cache file: {cache_path}")
                    except Exception as remove_error:
                        print(f"Error removing expired cache file: {str(remove_error)}")
            except Exception as e:
                print(f"Error reading from cache: {str(e)}")

        self.cache_misses += 1
        print(f"Cache miss: {cache_key} (hits: {self.cache_hits}, misses: {self.cache_misses})")
        return None

    def get_cache_stats(self):
        """
        Get cache statistics.

        Returns:
            dict: A dictionary containing cache statistics.
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests) * 100 if total_requests > 0 else 0

        # Count disk cache files
        disk_cache_count = 0
        if self.cache_enabled and os.path.exists(self.cache_dir):
            disk_cache_count = len([f for f in os.listdir(self.cache_dir) if f.endswith('.json')])

        return {
            "memory_cache_size": len(self.cache),
            "disk_cache_size": disk_cache_count,
            "max_cache_size": self.max_cache_size,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "cache_enabled": self.cache_enabled,
            "cache_expiry": self.cache_expiry
        }

    def browse_multiple(self, urls, max_workers=5, timeout=30, headers=None, cookies=None, use_cache=True):
        """
        Browse multiple URLs in parallel and return the results.

        Args:
            urls (list): List of URLs to browse.
            max_workers (int, optional): Maximum number of parallel workers. Defaults to 5.
            timeout (int, optional): Request timeout in seconds. Defaults to 30.
            headers (dict, optional): Additional headers to send. Defaults to None.
            cookies (dict, optional): Cookies to send. Defaults to None.
            use_cache (bool, optional): Whether to use the cache. Defaults to True.

        Returns:
            list: A list of dictionaries containing the results for each URL.
        """
        results = []

        # Define a worker function to browse a single URL
        def browse_worker(url):
            try:
                return self.browse(url, timeout, headers, cookies, use_cache)
            except Exception as e:
                print(f"Error browsing {url}: {str(e)}")
                return {
                    "url": url,
                    "error": f"Error browsing {url}: {str(e)}",
                    "success": False
                }

        # Use ThreadPoolExecutor for parallel browsing
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all browsing tasks
            future_to_url = {executor.submit(browse_worker, url): url for url in urls}

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"Completed browsing {url}")
                except Exception as e:
                    print(f"Exception while processing result for {url}: {str(e)}")
                    results.append({
                        "url": url,
                        "error": f"Exception while processing result: {str(e)}",
                        "success": False
                    })

        # Sort results to match the order of input URLs
        url_to_index = {url: i for i, url in enumerate(urls)}
        results.sort(key=lambda x: url_to_index.get(x.get("url", ""), 999999))

        return results

    def search(self, query, num_results=5, use_cache=True):
        """
        Search for a query using a search engine and return the results.

        This is a simple implementation that uses a search engine to find relevant URLs,
        then browses those URLs to get their content.

        Args:
            query (str): The search query.
            num_results (int, optional): Number of results to return. Defaults to 5.
            use_cache (bool, optional): Whether to use the cache. Defaults to True.

        Returns:
            list: A list of dictionaries containing the search results.
        """
        try:
            # Construct a Google search URL
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

            # Browse the search results page
            search_results = self.browse(search_url, use_cache=use_cache)

            if not search_results.get("success", False):
                return [{
                    "error": f"Failed to get search results: {search_results.get('error', 'Unknown error')}",
                    "success": False
                }]

            # Extract result URLs from the search page
            soup = BeautifulSoup(search_results.get("html", ""), 'html.parser')
            result_urls = []

            # Look for search result links
            for a in soup.select('a'):
                href = a.get('href', '')
                # Google search results have URLs in this format
                if href.startswith('/url?q='):
                    # Extract the actual URL
                    url = href.split('/url?q=')[1].split('&')[0]
                    # Skip Google and similar domains
                    if not any(domain in url for domain in ['google.com', 'youtube.com', 'facebook.com', 'twitter.com']):
                        result_urls.append(url)
                        if len(result_urls) >= num_results:
                            break

            # If we didn't find enough results, try a different approach
            if len(result_urls) < num_results:
                for div in soup.select('div.g'):
                    a_tag = div.select_one('a')
                    if a_tag and a_tag.has_attr('href'):
                        href = a_tag['href']
                        if href.startswith('http'):
                            if href not in result_urls:
                                result_urls.append(href)
                                if len(result_urls) >= num_results:
                                    break

            # If we still don't have enough results, look for any links
            if len(result_urls) < num_results:
                for a in soup.select('a[href^="http"]'):
                    href = a['href']
                    # Skip Google and similar domains
                    if not any(domain in href for domain in ['google.com', 'youtube.com', 'facebook.com', 'twitter.com']):
                        if href not in result_urls:
                            result_urls.append(href)
                            if len(result_urls) >= num_results:
                                break

            print(f"Found {len(result_urls)} search result URLs")

            # Browse all result URLs in parallel
            if result_urls:
                return self.browse_multiple(result_urls, max_workers=min(len(result_urls), 5), use_cache=use_cache)
            else:
                return [{
                    "error": "No search results found",
                    "success": False
                }]

        except Exception as e:
            print(f"Error in search: {str(e)}")
            return [{
                "error": f"Error in search: {str(e)}",
                "success": False
            }]

    def _extract_images_from_soup(self, soup):
        """
        Extract images from a BeautifulSoup object using enhanced methods.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object to extract images from.

        Returns:
            list: A list of image objects with src, alt, width, and height.
        """
        images = []
        try:
            import re  # Add import for regex pattern matching

            # Find all img tags with src attribute
            img_tags = soup.find_all('img', src=True)
            print(f"DEBUG: Found {len(img_tags)} image tags on the page")

            # Find all picture elements with source tags
            picture_tags = soup.find_all('picture')
            for picture in picture_tags:
                sources = picture.find_all('source', srcset=True)
                for source in sources:
                    srcset = source.get('srcset', '')
                    if srcset:
                        # Extract the first URL from srcset (highest quality)
                        srcset_parts = srcset.split(',')[0].strip().split(' ')[0]
                        if srcset_parts:
                            img = soup.new_tag('img')
                            img['src'] = srcset_parts
                            img['alt'] = source.get('alt', 'Image from picture element')
                            img_tags.append(img)

            # Find background images in style attributes
            elements_with_style = soup.find_all(attrs={'style': True})
            for element in elements_with_style:
                style = element.get('style', '')
                if 'background-image' in style:
                    # Extract URL from background-image: url('...')
                    match = re.search(r"background-image:\s*url\(['\"]?([^'\"\)]+)['\"]?\)", style)
                    if match:
                        img = soup.new_tag('img')
                        img['src'] = match.group(1)
                        img['alt'] = 'Background image'
                        img_tags.append(img)

            # Process all image sources
            for img in img_tags:
                src = img.get('src')
                # Convert relative URLs to absolute
                if src and not src.startswith(('http://', 'https://', 'data:')):
                    src = urljoin(self.current_url, src)

                # Skip data URLs, SVGs, and very small images
                if src and not src.startswith('data:') and not src.endswith('.svg'):
                    # Get alt text and dimensions if available
                    alt = img.get('alt', '')
                    width = img.get('width', 0)
                    height = img.get('height', 0)

                    # Try to determine image quality and relevance
                    is_relevant = False

                    # Check dimensions if available
                    if width and height:
                        try:
                            w, h = int(width), int(height)
                            # Larger images are more likely to be content-relevant
                            if w >= 200 and h >= 200:
                                is_relevant = True
                            # Medium-sized images might be relevant
                            elif w >= 100 and h >= 100:
                                # Check if the image has a descriptive alt text
                                if alt and len(alt) > 10:
                                    is_relevant = True
                        except (ValueError, TypeError):
                            pass

                    # Check file extension for common image formats
                    if not is_relevant:
                        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
                        if any(src.lower().endswith(ext) for ext in image_extensions):
                            is_relevant = True

                    # Check if image is in a relevant container
                    if not is_relevant:
                        parent = img.parent
                        if parent:
                            # Images in articles, figures, or main content are likely relevant
                            if parent.name in ['figure', 'article', 'main', 'section'] or \
                               (parent.get('class') and any(c for c in parent.get('class') if 'content' in c.lower())):
                                is_relevant = True

                    # Add relevant images to the results
                    if is_relevant:
                        images.append({
                            "src": src,
                            "alt": alt,
                            "width": width,
                            "height": height
                        })
                        print(f"DEBUG: Added image to results: {src[:100]}...")

                        # Limit to 10 images to avoid overloading
                        if len(images) >= 10:
                            break

            # Sort images by size (larger first) if dimensions are available
            images.sort(key=lambda img:
                -1 * int(img.get('width', 0)) * int(img.get('height', 0))
                if img.get('width') and img.get('height') else 0
            )

        except Exception as e:
            print(f"DEBUG: Error extracting images from soup: {str(e)}")

        return images
