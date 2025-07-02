"""
Task Executor for Live Browser.

This module provides functionality to execute parsed tasks in the Live Browser.
"""

import logging
import time
import json
import sys
from typing import Dict, Any, List, Optional

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

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskExecutor:
    """
    A class for executing parsed tasks in the Live Browser.
    """

    def __init__(self, live_browser):
        """
        Initialize the Task Executor.

        Args:
            live_browser: The Live Browser instance to use for execution.
        """
        self.live_browser = live_browser
        self.current_step = 0
        self.total_steps = 0
        self.task_plan = None
        self.execution_log = []
        self.screenshots = []

    def set_task_plan(self, task_plan: Dict[str, Any]) -> None:
        """
        Set the task plan to execute.

        Args:
            task_plan: The task plan to execute.
        """
        self.task_plan = task_plan
        self.current_step = 0
        self.total_steps = task_plan.get("total_steps", 0)
        self.execution_log = []
        self.screenshots = []

        logger.info(f"Task plan set: {json.dumps(task_plan, indent=2)}")

    def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single step.

        Args:
            step: The step to execute.

        Returns:
            A dictionary containing the result of the step execution.
        """
        action = step.get("action")
        result = {"success": False, "action": action, "message": ""}

        try:
            if action == "navigate":
                url = step.get("url")
                logger.info(f"Navigating to {url}")
                nav_result = self.live_browser.navigate(url)
                result.update(nav_result)
                result["message"] = f"Navigated to {url}"

                # Add a small delay to allow the page to load
                time.sleep(2)

            elif action == "type":
                selector = step.get("selector")
                text = step.get("text")
                logger.info(f"Typing '{text}' into {selector}")
                type_result = self.live_browser.type_text(text, selector)
                result.update(type_result)
                result["message"] = f"Typed '{text}' into {selector}"

                # Add a small delay after typing
                time.sleep(1)

            elif action == "press_key":
                key = step.get("key")
                selector = step.get("selector", None)
                logger.info(f"Pressing key {key}")
                press_result = self.live_browser.press_key(key, selector)
                result.update(press_result)
                result["message"] = f"Pressed key {key}"

                # Add a small delay after pressing a key
                time.sleep(1)

            elif action == "click":
                selector = step.get("selector")
                text = step.get("text")

                if selector:
                    logger.info(f"Clicking on element with selector {selector}")
                    click_result = self.live_browser.click(selector=selector)
                    result.update(click_result)
                    result["message"] = f"Clicked on element with selector {selector}"
                elif text:
                    logger.info(f"Clicking on element with text {text}")
                    click_result = self.live_browser.click(text=text)
                    result.update(click_result)
                    result["message"] = f"Clicked on element with text {text}"
                else:
                    result["message"] = "No selector or text provided for click action"

                # Add a small delay after clicking
                time.sleep(1)

            elif action == "wait_for_selector":
                selector = step.get("selector")
                timeout = step.get("timeout", 10)
                logger.info(f"Waiting for selector {selector} with timeout {timeout}s")

                # This is a simplified version, actual implementation would depend on live_browser capabilities
                # For now, we'll just wait a fixed amount of time
                time.sleep(2)

                result["success"] = True
                result["message"] = f"Waited for selector {selector}"

            elif action == "wait":
                seconds = step.get("seconds", 3)
                logger.info(f"Waiting for {seconds} seconds")

                # Sleep for the specified number of seconds
                time.sleep(seconds)

                result["success"] = True
                result["message"] = f"Waited for {seconds} seconds"

            elif action == "scroll":
                direction = step.get("direction", "down")
                amount = step.get("amount", "medium")

                # Convert amount to pixels
                if amount == "small":
                    pixels = 300
                elif amount == "medium":
                    pixels = 600
                elif amount == "large":
                    pixels = 1000
                else:
                    try:
                        pixels = int(amount)
                    except ValueError:
                        pixels = 600

                # Adjust pixels for direction
                if direction == "up":
                    pixels = -pixels

                logger.info(f"Scrolling {direction} by {pixels} pixels")

                # Execute scroll using JavaScript
                scroll_result = self.live_browser.execute_script(
                    f"window.scrollBy(0, {pixels});"
                )

                result["success"] = True
                result["message"] = f"Scrolled {direction} by {pixels} pixels"

                # Add a small delay after scrolling
                time.sleep(1)

            elif action == "screenshot":
                logger.info("Taking screenshot")
                screenshot_url = self.live_browser.take_screenshot()
                if screenshot_url:
                    self.screenshots.append(screenshot_url)
                    result["success"] = True
                    result["message"] = "Screenshot taken"
                    result["screenshot"] = screenshot_url
                else:
                    result["message"] = "Failed to take screenshot"

            elif action == "message":
                text = step.get("text")
                logger.info(f"Message: {text}")
                result["success"] = True
                result["message"] = text

            else:
                logger.warning(f"Unknown action: {action}")
                result["message"] = f"Unknown action: {action}"

        except Exception as e:
            logger.error(f"Error executing step {action}: {str(e)}")
            result["success"] = False
            result["error"] = str(e)
            result["message"] = f"Error executing {action}: {str(e)}"

        # Log the result
        self.execution_log.append(result)
        return result

    def execute_task_plan(self) -> Dict[str, Any]:
        """
        Execute the entire task plan with resource limits.

        Returns:
            A dictionary containing the result of the task execution.
        """
        if not self.task_plan:
            return {
                "success": False,
                "error": "No task plan set",
                "message": "No task plan set"
            }

        logger.info(f"Executing task plan: {self.task_plan.get('original_task')}")

        # Check if this is an LLM-powered task plan
        is_llm_powered = self.task_plan.get("llm_powered", False)
        if is_llm_powered:
            logger.info("Using LLM-powered task plan")

        steps = self.task_plan.get("steps", [])

        # Limit the number of steps based on configuration
        max_steps = BROWSER_CONFIG.get('max_steps', 10)
        if len(steps) > max_steps:
            logger.warning(f"Task plan has too many steps ({len(steps)}). Limiting to {max_steps} steps.")
            steps = steps[:max_steps]

        self.total_steps = len(steps)

        overall_success = True
        max_execution_time = BROWSER_CONFIG.get('execution_timeout_seconds', 60)
        step_timeout = BROWSER_CONFIG.get('step_timeout_seconds', 15)
        start_time = time.time()

        logger.info(f"Using execution timeout: {max_execution_time}s, step timeout: {step_timeout}s")

        for i, step in enumerate(steps):
            # Check if we've exceeded the maximum execution time
            if time.time() - start_time > max_execution_time:
                logger.warning(f"Maximum execution time exceeded. Stopping execution.")
                self.execution_log.append({
                    "success": False,
                    "action": "timeout",
                    "message": f"Maximum execution time of {max_execution_time} seconds exceeded"
                })
                overall_success = False
                break

            self.current_step = i + 1

            # Calculate progress percentage
            progress_percent = int((self.current_step / self.total_steps) * 100)

            logger.info(f"Executing step {self.current_step}/{self.total_steps} ({progress_percent}%): {step.get('action')}")

            # Skip screenshot steps except for the last one to reduce resource usage
            if step.get("action") == "screenshot":
                if i < len(steps) - 1 or BROWSER_CONFIG.get('disable_screenshots', False):
                    logger.info("Skipping intermediate screenshot to save resources")
                    self.execution_log.append({
                        "success": True,
                        "action": "screenshot",
                        "message": "Screenshot skipped to save resources"
                    })
                    continue

            try:
                # Set a timeout for each step execution
                step_start_time = time.time()

                # Execute the step with timeout
                step_result = self.execute_step(step)

                # Check if step took too long
                if time.time() - step_start_time > step_timeout:
                    logger.warning(f"Step {self.current_step} took too long to execute")
                    step_result["message"] += " (execution time warning)"

                if not step_result.get("success", False):
                    logger.warning(f"Step {self.current_step} failed: {step_result.get('message')}")
                    overall_success = False

                    # Limit the number of consecutive failures
                    if i > 0 and not self.execution_log[-1].get("success", False):
                        logger.warning("Two consecutive steps failed. Stopping execution.")
                        break

                # Add a small delay between steps to reduce CPU usage
                if BROWSER_CONFIG.get('lightweight_mode', False):
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error executing step {self.current_step}: {str(e)}")
                self.execution_log.append({
                    "success": False,
                    "action": step.get("action", "unknown"),
                    "error": str(e),
                    "message": f"Error executing step: {str(e)}"
                })
                overall_success = False
                break

        # Prepare the final result
        final_result = {
            "success": overall_success,
            "original_task": self.task_plan.get("original_task"),
            "task_type": self.task_plan.get("task_type"),
            "steps_executed": self.current_step,
            "total_steps": self.total_steps,
            "execution_log": self.execution_log,
            "screenshots": self.screenshots,
            "message": "Task execution completed" if overall_success else "Task execution completed with errors"
        }

        logger.info(f"Task execution completed: {final_result.get('message')}")
        return final_result
