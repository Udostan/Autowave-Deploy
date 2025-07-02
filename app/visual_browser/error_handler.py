"""
Error handler for the Live Browser.

This module provides error handling functionality for the Live Browser.
"""

import logging
import traceback
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ErrorHandler:
    """
    Error handler for the Live Browser.
    Provides error recovery strategies for common browser automation errors.
    """

    def __init__(self, live_browser):
        """
        Initialize the Error Handler.

        Args:
            live_browser: The Live Browser instance to use for error recovery.
        """
        self.live_browser = live_browser
        self.logger = logging.getLogger(__name__)

    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an error that occurred during browser automation.

        Args:
            error: The exception that was raised.
            context: Additional context about the error (e.g., action, selector).

        Returns:
            Dict containing the result of error handling.
        """
        error_type = type(error).__name__
        error_message = str(error)
        action = context.get('action', 'unknown')
        
        self.logger.error(f"Error during {action}: {error_type}: {error_message}")
        self.logger.error(traceback.format_exc())

        # Handle different types of errors
        if "no such element" in error_message.lower():
            return self._handle_no_such_element(error, context)
        elif "element not interactable" in error_message.lower():
            return self._handle_element_not_interactable(error, context)
        elif "timeout" in error_message.lower():
            return self._handle_timeout(error, context)
        elif "stale element reference" in error_message.lower():
            return self._handle_stale_element(error, context)
        elif "element click intercepted" in error_message.lower():
            return self._handle_click_intercepted(error, context)
        elif "invalid selector" in error_message.lower():
            return self._handle_invalid_selector(error, context)
        elif "no such window" in error_message.lower():
            return self._handle_no_such_window(error, context)
        else:
            return self._handle_generic_error(error, context)

    def _handle_no_such_element(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'no such element' errors by waiting and retrying with alternative selectors.
        """
        selector = context.get('selector', '')
        action = context.get('action', 'unknown')
        
        self.logger.info(f"Handling 'no such element' error for selector: {selector}")
        
        # Try to recover by waiting for the page to load more completely
        try:
            self.logger.info("Waiting for page to load more completely...")
            self.live_browser.wait(2)
            
            # Try alternative selectors based on the original selector
            alternative_selectors = self._generate_alternative_selectors(selector)
            
            for alt_selector in alternative_selectors:
                self.logger.info(f"Trying alternative selector: {alt_selector}")
                try:
                    # Check if the element exists with the alternative selector
                    if self.live_browser.element_exists(alt_selector):
                        self.logger.info(f"Found element with alternative selector: {alt_selector}")
                        return {
                            'success': True,
                            'message': f"Recovered from 'no such element' error by using alternative selector: {alt_selector}",
                            'alternative_selector': alt_selector
                        }
                except Exception as e:
                    self.logger.warning(f"Error checking alternative selector {alt_selector}: {str(e)}")
                    continue
            
            # If we couldn't find any alternative selectors, try scrolling to reveal more content
            self.logger.info("Scrolling to reveal more content...")
            self.live_browser.scroll("down", 500)
            self.live_browser.wait(1)
            
            # Check if the original selector now exists
            if self.live_browser.element_exists(selector):
                self.logger.info(f"Found element after scrolling: {selector}")
                return {
                    'success': True,
                    'message': f"Recovered from 'no such element' error by scrolling to reveal the element"
                }
                
            return {
                'success': False,
                'message': f"Could not find element with selector: {selector}",
                'error': str(error)
            }
        except Exception as recovery_error:
            self.logger.error(f"Error during recovery attempt: {str(recovery_error)}")
            return {
                'success': False,
                'message': f"Error during recovery attempt: {str(recovery_error)}",
                'error': str(error)
            }

    def _handle_element_not_interactable(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'element not interactable' errors by scrolling to the element and retrying.
        """
        selector = context.get('selector', '')
        action = context.get('action', 'unknown')
        
        self.logger.info(f"Handling 'element not interactable' error for selector: {selector}")
        
        try:
            # Try to scroll to the element
            self.logger.info(f"Scrolling to element: {selector}")
            self.live_browser.scroll_to_element(selector)
            self.live_browser.wait(1)
            
            # Check if the element is now interactable
            if self.live_browser.element_exists(selector):
                self.logger.info(f"Element is now visible after scrolling: {selector}")
                return {
                    'success': True,
                    'message': f"Recovered from 'element not interactable' error by scrolling to the element"
                }
            
            # Try clicking with JavaScript as a fallback
            if action == 'click':
                self.logger.info(f"Attempting to click element with JavaScript: {selector}")
                self.live_browser.click_with_js(selector)
                return {
                    'success': True,
                    'message': f"Recovered from 'element not interactable' error by clicking with JavaScript"
                }
                
            return {
                'success': False,
                'message': f"Element exists but is not interactable: {selector}",
                'error': str(error)
            }
        except Exception as recovery_error:
            self.logger.error(f"Error during recovery attempt: {str(recovery_error)}")
            return {
                'success': False,
                'message': f"Error during recovery attempt: {str(recovery_error)}",
                'error': str(error)
            }

    def _handle_timeout(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle timeout errors by waiting and retrying.
        """
        action = context.get('action', 'unknown')
        
        self.logger.info(f"Handling timeout error during {action}")
        
        try:
            # Wait a bit longer and retry
            self.logger.info("Waiting for page to respond...")
            self.live_browser.wait(5)
            
            # Refresh the page as a last resort
            self.logger.info("Refreshing the page...")
            self.live_browser.refresh()
            self.live_browser.wait(3)
            
            return {
                'success': True,
                'message': f"Recovered from timeout error by refreshing the page"
            }
        except Exception as recovery_error:
            self.logger.error(f"Error during recovery attempt: {str(recovery_error)}")
            return {
                'success': False,
                'message': f"Error during recovery attempt: {str(recovery_error)}",
                'error': str(error)
            }

    def _handle_stale_element(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'stale element reference' errors by refreshing the element reference.
        """
        selector = context.get('selector', '')
        
        self.logger.info(f"Handling 'stale element reference' error for selector: {selector}")
        
        try:
            # Wait for the page to stabilize
            self.logger.info("Waiting for page to stabilize...")
            self.live_browser.wait(2)
            
            # Check if the element still exists
            if self.live_browser.element_exists(selector):
                self.logger.info(f"Element still exists after waiting: {selector}")
                return {
                    'success': True,
                    'message': f"Recovered from 'stale element reference' error by refreshing the element reference"
                }
            
            return {
                'success': False,
                'message': f"Element no longer exists in the DOM: {selector}",
                'error': str(error)
            }
        except Exception as recovery_error:
            self.logger.error(f"Error during recovery attempt: {str(recovery_error)}")
            return {
                'success': False,
                'message': f"Error during recovery attempt: {str(recovery_error)}",
                'error': str(error)
            }

    def _handle_click_intercepted(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'element click intercepted' errors by trying alternative click methods.
        """
        selector = context.get('selector', '')
        
        self.logger.info(f"Handling 'element click intercepted' error for selector: {selector}")
        
        try:
            # Try to click with JavaScript
            self.logger.info(f"Attempting to click element with JavaScript: {selector}")
            self.live_browser.click_with_js(selector)
            
            return {
                'success': True,
                'message': f"Recovered from 'element click intercepted' error by clicking with JavaScript"
            }
        except Exception as js_error:
            self.logger.warning(f"JavaScript click failed: {str(js_error)}")
            
            try:
                # Try to remove overlays that might be intercepting the click
                self.logger.info("Attempting to remove potential overlays...")
                self.live_browser.execute_js("""
                    document.querySelectorAll('div[class*="overlay"], div[class*="modal"], div[class*="popup"], div[id*="overlay"], div[id*="modal"], div[id*="popup"]').forEach(el => el.remove());
                """)
                
                # Try clicking again
                self.logger.info(f"Attempting to click element after removing overlays: {selector}")
                self.live_browser.click(selector)
                
                return {
                    'success': True,
                    'message': f"Recovered from 'element click intercepted' error by removing overlays"
                }
            except Exception as recovery_error:
                self.logger.error(f"Error during recovery attempt: {str(recovery_error)}")
                return {
                    'success': False,
                    'message': f"Error during recovery attempt: {str(recovery_error)}",
                    'error': str(error)
                }

    def _handle_invalid_selector(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'invalid selector' errors by suggesting alternative selectors.
        """
        selector = context.get('selector', '')
        
        self.logger.info(f"Handling 'invalid selector' error for selector: {selector}")
        
        # Generate alternative selectors
        alternative_selectors = self._generate_alternative_selectors(selector)
        
        for alt_selector in alternative_selectors:
            self.logger.info(f"Trying alternative selector: {alt_selector}")
            try:
                # Check if the element exists with the alternative selector
                if self.live_browser.element_exists(alt_selector):
                    self.logger.info(f"Found element with alternative selector: {alt_selector}")
                    return {
                        'success': True,
                        'message': f"Recovered from 'invalid selector' error by using alternative selector: {alt_selector}",
                        'alternative_selector': alt_selector
                    }
            except Exception as e:
                self.logger.warning(f"Error checking alternative selector {alt_selector}: {str(e)}")
                continue
        
        return {
            'success': False,
            'message': f"Invalid selector and no valid alternatives found: {selector}",
            'error': str(error)
        }

    def _handle_no_such_window(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'no such window' errors by restarting the browser.
        """
        self.logger.info("Handling 'no such window' error")
        
        try:
            # Restart the browser
            self.logger.info("Restarting the browser...")
            self.live_browser.stop()
            self.live_browser.wait(2)
            self.live_browser.start()
            self.live_browser.wait(3)
            
            return {
                'success': True,
                'message': "Recovered from 'no such window' error by restarting the browser"
            }
        except Exception as recovery_error:
            self.logger.error(f"Error during recovery attempt: {str(recovery_error)}")
            return {
                'success': False,
                'message': f"Error during recovery attempt: {str(recovery_error)}",
                'error': str(error)
            }

    def _handle_generic_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle generic errors with basic recovery strategies.
        """
        action = context.get('action', 'unknown')
        
        self.logger.info(f"Handling generic error during {action}: {str(error)}")
        
        try:
            # Wait a bit
            self.logger.info("Waiting to see if the error resolves...")
            self.live_browser.wait(3)
            
            # Refresh the page as a generic recovery strategy
            self.logger.info("Refreshing the page...")
            self.live_browser.refresh()
            self.live_browser.wait(2)
            
            return {
                'success': True,
                'message': f"Attempted recovery from error by refreshing the page"
            }
        except Exception as recovery_error:
            self.logger.error(f"Error during recovery attempt: {str(recovery_error)}")
            return {
                'success': False,
                'message': f"Error during recovery attempt: {str(recovery_error)}",
                'error': str(error)
            }

    def _generate_alternative_selectors(self, selector: str) -> list:
        """
        Generate alternative selectors based on the original selector.
        
        Args:
            selector: The original selector that failed.
            
        Returns:
            List of alternative selectors to try.
        """
        alternatives = []
        
        # Handle common selector types
        if selector.startswith('#'):
            # ID selector
            id_value = selector[1:]
            alternatives.extend([
                f"[id='{id_value}']",
                f"[id*='{id_value}']",
                f"*[id='{id_value}']"
            ])
        elif selector.startswith('.'):
            # Class selector
            class_value = selector[1:]
            alternatives.extend([
                f"[class='{class_value}']",
                f"[class*='{class_value}']",
                f"*[class*='{class_value}']"
            ])
        elif selector.startswith('['):
            # Attribute selector
            if '=' in selector:
                attr_parts = selector.strip('[]').split('=', 1)
                if len(attr_parts) == 2:
                    attr_name = attr_parts[0]
                    attr_value = attr_parts[1].strip('\'"')
                    alternatives.extend([
                        f"[{attr_name}*='{attr_value}']",
                        f"*[{attr_name}*='{attr_value}']"
                    ])
        
        # Add common element selectors for search boxes, buttons, etc.
        if 'search' in selector.lower():
            alternatives.extend([
                "input[type='search']",
                "input[name='q']",
                "input[name='query']",
                "input[id*='search']",
                "input[class*='search']",
                "textarea[name='q']"
            ])
        elif 'button' in selector.lower():
            alternatives.extend([
                "button",
                "input[type='button']",
                "input[type='submit']",
                "a[role='button']",
                "div[role='button']"
            ])
        
        # Add XPath alternatives
        if not selector.startswith('//'):
            # Convert CSS to XPath for common elements
            if selector.lower() == 'input[name="q"]' or selector.lower() == 'textarea[name="q"]':
                alternatives.append("//input[@name='q']")
                alternatives.append("//textarea[@name='q']")
            elif 'search' in selector.lower():
                alternatives.append("//input[contains(@id, 'search')]")
                alternatives.append("//input[contains(@class, 'search')]")
                alternatives.append("//input[contains(@name, 'search')]")
            elif 'button' in selector.lower():
                alternatives.append("//button")
                alternatives.append("//input[@type='button']")
                alternatives.append("//input[@type='submit']")
        
        return alternatives
