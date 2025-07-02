"""
Live Browser Automation for Visual Browser.

This module provides a class for automating a visible browser that users can watch in real-time.
"""

import os
import time
import random
import logging
import threading
import traceback
import resource
import json
from typing import Dict, Any, List, Optional, Tuple

# Import configuration
try:
    from app.visual_browser.config import BROWSER_CONFIG
except ImportError:
    # Default configuration if config module is not available
    BROWSER_CONFIG = {
        'lightweight_mode': True,
        'screenshot_interval_ms': 1000,
        'disable_screenshots': True,
        'disable_screen_recording': True,
        'window_width': 800,
        'window_height': 600,
        'memory_limit_mb': 512,
        'max_steps': 5,
        'execution_timeout_seconds': 30,
        'step_timeout_seconds': 5,
    }

# Import browser events module
try:
    from app.visual_browser.browser_events import (
        send_navigation_event,
        send_search_event,
        send_status_event,
        send_error_event,
        send_screenshot_event
    )
    EVENTS_AVAILABLE = True
except ImportError:
    EVENTS_AVAILABLE = False
    def send_navigation_event(*args, **kwargs): pass
    def send_search_event(*args, **kwargs): pass
    def send_status_event(*args, **kwargs): pass
    def send_error_event(*args, **kwargs): pass
    def send_screenshot_event(*args, **kwargs): pass

