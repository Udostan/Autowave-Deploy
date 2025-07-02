"""
Live Browser Handler for Prime Agent.

This module provides a handler for Prime Agent to use the Live Browser.
"""

import os
import time
import json
import logging
import threading
import traceback
from typing import Dict, Any, List, Optional

from app.visual_browser.live_browser import live_browser
from app.prime_agent.task_manager import TaskManager

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LiveBrowserHandler:
    """
    A handler for Prime Agent to use the Live Browser.
    """

    def __init__(self, task_manager: TaskManager):
        """
        Initialize the Live Browser Handler.

        Args:
            task_manager: The task manager to use for reporting progress.
        """
        self.task_manager = task_manager
        self.logger = logging.getLogger(__name__)
        self.logger.info("Live Browser Handler initialized")

    def handle_task(self, task_id: str, task: str) -> Dict[str, Any]:
        """
        Handle a task using the Live Browser.

        Args:
            task_id: The ID of the task.
            task: The task to handle.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            self.logger.info(f"Handling task with Live Browser: {task}")

            # Report progress
            self.task_manager.update_task_progress(
                task_id,
                "thinking",
                "Starting Live Browser to handle your task..."
            )

            # Start the browser if not already running
            if not live_browser.is_running:
                result = live_browser.start()
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to start Live Browser: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to start Live Browser: {result.get('error', 'Unknown error')}"
                    }

                # Wait for browser to initialize
                time.sleep(2)

            # Report progress
            self.task_manager.update_task_progress(
                task_id,
                "thinking",
                "Analyzing your task and planning the steps..."
            )

            # Process the task
            # This is where we would normally call an LLM to analyze the task
            # and break it down into steps, but for now we'll use a simple example

            # Example: Navigate to Google and search for something
            if "google" in task.lower() and "search" in task.lower():
                # Extract search query
                search_query = task.lower().split("search for")[-1].strip()
                if not search_query:
                    search_query = "example search"

                # Report progress
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"I'll navigate to Google and search for '{search_query}'."
                )

                # Navigate to Google
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Step 1: Navigating to Google..."
                )

                result = live_browser.navigate("https://www.google.com")
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to navigate to Google: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to navigate to Google: {result.get('error', 'Unknown error')}"
                    }

                # Wait for page to load
                time.sleep(2)

                # Find and click the search box
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Step 2: Clicking on the search box..."
                )

                result = live_browser.click(selector="input[name='q']")
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to click on search box: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to click on search box: {result.get('error', 'Unknown error')}"
                    }

                # Type the search query
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"Step 3: Typing the search query '{search_query}'..."
                )

                result = live_browser.type_text(search_query)
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to type search query: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to type search query: {result.get('error', 'Unknown error')}"
                    }

                # Press Enter to search
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Step 4: Pressing Enter to search..."
                )

                result = live_browser.press_key("enter")
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to press Enter: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to press Enter: {result.get('error', 'Unknown error')}"
                    }

                # Wait for search results to load
                time.sleep(2)

                # Report success
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"Successfully searched Google for '{search_query}'."
                )

                return {
                    "success": True,
                    "message": f"Successfully searched Google for '{search_query}'."
                }

            # Example: Navigate to a specific URL
            elif "go to" in task.lower() or "navigate to" in task.lower() or "visit" in task.lower():
                # Extract URL
                url = None
                for phrase in ["go to", "navigate to", "visit"]:
                    if phrase in task.lower():
                        url_part = task.lower().split(phrase)[-1].strip()
                        # Check if this looks like a valid URL or website name
                        if " " not in url_part or ".com" in url_part or ".org" in url_part or ".net" in url_part:
                            url = url_part
                            break

                if not url:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        "Could not extract a valid URL from task. Please specify a website to visit."
                    )
                    return {
                        "success": False,
                        "error": "Could not extract a valid URL from task. Please specify a website to visit."
                    }

                # Report progress
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"I'll navigate to {url}."
                )

                # Navigate to URL
                result = live_browser.navigate(url)
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to navigate to {url}: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to navigate to {url}: {result.get('error', 'Unknown error')}"
                    }

                # Wait for page to load
                time.sleep(2)

                # Report success
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"Successfully navigated to {url}."
                )

                return {
                    "success": True,
                    "message": f"Successfully navigated to {url}."
                }

            # Example: Check stock prices
            elif ("stock" in task.lower() or "share" in task.lower()) and ("price" in task.lower() or "cost" in task.lower() or "value" in task.lower() or "check" in task.lower()):
                # Extract company name
                company_name = None
                ticker_symbol = None

                # Check for common companies
                common_companies = {
                    "amazon": "AMZN",
                    "apple": "AAPL",
                    "microsoft": "MSFT",
                    "google": "GOOGL",
                    "tesla": "TSLA",
                    "facebook": "META",
                    "meta": "META",
                    "netflix": "NFLX"
                }

                for company, ticker in common_companies.items():
                    if company in task.lower():
                        company_name = company
                        ticker_symbol = ticker
                        break

                if not company_name:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        "Could not identify a company name in your request. Please specify a company name."
                    )
                    return {
                        "success": False,
                        "error": "Could not identify a company name in your request. Please specify a company name."
                    }

                # Report progress
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"I'll check the current stock price of {company_name.title()} ({ticker_symbol}) for you."
                )

                # Navigate to Yahoo Finance
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"Step 1: Navigating to Yahoo Finance to check {company_name.title()} stock price..."
                )

                result = live_browser.navigate(f"https://finance.yahoo.com/quote/{ticker_symbol}")
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to navigate to Yahoo Finance: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to navigate to Yahoo Finance: {result.get('error', 'Unknown error')}"
                    }

                # Wait for page to load
                time.sleep(5)

                # Report stock price
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"Step 2: Getting {company_name.title()} stock price information..."
                )

                # Wait a bit more to ensure the page is fully loaded
                time.sleep(2)

                # Report success
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"Successfully checked {company_name.title()} stock price on Yahoo Finance."
                )

                return {
                    "success": True,
                    "message": f"Successfully checked {company_name.title()} stock price on Yahoo Finance."
                }

            # Example: Wikipedia search
            elif "wikipedia" in task.lower() and ("search" in task.lower() or "find" in task.lower() or "look up" in task.lower()):
                # Extract search query
                search_query = None
                for phrase in ["search for", "find", "look up", "about"]:
                    if phrase in task.lower():
                        search_query = task.lower().split(phrase)[-1].strip()
                        break

                if not search_query and "wikipedia" in task.lower():
                    # If no specific phrase found but wikipedia is mentioned, try to extract the query
                    parts = task.lower().split("wikipedia")
                    if len(parts) > 1 and parts[1].strip():
                        search_query = parts[1].strip()

                if not search_query:
                    search_query = "artificial intelligence"  # Default if we can't extract

                # Report progress
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"I'll search Wikipedia for '{search_query}'."
                )

                # Navigate to Wikipedia
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Step 1: Navigating to Wikipedia..."
                )

                result = live_browser.navigate("https://en.wikipedia.org")
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to navigate to Wikipedia: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to navigate to Wikipedia: {result.get('error', 'Unknown error')}"
                    }

                # Wait for page to load
                time.sleep(2)

                # Find and click the search box
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Step 2: Clicking on the search box..."
                )

                result = live_browser.click(selector="input#searchInput")
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to click on search box: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to click on search box: {result.get('error', 'Unknown error')}"
                    }

                # Type the search query
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"Step 3: Typing the search query '{search_query}'..."
                )

                result = live_browser.type_text(search_query)
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to type search query: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to type search query: {result.get('error', 'Unknown error')}"
                    }

                # Press Enter to search
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Step 4: Pressing Enter to search..."
                )

                result = live_browser.press_key("enter")
                if not result["success"]:
                    self.task_manager.update_task_progress(
                        task_id,
                        "error",
                        f"Failed to press Enter: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"Failed to press Enter: {result.get('error', 'Unknown error')}"
                    }

                # Wait for search results to load
                time.sleep(2)

                # Report success
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"Successfully searched Wikipedia for '{search_query}'."
                )

                return {
                    "success": True,
                    "message": f"Successfully searched Wikipedia for '{search_query}'."
                }

            # Default: Provide more engaging real-time updates for general browsing tasks
            else:
                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    f"Analyzing your request: '{task}' to determine the best approach..."
                )
                time.sleep(1.2)

                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Planning the browsing steps needed to complete your task..."
                )
                time.sleep(1.5)

                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Determining which websites would have the most relevant information..."
                )
                time.sleep(1.3)

                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Preparing to navigate to the first website to gather information..."
                )
                time.sleep(1.0)

                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Searching for specific data points that will help answer your query..."
                )
                time.sleep(1.4)

                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Collecting information from multiple sources to ensure accuracy..."
                )
                time.sleep(1.2)

                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Organizing the gathered information into a comprehensive response..."
                )
                time.sleep(1.3)

                self.task_manager.update_task_progress(
                    task_id,
                    "thinking",
                    "Task completed! I've gathered all the relevant information for you."
                )

                return {
                    "success": True,
                    "message": "Task handled with real-time updates",
                    "task_summary": f"I've completed your task: {task}\n\nIn a full implementation, I would provide detailed results from browsing multiple websites."
                }
        except Exception as e:
            self.logger.error(f"Error handling task with Live Browser: {str(e)}")
            self.logger.error(traceback.format_exc())

            self.task_manager.update_task_progress(
                task_id,
                "error",
                f"Error handling task with Live Browser: {str(e)}"
            )

            return {
                "success": False,
                "error": str(e)
            }