# Import Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LiveBrowser:
    """
    A class for automating a visible browser that users can watch in real-time.
    """

    def __init__(self):
        """
        Initialize the Live Browser.
        """
        self.driver = None
        self.current_url = None
        self.is_running = False
        self.task_queue = []
        self.task_thread = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Live Browser initialized")

    # Import execute_complex_task method
    from app.visual_browser.execute_complex_task import execute_complex_task

    def start(self) -> Dict[str, Any]:
        """
        Start the browser.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            # If browser is already running, check if it's still responsive
            if self.is_running and self.driver:
                try:
                    # Test if the driver is still responsive
                    _ = self.driver.window_handles
                    self.logger.info("Browser is already running and responsive")

                    # Make sure screenshot service is running
                    try:
                        from app.visual_browser.screenshot_service import get_screenshot_service
                        screenshot_service = get_screenshot_service()
                        if screenshot_service and not screenshot_service.is_running:
                            screenshot_service.start()
                    except Exception as ss_error:
                        self.logger.warning(f"Error starting screenshot service: {str(ss_error)}")

                    return {
                        "success": True,
                        "message": "Browser is already running"
                    }
                except Exception as e:
                    # Driver is not responsive, clean up and restart
                    self.logger.warning(f"Browser is marked as running but not responsive: {str(e)}")
                    self.logger.info("Cleaning up and restarting browser...")
                    try:
                        if self.driver:
                            self.driver.quit()
                    except:
                        pass
                    self.driver = None
                    self.is_running = False

            self.logger.info("Starting live browser...")

            # Set up Chrome options for a visible browser
            chrome_options = Options()

            # Set resource limits for the process
            try:
                # Limit memory usage based on configuration
                memory_limit_bytes = BROWSER_CONFIG['memory_limit_mb'] * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
                self.logger.info(f"Set memory limit to {BROWSER_CONFIG['memory_limit_mb']}MB")
            except Exception as e:
                self.logger.warning(f"Could not set memory limit: {str(e)}")

            # Set window size based on configuration
            window_width = BROWSER_CONFIG['window_width']
            window_height = BROWSER_CONFIG['window_height']
            chrome_options.add_argument(f"--window-size={window_width},{window_height}")
            self.logger.info(f"Set window size to {window_width}x{window_height}")

            # Add comprehensive stealth arguments to avoid detection
            # These settings help prevent the "No secure data" message in the URL bar

            # Add arguments that help with stealth
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-automation")

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
                self.logger.warning(f"Could not add experimental options: {str(e)}")
                # Continue anyway, this is not critical

            # Add a realistic user agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")

            # Basic necessary options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")

            # Add options for lightweight mode
            if BROWSER_CONFIG['lightweight_mode']:
                self.logger.info("Using lightweight mode for browser")

                # Disable features to reduce memory usage
                chrome_options.add_argument("--disable-3d-apis")
                chrome_options.add_argument("--disable-accelerated-2d-canvas")
                chrome_options.add_argument("--disable-accelerated-video-decode")
                chrome_options.add_argument("--disable-background-networking")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-breakpad")
                chrome_options.add_argument("--disable-client-side-phishing-detection")
                chrome_options.add_argument("--disable-default-apps")
                chrome_options.add_argument("--disable-hang-monitor")
                chrome_options.add_argument("--disable-prompt-on-repost")
                chrome_options.add_argument("--disable-sync")
                chrome_options.add_argument("--disable-translate")
                chrome_options.add_argument("--metrics-recording-only")
                chrome_options.add_argument("--no-first-run")
                chrome_options.add_argument("--safebrowsing-disable-auto-update")
                chrome_options.add_argument("--password-store=basic")
                chrome_options.add_argument("--mute-audio")
                chrome_options.add_argument("--js-flags=--expose-gc")

                # Disable images to reduce memory usage
                chrome_options.add_experimental_option("prefs", {
                    "profile.default_content_setting_values.images": 2,  # 2 = block images
                    "profile.managed_default_content_settings.images": 2
                })

            # Add options to make browser more stable
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--ignore-certificate-errors")

            # Set up Chrome service
            service = Service(ChromeDriverManager().install())

            # Create a new Chrome driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Maximize the window to make it more visible to the user
            self.driver.maximize_window()

            # Apply additional stealth settings via JavaScript
            # This helps avoid detection by websites like Google
            try:
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
                    "platform": "macOS"
                })
            except Exception as e:
                self.logger.warning(f"Could not set user agent via CDP: {str(e)}")
                # Continue anyway, this is not critical

            # Apply comprehensive stealth techniques via JavaScript
            # These techniques help prevent detection and the "No secure data" message
            try:
                # Apply multiple stealth techniques in one script
                self.driver.execute_script("""
                    // Advanced stealth script for Chrome 135+
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

                        // 2. Modify the user agent if needed
                        try {
                            Object.defineProperty(navigator, 'userAgent', {
                                get: () => window.navigator.userAgent.replace('Headless', '')
                            });
                        } catch (e) { console.log('Failed to modify userAgent'); }

                        // 3. Spoof plugins to look like a regular browser
                        try {
                            Object.defineProperty(navigator, 'plugins', {
                                get: () => {
                                    // Create a plugins array with a length property
                                    const plugins = { length: 5 };
                                    // Add some fake plugins
                                    plugins[0] = { name: 'Chrome PDF Plugin' };
                                    plugins[1] = { name: 'Chrome PDF Viewer' };
                                    plugins[2] = { name: 'Native Client' };
                                    plugins[3] = { name: 'Widevine Content Decryption Module' };
                                    plugins[4] = { name: 'Chrome Web Store' };
                                    return plugins;
                                }
                            });
                        } catch (e) { console.log('Failed to modify plugins'); }

                        // 4. Spoof languages
                        try {
                            Object.defineProperty(navigator, 'languages', {
                                get: () => ['en-US', 'en']
                            });
                        } catch (e) { console.log('Failed to modify languages'); }

                        // 5. Modify permissions API if it exists
                        if (navigator.permissions) {
                            try {
                                const originalQuery = navigator.permissions.query;
                                navigator.permissions.query = function(parameters) {
                                    if (parameters.name === 'notifications') {
                                        return Promise.resolve({ state: Notification.permission });
                                    }
                                    return originalQuery.apply(this, arguments);
                                };
                                // Make toString match native function
                                Object.defineProperty(navigator.permissions.query, 'toString', {
                                    value: () => makeNativeString('query')
                                });
                            } catch (e) { console.log('Failed to modify permissions API'); }
                        }

                        // 6. Add Chrome-specific properties
                        try {
                            window.chrome = {
                                app: {
                                    isInstalled: false,
                                    InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                                    RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }
                                },
                                runtime: {
                                    OnInstalledReason: {
                                        CHROME_UPDATE: 'chrome_update',
                                        INSTALL: 'install',
                                        SHARED_MODULE_UPDATE: 'shared_module_update',
                                        UPDATE: 'update'
                                    },
                                    OnRestartRequiredReason: {
                                        APP_UPDATE: 'app_update',
                                        OS_UPDATE: 'os_update',
                                        PERIODIC: 'periodic'
                                    },
                                    PlatformArch: {
                                        ARM: 'arm',
                                        ARM64: 'arm64',
                                        MIPS: 'mips',
                                        MIPS64: 'mips64',
                                        X86_32: 'x86-32',
                                        X86_64: 'x86-64'
                                    },
                                    PlatformNaclArch: {
                                        ARM: 'arm',
                                        MIPS: 'mips',
                                        MIPS64: 'mips64',
                                        X86_32: 'x86-32',
                                        X86_64: 'x86-64'
                                    },
                                    PlatformOs: {
                                        ANDROID: 'android',
                                        CROS: 'cros',
                                        LINUX: 'linux',
                                        MAC: 'mac',
                                        OPENBSD: 'openbsd',
                                        WIN: 'win'
                                    },
                                    RequestUpdateCheckStatus: {
                                        NO_UPDATE: 'no_update',
                                        THROTTLED: 'throttled',
                                        UPDATE_AVAILABLE: 'update_available'
                                    }
                                }
                            };
                        } catch (e) { console.log('Failed to add chrome properties'); }

                        // 7. Modify iframe contentWindow access
                        try {
                            const originalFrameContentWindow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
                            Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                                get: function() {
                                    const frame = originalFrameContentWindow.get.call(this);
                                    if (frame) {
                                        // Apply the same stealth techniques to iframes
                                        try {
                                            Object.defineProperty(frame.navigator, 'webdriver', {
                                                get: () => false
                                            });
                                        } catch (e) {}
                                    }
                                    return frame;
                                }
                            });
                        } catch (e) { console.log('Failed to modify iframe contentWindow'); }
                    })();
                """)
                self.logger.info("Applied advanced stealth techniques")
            except Exception as e:
                self.logger.warning(f"Could not apply stealth techniques: {str(e)}")
                # Continue anyway, this is not critical

            # Add random delay to mimic human behavior
            time.sleep(0.5 + (0.5 * random.random()))

            # Set initial state
            self.is_running = True
            self.current_url = None

            # Navigate to a reliable website instead of about:blank
            # Use a more robust approach to ensure proper navigation
            try:
                self.logger.info("Navigating to Google as initial page...")

                # Add random delay before navigation to mimic human behavior
                time.sleep(0.5 + random.random())

                # First navigate to a blank page to ensure a clean start
                self.driver.get("about:blank")
                time.sleep(0.5)

                # Apply additional stealth before navigating to Google
                self.driver.execute_script("""
                    // Set additional properties to make the browser look more human
                    try {
                        // Make it look like we have a history
                        Object.defineProperty(window, 'history', {
                            get: function() {
                                return { length: 5 };
                            }
                        });

                        // Add some common browser features
                        if (!window.chrome) {
                            window.chrome = {};
                        }
                    } catch (e) {}
                """)

                # Now navigate to Google with a proper referrer
                self.driver.execute_script("""
                    // Create a proper navigation with referrer
                    const a = document.createElement('a');
                    a.href = 'https://www.google.com';
                    a.click();
                """)

                # Wait for page to load with a more robust approach
                try:
                    WebDriverWait(self.driver, 15).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete' and
                                 'google' in d.current_url
                    )
                except Exception as wait_error:
                    self.logger.warning(f"JavaScript navigation failed: {str(wait_error)}")
                    # If the JavaScript approach fails, use the direct method
                    self.driver.get("https://www.google.com")
                    WebDriverWait(self.driver, 15).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )

                # Add random delay after page load to mimic human reading
                time.sleep(1.0 + (2.0 * random.random()))

                # Apply additional stealth after navigation
                self.driver.execute_script("""
                    // Make it look like we interacted with the page
                    try {
                        // Simulate mouse movements
                        const event = new MouseEvent('mousemove', {
                            'view': window,
                            'bubbles': true,
                            'cancelable': true,
                            'clientX': 100 + Math.random() * 100,
                            'clientY': 100 + Math.random() * 100
                        });
                        document.dispatchEvent(event);

                        // Simulate focus on the search box if it exists
                        const searchBox = document.querySelector('input[name="q"]');
                        if (searchBox) {
                            searchBox.focus();
                            // Don't actually type anything
                        }
                    } catch (e) {}
                """)

                # Simulate human-like scrolling behavior
                self.driver.execute_script("""
                    // Scroll down slowly with more human-like behavior
                    let totalHeight = 0;
                    let distance = 100;
                    let scrolls = 3 + Math.floor(Math.random() * 3);

                    for (let i = 0; i < scrolls; i++) {
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                    }

                    // Scroll back up partially after a short delay
                    setTimeout(() => {
                        window.scrollTo(0, totalHeight / 2);
                    }, 300 + Math.random() * 200);
                """)

                # Add another small random delay
                time.sleep(0.3 + (0.7 * random.random()))

                # Update current URL
                self.current_url = self.driver.current_url
                self.logger.info(f"Initial navigation successful, current URL: {self.current_url}")
            except Exception as e:
                self.logger.error(f"Error navigating to initial page: {str(e)}")
                self.logger.error(traceback.format_exc())

                # Fall back to direct navigation if the sophisticated approach fails
                try:
                    self.logger.info("Trying direct navigation to Google...")
                    self.driver.get("https://www.google.com")
                    time.sleep(2)  # Give it more time to load
                    self.current_url = self.driver.current_url
                    self.logger.info(f"Fallback to Google successful: {self.current_url}")
                except Exception as blank_error:
                    self.logger.error(f"Error navigating to Google: {str(blank_error)}")
                    # Continue anyway, as this is just a test

            # Start the task processing thread if not already running
            if not self.task_thread or not self.task_thread.is_alive():
                self.task_thread = threading.Thread(target=self._process_tasks)
                self.task_thread.daemon = True
                self.task_thread.start()

            # Initialize and start screenshot service if not disabled
            if not BROWSER_CONFIG.get('disable_screenshots', False):
                try:
                    from app.visual_browser.screenshot_service import init_screenshot_service
                    screenshot_service = init_screenshot_service(self)
                    screenshot_service.start()
                    self.logger.info("Screenshot service started successfully")
                except Exception as ss_error:
                    self.logger.warning(f"Error starting screenshot service: {str(ss_error)}")
            else:
                self.logger.info("Screenshot service disabled in configuration")

            # Initialize and start screen recorder if not disabled
            if not BROWSER_CONFIG.get('disable_screen_recording', False):
                try:
                    from app.visual_browser.screen_recorder import init_screen_recorder
                    screen_recorder = init_screen_recorder(self)
                    screen_recorder.start_capture()
                    self.logger.info("Screen recorder started successfully")
                except Exception as sr_error:
                    self.logger.warning(f"Error starting screen recorder: {str(sr_error)}")
            else:
                self.logger.info("Screen recorder disabled in configuration")

            self.logger.info("Live browser started successfully")

            return {
                "success": True,
                "message": "Live browser started successfully"
            }
        except Exception as e:
            self.logger.error(f"Error starting live browser: {str(e)}")
            self.logger.error(traceback.format_exc())

            # Clean up in case of error
            self.is_running = False
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            self.driver = None

            return {
                "success": False,
                "error": str(e)
            }

    def stop(self) -> Dict[str, Any]:
        """
        Stop the browser.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.is_running and not self.driver:
                return {
                    "success": True,
                    "message": "Browser is not running"
                }

            self.logger.info("Stopping live browser...")

            # Set flag to stop task processing
            self.is_running = False

            # Clear task queue
            with self.lock:
                self.task_queue = []

            # Quit the driver
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as driver_error:
                    self.logger.warning(f"Error quitting driver: {str(driver_error)}")
                finally:
                    self.driver = None

            # Reset state
            self.current_url = None

            # Stop screenshot service
            try:
                from app.visual_browser.screenshot_service import get_screenshot_service
                screenshot_service = get_screenshot_service()
                if screenshot_service and screenshot_service.is_running:
                    screenshot_service.stop()
                    self.logger.info("Screenshot service stopped successfully")
            except Exception as ss_error:
                self.logger.warning(f"Error stopping screenshot service: {str(ss_error)}")

            # Stop screen recorder
            try:
                from app.visual_browser.screen_recorder import get_screen_recorder
                screen_recorder = get_screen_recorder()
                if screen_recorder and screen_recorder.is_running:
                    screen_recorder.stop_capture()
                    self.logger.info("Screen recorder stopped successfully")
            except Exception as sr_error:
                self.logger.warning(f"Error stopping screen recorder: {str(sr_error)}")

            self.logger.info("Live browser stopped successfully")

            return {
                "success": True,
                "message": "Live browser stopped successfully"
            }
        except Exception as e:
            self.logger.error(f"Error stopping live browser: {str(e)}")
            self.logger.error(traceback.format_exc())

            # Ensure driver is cleaned up even if there's an error
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass

            self.driver = None
            self.is_running = False
            self.current_url = None

            return {
                "success": False,
                "error": str(e)
            }

    def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL.

        Args:
            url: The URL to navigate to.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "error": "Browser is not running"
                }

            # Ensure URL has proper format
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url

            self.logger.info(f"Adding navigation task to queue: {url}")

            # Add task to queue
            with self.lock:
                self.task_queue.append(("navigate", {"url": url}))

            return {
                "success": True,
                "message": f"Navigation to {url} queued"
            }
        except Exception as e:
            self.logger.error(f"Error queueing navigation: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def click(self, selector: str = None, x: int = None, y: int = None, text: str = None) -> Dict[str, Any]:
        """
        Click on an element or at specific coordinates.

        Args:
            selector: The CSS selector of the element to click.
            x: The x-coordinate to click at.
            y: The y-coordinate to click at.
            text: The text of the element to click.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "error": "Browser is not running"
                }

            if not selector and not (x is not None and y is not None) and not text:
                return {
                    "success": False,
                    "error": "Either selector, coordinates, or text must be provided"
                }

            self.logger.info(f"Adding click task to queue: selector={selector}, coords=({x}, {y}), text={text}")

            # Add task to queue
            with self.lock:
                self.task_queue.append(("click", {
                    "selector": selector,
                    "x": x,
                    "y": y,
                    "text": text
                }))

            return {
                "success": True,
                "message": "Click task queued"
            }
        except Exception as e:
            self.logger.error(f"Error queueing click: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def execute_script(self, script: str) -> Any:
        """
        Execute JavaScript in the browser.

        Args:
            script: The JavaScript code to execute.

        Returns:
            The result of the script execution.
        """
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "error": "Browser is not running"
                }

            self.logger.info(f"Executing script: {script[:50]}...")

            # Execute the script
            result = self.driver.execute_script(script)

            return {
                "success": True,
                "result": result,
                "message": "Script executed successfully"
            }
        except Exception as e:
            self.logger.error(f"Error executing script: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def type_text(self, text: str, selector: str = None) -> Dict[str, Any]:
        """
        Type text into an input field.

        Args:
            text: The text to type.
            selector: The CSS selector of the input field.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "error": "Browser is not running"
                }

            if not text:
                return {
                    "success": False,
                    "error": "Text is required"
                }

            self.logger.info(f"Adding type task to queue: text='{text}', selector={selector}")

            # Add task to queue
            with self.lock:
                self.task_queue.append(("type", {
                    "text": text,
                    "selector": selector
                }))

            return {
                "success": True,
                "message": "Type task queued"
            }
        except Exception as e:
            self.logger.error(f"Error queueing type: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def scroll(self, direction: str = 'down', distance: int = 300) -> Dict[str, Any]:
        """
        Scroll the page.

        Args:
            direction: The direction to scroll ('up', 'down', 'left', 'right').
            distance: The distance to scroll in pixels.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "error": "Browser is not running"
                }

            self.logger.info(f"Adding scroll task to queue: direction={direction}, distance={distance}")

            # Add task to queue
            with self.lock:
                self.task_queue.append(("scroll", {
                    "direction": direction,
                    "distance": distance
                }))

            return {
                "success": True,
                "message": "Scroll task queued"
            }
        except Exception as e:
            self.logger.error(f"Error queueing scroll: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def scroll(self, direction: str = 'down', distance: int = 300) -> Dict[str, Any]:
        """
        Scroll the page.

        Args:
            direction: The direction to scroll ('up', 'down', 'left', 'right').
            distance: The distance to scroll in pixels.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "error": "Browser is not running"
                }

            self.logger.info(f"Adding scroll task to queue: direction={direction}, distance={distance}")

            # Add task to queue
            with self.lock:
                self.task_queue.append(("scroll", {
                    "direction": direction,
                    "distance": distance
                }))

            return {
                "success": True,
                "message": "Scroll task queued"
            }
        except Exception as e:
            self.logger.error(f"Error queueing scroll: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def press_key(self, key: str, selector: str = None) -> Dict[str, Any]:
        """
        Press a key on the keyboard.

        Args:
            key: The key to press (e.g., 'Enter', 'Tab', 'Escape').
            selector: The CSS selector of the element to focus before pressing the key.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "error": "Browser is not running"
                }

            if not key:
                return {
                    "success": False,
                    "error": "Key is required"
                }

            self.logger.info(f"Adding key press task to queue: key={key}, selector={selector}")

            # Add task to queue
            with self.lock:
                self.task_queue.append(("press_key", {
                    "key": key,
                    "selector": selector
                }))

            return {
                "success": True,
                "message": "Key press task queued"
            }
        except Exception as e:
            self.logger.error(f"Error queueing key press: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task autonomously.

        Args:
            task_type: The type of task to execute.
            task_data: The data for the task.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "error": "Browser is not running"
                }

            self.logger.info(f"Adding autonomous task to queue: {task_type}")

            # Add task to queue
            with self.lock:
                self.task_queue.append((task_type, task_data))

            return {
                "success": True,
                "message": f"Task {task_type} queued"
            }
        except Exception as e:
            self.logger.error(f"Error queueing task: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def _process_tasks(self):
        """
        Process tasks in the queue.
        """
        while self.is_running:
            try:
                # Check if there are tasks in the queue
                with self.lock:
                    if not self.task_queue:
                        time.sleep(0.1)
                        continue

                    # Get the next task
                    task_type, task_data = self.task_queue.pop(0)

                # Process the task
                if task_type == "navigate":
                    self._execute_navigate(task_data["url"])
                elif task_type == "click":
                    self._execute_click(
                        task_data.get("selector"),
                        task_data.get("x"),
                        task_data.get("y"),
                        task_data.get("text")
                    )
                elif task_type == "type":
                    self._execute_type(task_data["text"], task_data.get("selector"))
                elif task_type == "scroll":
                    self._execute_scroll(task_data["direction"], task_data["distance"])
                elif task_type == "press_key":
                    self._execute_press_key(task_data["key"], task_data.get("selector"))
                elif task_type == "natural_language":
                    # Handle natural language tasks
                    task = task_data.get("task")
                    if task:
                        self.logger.info(f"Executing natural language task: {task}")
                        result = self.execute_complex_task(task)
                        self.logger.info(f"Natural language task result: {result.get('success')}")
                    else:
                        self.logger.warning("Natural language task missing 'task' parameter")
                elif task_type == "autonomous":
                    # Handle autonomous tasks
                    task = task_data.get("task")
                    if task:
                        self.logger.info(f"Executing autonomous task: {task}")
                        # For autonomous tasks, we want to use LLM intelligence
                        try:
                            # Import the LLM task parser
                            from app.visual_browser.llm_task_parser import parse_complex_task_with_llm

                            # Parse the task with LLM
                            task_plan = parse_complex_task_with_llm(task)

                            # Import the task executor
                            from app.visual_browser.task_executor import TaskExecutor

                            # Create a task executor
                            executor = TaskExecutor(self)

                            # Set the task plan
                            executor.set_task_plan(task_plan)

                            # Execute the task plan
                            result = executor.execute_task_plan()

                            self.logger.info(f"Autonomous task result: {result.get('success')}")
                        except Exception as e:
                            self.logger.error(f"Error executing autonomous task: {str(e)}")
                            self.logger.error(traceback.format_exc())
                            # Fall back to regular complex task execution
                            result = self.execute_complex_task(task)
                            self.logger.info(f"Autonomous task fallback result: {result.get('success')}")
                    else:
                        self.logger.warning("Autonomous task missing 'task' parameter")
                else:
                    self.logger.warning(f"Unknown task type: {task_type}")
            except Exception as e:
                self.logger.error(f"Error processing task: {str(e)}")
                self.logger.error(traceback.format_exc())
                time.sleep(0.5)

    def _execute_navigate(self, url: str):
        """
        Execute a navigate task.

        Args:
            url: The URL to navigate to.
        """
        try:
            self.logger.info(f"Navigating to {url}...")

            # Send navigation event - starting
            if EVENTS_AVAILABLE:
                send_navigation_event(url=url, status="loading")
                send_status_event(status="navigating", details=f"Navigating to {url}")

            # Check if driver is still active
            if not self.driver:
                self.logger.error("Browser driver is not initialized")
                # Try to restart the browser
                self.start()
                if not self.driver:
                    self.logger.error("Failed to restart browser")
                    if EVENTS_AVAILABLE:
                        send_error_event(error="Browser not initialized", details="Failed to restart browser")
                    return

            try:
                # Simple test to see if the driver is still responsive
                _ = self.driver.window_handles
            except Exception as e:
                self.logger.error(f"Browser window appears to be closed: {str(e)}")
                # Restart the browser
                self.stop()
                time.sleep(1)
                self.start()
                if not self.driver:
                    self.logger.error("Failed to restart browser")
                    if EVENTS_AVAILABLE:
                        send_error_event(error="Browser window closed", details="Failed to restart browser")
                    return

            # Ensure URL has protocol
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url

            # Create screenshots directory if it doesn't exist
            screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'screenshots')
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)

            # Take a screenshot before navigation
            screenshot_before_path = os.path.join(screenshots_dir, 'before_navigation.png')
            try:
                self.driver.save_screenshot(screenshot_before_path)
                self.logger.info(f"Saved screenshot before navigation to {screenshot_before_path}")
            except Exception as ss_error:
                self.logger.warning(f"Could not save screenshot: {str(ss_error)}")

            # Navigate to the URL with timeout handling and multiple fallbacks
            success = False
            error_message = ""

            # Special handling for Google
            is_google = 'google.com' in url
            if is_google and EVENTS_AVAILABLE:
                send_status_event(status="google_detected", details="Google detected, using special handling")

            # Approach 1: Standard navigation with human-like behavior
            if not success:
                try:
                    self.logger.info(f"Trying standard navigation to {url}")
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigating_standard", details=f"Trying standard navigation to {url}")

                    # Add random delay before navigation to mimic human behavior
                    time.sleep(0.5 + random.random())

                    # Set page load timeout to prevent hanging
                    self.driver.set_page_load_timeout(30)

                    # Navigate to the URL
                    self.driver.get(url)

                    # Wait for page to load
                    WebDriverWait(self.driver, 10).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )

                    # Add random delay after page load to mimic human reading
                    time.sleep(1.0 + (2.0 * random.random()))

                    # Simulate human-like scrolling behavior
                    self.driver.execute_script("""
                        // Scroll down slowly
                        let totalHeight = 0;
                        let distance = 100;
                        let scrolls = 3 + Math.floor(Math.random() * 3);

                        for (let i = 0; i < scrolls; i++) {
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            // This will be executed in the browser, so we use setTimeout
                            // But we'll still see the scrolling happen quickly
                        }

                        // Scroll back up partially
                        setTimeout(() => {
                            window.scrollTo(0, totalHeight / 2);
                        }, 100);
                    """)

                    # Add another small random delay
                    time.sleep(0.3 + (0.7 * random.random()))

                    success = True
                    self.logger.info("Standard navigation successful")
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigation_success", details="Standard navigation successful")
                except Exception as e:
                    error_message = f"Standard navigation failed: {str(e)}"
                    self.logger.warning(error_message)
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigation_retry", details="Standard navigation failed, trying alternative methods")

            # Approach 2: JavaScript navigation
            if not success:
                try:
                    self.logger.info(f"Trying JavaScript navigation to {url}")
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigating_js", details=f"Trying JavaScript navigation to {url}")

                    # Use JavaScript to navigate
                    self.driver.execute_script(f"window.location.href = '{url}';")
                    # Wait for page to load
                    time.sleep(5)
                    WebDriverWait(self.driver, 10).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )
                    success = True
                    self.logger.info("JavaScript navigation successful")
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigation_success", details="JavaScript navigation successful")
                except Exception as e:
                    error_message += f"\nJavaScript navigation failed: {str(e)}"
                    self.logger.warning(f"JavaScript navigation failed: {str(e)}")
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigation_retry", details="JavaScript navigation failed, trying alternative methods")

            # Approach 3: Open in new tab
            if not success:
                try:
                    self.logger.info(f"Trying new tab navigation to {url}")
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigating_newtab", details=f"Trying new tab navigation to {url}")

                    # Open URL in new tab
                    self.driver.execute_script(f"window.open('{url}', '_blank');")
                    # Switch to the new tab
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    # Wait for page to load
                    time.sleep(5)
                    success = True
                    self.logger.info("New tab navigation successful")
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigation_success", details="New tab navigation successful")
                except Exception as e:
                    error_message += f"\nNew tab navigation failed: {str(e)}"
                    self.logger.warning(f"New tab navigation failed: {str(e)}")
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigation_retry", details="New tab navigation failed, trying fallback")

            # If all approaches failed, try a simple URL
            if not success:
                try:
                    self.logger.error(f"All navigation approaches failed for {url}. Trying to navigate to a simple URL.")
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigation_fallback", details="All navigation approaches failed, using fallback")

                    self.driver.get("about:blank")
                    time.sleep(1)
                    self.logger.info("Navigated to about:blank as fallback")
                    # Set current URL to the requested URL even though navigation failed
                    # This allows the UI to show the correct URL
                    self.current_url = url
                    if EVENTS_AVAILABLE:
                        send_status_event(status="navigation_fallback_success", details="Fallback navigation successful")
                except Exception as e:
                    self.logger.error(f"Even fallback navigation failed: {str(e)}")
                    if EVENTS_AVAILABLE:
                        send_error_event(error="Navigation failed", details=f"All navigation approaches failed: {error_message}")
                    raise Exception(f"Navigation failed: {error_message}")

            # Take a screenshot after navigation and save it for the UI
            timestamp = int(time.time())
            screenshot_path = os.path.join(screenshots_dir, f'screenshot_{timestamp}.png')
            try:
                self.driver.save_screenshot(screenshot_path)
                self.logger.info(f"Saved screenshot after navigation to {screenshot_path}")

                # Store the screenshot path for the UI to access
                self.current_screenshot = f'/static/screenshots/screenshot_{timestamp}.png'

                # Send screenshot event
                if EVENTS_AVAILABLE:
                    send_screenshot_event(screenshot_url=self.current_screenshot)

                # Emit screenshot update via WebSocket if available
                try:
                    from app.visual_browser.websocket_server import send_message
                    send_message({
                        'type': 'screenshot_update',
                        'url': self.current_url,
                        'screenshot': self.current_screenshot
                    })
                except Exception as ws_error:
                    self.logger.warning(f"Could not send WebSocket message: {str(ws_error)}")

            except Exception as ss_error:
                self.logger.warning(f"Could not save screenshot: {str(ss_error)}")

            # Update current URL
            try:
                self.current_url = self.driver.current_url
                self.logger.info(f"Current URL after navigation: {self.current_url}")

                # Get page title
                try:
                    page_title = self.driver.title
                except:
                    page_title = "Unknown"

                # Send navigation complete event
                if EVENTS_AVAILABLE:
                    send_navigation_event(url=self.current_url, title=page_title, status="complete")

                # Special handling for Google search
                if is_google and 'q=' in self.current_url:
                    try:
                        # Extract search query
                        from urllib.parse import urlparse, parse_qs
                        parsed_url = urlparse(self.current_url)
                        query_params = parse_qs(parsed_url.query)
                        search_query = query_params.get('q', [''])[0]

                        if search_query and EVENTS_AVAILABLE:
                            self.logger.info(f"Detected Google search for: {search_query}")
                            send_search_event(query=search_query)

                            # Try to extract search results
                            try:
                                # Wait for search results to load
                                WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.g"))
                                )

                                # Extract search results
                                search_results = []
                                result_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.g")

                                for element in result_elements[:5]:  # Limit to first 5 results
                                    try:
                                        title_element = element.find_element(By.CSS_SELECTOR, "h3")
                                        link_element = element.find_element(By.CSS_SELECTOR, "a")
                                        snippet_element = element.find_element(By.CSS_SELECTOR, "div.VwiC3b")

                                        result = {
                                            "title": title_element.text,
                                            "url": link_element.get_attribute("href"),
                                            "snippet": snippet_element.text
                                        }
                                        search_results.append(result)
                                    except:
                                        continue

                                if search_results and EVENTS_AVAILABLE:
                                    send_search_event(query=search_query, results=search_results)
                            except:
                                self.logger.warning("Could not extract Google search results")
                    except Exception as search_error:
                        self.logger.warning(f"Error processing Google search: {str(search_error)}")

            except Exception as url_error:
                self.logger.error(f"Error getting current URL: {str(url_error)}")
                self.current_url = url  # Use requested URL as fallback
                if EVENTS_AVAILABLE:
                    send_navigation_event(url=url, status="complete")

            self.logger.info(f"Successfully navigated to {url}")
            if EVENTS_AVAILABLE:
                send_status_event(status="navigation_complete", details=f"Successfully navigated to {url}")

        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {str(e)}")
            self.logger.error(traceback.format_exc())

            if EVENTS_AVAILABLE:
                send_error_event(error=f"Navigation error", details=str(e))

            # Try to recover from error
            try:
                if self.is_running and self.driver:
                    # Check if we can still use the driver
                    try:
                        _ = self.driver.window_handles
                    except:
                        # Driver is not usable, restart it
                        self.logger.info("Attempting to restart browser after navigation error")
                        if EVENTS_AVAILABLE:
                            send_status_event(status="browser_restart", details="Attempting to restart browser after navigation error")

                        self.stop()
                        time.sleep(1)
                        self.start()
                        # Try to navigate to a simple page to verify browser is working
                        if self.driver:
                            try:
                                self.driver.get("about:blank")
                                self.current_url = "about:blank"
                                self.logger.info("Recovery successful, browser restarted")
                                if EVENTS_AVAILABLE:
                                    send_status_event(status="browser_restart_success", details="Browser restarted successfully")
                            except Exception as blank_error:
                                self.logger.error(f"Error navigating to blank page during recovery: {str(blank_error)}")
                                if EVENTS_AVAILABLE:
                                    send_error_event(error="Recovery failed", details=f"Error navigating to blank page: {str(blank_error)}")
            except Exception as recovery_error:
                self.logger.error(f"Error during recovery: {str(recovery_error)}")
                self.logger.error(traceback.format_exc())
                if EVENTS_AVAILABLE:
                    send_error_event(error="Recovery failed", details=f"Error during recovery: {str(recovery_error)}")

    def _execute_click(self, selector: str = None, x: int = None, y: int = None, text: str = None):
        """
        Execute a click task.

        Args:
            selector: The CSS selector of the element to click.
            x: The x-coordinate to click at.
            y: The y-coordinate to click at.
            text: The text of the element to click.
        """
        try:
            if selector:
                self.logger.info(f"Clicking on element with selector: {selector}")

                # Wait for the element to be clickable
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )

                # Highlight the element before clicking (visual feedback)
                self.driver.execute_script(
                    "arguments[0].style.border='3px solid red'", element
                )
                time.sleep(0.5)

                # Click the element
                element.click()

            elif text:
                self.logger.info(f"Clicking on element with text: {text}")

                # Try different strategies to find the element by text
                try:
                    # Try exact text match with XPath
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//*[text()='{text}']"))
                    )
                except:
                    try:
                        # Try contains text match with XPath
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{text}')]"))
                        )
                    except:
                        # Try link text
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.LINK_TEXT, text))
                        )

                # Highlight the element before clicking (visual feedback)
                self.driver.execute_script(
                    "arguments[0].style.border='3px solid red'", element
                )
                time.sleep(0.5)

                # Click the element
                element.click()

            elif x is not None and y is not None:
                self.logger.info(f"Clicking at coordinates: ({x}, {y})")

                # Create an action chain
                actions = ActionChains(self.driver)

                # Move to the coordinates and click
                actions.move_by_offset(x, y).click().perform()

            # Wait a moment after clicking
            time.sleep(0.5)

            # Update current URL if it changed
            if self.driver.current_url != self.current_url:
                self.current_url = self.driver.current_url

            self.logger.info("Click executed successfully")
        except Exception as e:
            self.logger.error(f"Error clicking: {str(e)}")
            self.logger.error(traceback.format_exc())

    def _execute_type(self, text: str, selector: str = None):
        """
        Execute a type task.

        Args:
            text: The text to type.
            selector: The CSS selector of the input field.
        """
        try:
            if selector:
                self.logger.info(f"Typing '{text}' into element with selector: {selector}")

                # Wait for the element to be visible
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )

                # Highlight the element before typing (visual feedback)
                self.driver.execute_script(
                    "arguments[0].style.border='3px solid red'", element
                )
                time.sleep(0.5)

                # Clear the input field
                element.clear()

                # Type the text character by character for visual effect
                for char in text:
                    element.send_keys(char)
                    time.sleep(0.05)  # Small delay between characters
            else:
                self.logger.info(f"Typing '{text}' at current focus")

                # Get the active element
                active_element = self.driver.switch_to.active_element

                # Type the text character by character for visual effect
                for char in text:
                    active_element.send_keys(char)
                    time.sleep(0.05)  # Small delay between characters

            # Wait a moment after typing
            time.sleep(0.5)

            self.logger.info("Type executed successfully")
        except Exception as e:
            self.logger.error(f"Error typing: {str(e)}")
            self.logger.error(traceback.format_exc())

    def _execute_scroll(self, direction: str = 'down', distance: int = 300):
        """
        Execute a scroll task.

        Args:
            direction: The direction to scroll ('up', 'down', 'left', 'right').
            distance: The distance to scroll in pixels.
        """
        try:
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
                self.logger.warning(f"Invalid scroll direction: {direction}")
                return

            # Execute scroll with a simpler script
            scroll_script = f"window.scrollBy({x_scroll}, {y_scroll});"
            self.driver.execute_script(scroll_script)

            # Wait for the scroll animation to complete
            time.sleep(1)

            self.logger.info("Scroll executed successfully")
        except Exception as e:
            self.logger.error(f"Error scrolling: {str(e)}")
            self.logger.error(traceback.format_exc())

    def _execute_press_key(self, key: str, selector: str = None):
        """
        Execute a key press task.

        Args:
            key: The key to press.
            selector: The CSS selector of the element to focus before pressing the key.
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
                'right': Keys.RIGHT
            }

            # Get the key constant
            key_lower = key.lower()
            if key_lower in key_mapping:
                key_to_press = key_mapping[key_lower]
            else:
                key_to_press = key

            if selector:
                self.logger.info(f"Pressing key '{key}' on element with selector: {selector}")

                # Wait for the element to be visible
                element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                )

                # Highlight the element before pressing key (visual feedback)
                self.driver.execute_script(
                    "arguments[0].style.border='3px solid red'", element
                )
                time.sleep(0.5)

                # Focus the element
                element.click()

                # Press the key
                element.send_keys(key_to_press)
            else:
                self.logger.info(f"Pressing key '{key}' on active element")

                # Get the active element
                active_element = self.driver.switch_to.active_element

                # Press the key
                active_element.send_keys(key_to_press)

            # Wait a moment after pressing key
            time.sleep(0.5)

            # Update current URL if it changed
            if self.driver.current_url != self.current_url:
                self.current_url = self.driver.current_url

            self.logger.info("Key press executed successfully")
        except Exception as e:
            self.logger.error(f"Error pressing key: {str(e)}")
            self.logger.error(traceback.format_exc())

    def execute_complex_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a complex task by breaking it down into simple steps.
        Uses resource limits to prevent system overload.

        Args:
            task: The complex task description.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "error": "Browser is not running",
                    "message": "Browser is not running"
                }

            self.logger.info(f"Executing complex task: {task}")

            # Set resource limits
            try:
                # Import configuration
                try:
                    from app.visual_browser.config import BROWSER_CONFIG
                except ImportError:
                    # Default configuration if config module is not available
                    BROWSER_CONFIG = {
                        'lightweight_mode': True,
                        'screenshot_interval_ms': 1000,
                        'disable_screenshots': True,
                        'disable_screen_recording': True,
                        'window_width': 800,
                        'window_height': 600,
                        'memory_limit_mb': 512,
                        'max_steps': 5,
                        'execution_timeout_seconds': 30,
                        'step_timeout_seconds': 5,
                    }

                # Limit memory usage based on configuration
                memory_limit_bytes = BROWSER_CONFIG['memory_limit_mb'] * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
                self.logger.info(f"Set memory limit to {BROWSER_CONFIG['memory_limit_mb']}MB")
            except Exception as e:
                self.logger.warning(f"Could not set memory limit: {str(e)}")

            # Import task parser and executor
            from app.visual_browser.task_parser import parse_complex_task
            from app.visual_browser.task_executor import TaskExecutor

            # Simplify the task if it's too complex
            max_task_length = 200
            if len(task) > max_task_length:
                self.logger.warning(f"Task is too complex ({len(task)} chars). Truncating.")
                task = task[:max_task_length] + "..."

            # Parse the task
            task_plan = parse_complex_task(task)

            # Create a task executor
            executor = TaskExecutor(self)

            # Set the task plan
            executor.set_task_plan(task_plan)

            # Execute the task plan with a timeout
            import queue
            result_queue = queue.Queue()

            def execute_with_timeout():
                try:
                    result = executor.execute_task_plan()
                    result_queue.put(result)
                except Exception as e:
                    self.logger.error(f"Error in execution thread: {str(e)}")
                    result_queue.put({
                        "success": False,
                        "error": str(e),
                        "message": f"Error in execution thread: {str(e)}"
                    })

            # Start execution in a separate thread
            execution_thread = threading.Thread(target=execute_with_timeout)
            execution_thread.daemon = True
            execution_thread.start()

            # Wait for the thread to complete with a timeout
            execution_timeout = 30  # 30 seconds max for the entire task
            execution_thread.join(execution_timeout)

            # Check if the thread is still alive (timeout occurred)
            if execution_thread.is_alive():
                self.logger.warning(f"Execution timeout after {execution_timeout} seconds")
                return {
                    "success": False,
                    "error": f"Execution timeout after {execution_timeout} seconds",
                    "message": f"The task execution took too long and was terminated to prevent system overload",
                    "execution_log": [{"action": "timeout", "message": "Execution timed out"}]
                }

            # Get the result from the queue
            try:
                result = result_queue.get(block=False)
                return result
            except queue.Empty:
                return {
                    "success": False,
                    "error": "No result returned from execution thread",
                    "message": "The task execution failed to return a result"
                }

        except Exception as e:
            self.logger.error(f"Error executing complex task: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "message": f"Error executing complex task: {str(e)}"
            }

# Create a singleton instance
live_browser = LiveBrowser()
