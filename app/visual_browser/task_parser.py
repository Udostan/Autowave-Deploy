"""
Task Parser for Live Browser.

This module provides functionality to parse complex tasks into simple steps
that can be executed by the Live Browser without requiring a heavy LLM.
"""

import re
import logging
import json
from typing import List, Dict, Any, Optional

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

# Define task templates
TASK_TEMPLATES = {
    "search": {
        "keywords": ["search", "find", "look up", "google", "information about"],
        "steps": [
            {"action": "navigate", "url": "https://www.google.com"},
            {"action": "type", "selector": "textarea[name='q']", "text": "{query}"},
            {"action": "press_key", "key": "enter"}
        ]
    },
    "login": {
        "keywords": ["login", "sign in", "log in", "access", "account"],
        "steps": [
            {"action": "navigate", "url": "{url}"},
            {"action": "type", "selector": "input[type='email'], input[name='email'], input[type='text'], input[name='username']", "text": "{username}"},
            {"action": "type", "selector": "input[type='password'], input[name='password']", "text": "{password}"},
            {"action": "click", "selector": "button[type='submit'], input[type='submit']"}
        ]
    },
    "fill_form": {
        "keywords": ["fill", "form", "complete", "submit", "enter information"],
        "steps": [
            {"action": "navigate", "url": "{url}"},
            {"action": "fill_form", "form_data": "{form_data}"}
        ]
    },
    "navigate": {
        "keywords": ["go to", "visit", "open", "navigate to", "browse"],
        "steps": [
            {"action": "navigate", "url": "{url}"}
        ]
    },
    "click": {
        "keywords": ["click", "press", "select", "choose"],
        "steps": [
            {"action": "click", "selector": "{selector}", "text": "{text}"}
        ]
    },
    "scroll": {
        "keywords": ["scroll", "move down", "move up"],
        "steps": [
            {"action": "scroll", "direction": "{direction}", "amount": "{amount}"}
        ]
    }
}

def extract_url(task: str) -> Optional[str]:
    """
    Extract URL from a task description.

    Args:
        task: The task description.

    Returns:
        The extracted URL or None if no URL is found.
    """
    # URL pattern
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    match = re.search(url_pattern, task)
    if match:
        return match.group(0)

    # Check for domain-like text
    domain_pattern = r'\b(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z0-9]{2,}\b'
    match = re.search(domain_pattern, task)
    if match:
        domain = match.group(0)
        if not domain.startswith('http'):
            return f"https://{domain}"
        return domain

    return None

def extract_search_query(task: str) -> str:
    """
    Extract search query from a task description.

    Args:
        task: The task description.

    Returns:
        The extracted search query.
    """
    # Remove common search prefixes
    prefixes = [
        "search for", "search", "find", "look up", "google",
        "information about", "tell me about", "find information on"
    ]

    task_lower = task.lower()
    for prefix in prefixes:
        if task_lower.startswith(prefix):
            return task[len(prefix):].strip()

    return task

def identify_task_type(task: str) -> str:
    """
    Identify the type of task based on keywords.

    Args:
        task: The task description.

    Returns:
        The identified task type.
    """
    task_lower = task.lower()

    # Check for URL in task
    if extract_url(task):
        return "navigate"

    # Check for task type based on keywords
    for task_type, template in TASK_TEMPLATES.items():
        for keyword in template["keywords"]:
            if keyword.lower() in task_lower:
                return task_type

    # Default to search if no specific task type is identified
    return "search"

def parse_task(task: str) -> List[Dict[str, Any]]:
    """
    Parse a complex task into simple steps.

    Args:
        task: The complex task description.

    Returns:
        A list of steps to execute.
    """
    logger.info(f"Parsing task: {task}")

    # Check for multi-step tasks
    if "," in task or " and " in task or " then " in task:
        return parse_multi_step_task(task)

    task_type = identify_task_type(task)
    logger.info(f"Identified task type: {task_type}")

    steps = []

    if task_type == "search":
        query = extract_search_query(task)
        steps = [
            {"action": "navigate", "url": "https://www.google.com"},
            {"action": "type", "selector": "textarea[name='q']", "text": query},
            {"action": "press_key", "key": "enter"}
        ]
    elif task_type == "navigate":
        url = extract_url(task)
        if url:
            steps = [{"action": "navigate", "url": url}]
        else:
            # Fallback to search if URL extraction fails
            query = extract_search_query(task)
            steps = [
                {"action": "navigate", "url": "https://www.google.com"},
                {"action": "type", "selector": "textarea[name='q']", "text": query},
                {"action": "press_key", "key": "enter"}
            ]
    elif task_type == "login":
        # For login, we need more specific information
        # This is a simplified version that would need to be expanded
        url = extract_url(task)
        if url:
            steps = [
                {"action": "navigate", "url": url},
                {"action": "wait_for_selector", "selector": "input[type='email'], input[name='email'], input[type='text'], input[name='username']"},
                {"action": "message", "text": "Please provide login credentials in the next step"}
            ]
        else:
            # Fallback to search if URL extraction fails
            query = f"login {extract_search_query(task)}"
            steps = [
                {"action": "navigate", "url": "https://www.google.com"},
                {"action": "type", "selector": "textarea[name='q']", "text": query},
                {"action": "press_key", "key": "enter"}
            ]
    elif task_type == "fill_form":
        # For form filling, we need more specific information
        url = extract_url(task)
        if url:
            steps = [
                {"action": "navigate", "url": url},
                {"action": "wait_for_selector", "selector": "form"},
                {"action": "message", "text": "Please provide form data in the next step"}
            ]
        else:
            # Fallback to search if URL extraction fails
            query = f"form {extract_search_query(task)}"
            steps = [
                {"action": "navigate", "url": "https://www.google.com"},
                {"action": "type", "selector": "textarea[name='q']", "text": query},
                {"action": "press_key", "key": "enter"}
            ]

    # Add a final step to take a screenshot
    steps.append({"action": "screenshot"})

    logger.info(f"Parsed steps: {json.dumps(steps, indent=2)}")
    return steps

def parse_multi_step_task(task: str) -> List[Dict[str, Any]]:
    """
    Parse a multi-step task by breaking it down into individual steps.
    Simplified version to reduce resource usage.

    Args:
        task: The complex task description with multiple steps.

    Returns:
        A list of steps to execute.
    """
    logger.info(f"Parsing multi-step task: {task}")

    # Limit task length to prevent excessive processing
    max_task_length = 200 if BROWSER_CONFIG.get('lightweight_mode', False) else 500
    if len(task) > max_task_length:
        task = task[:max_task_length] + "..."
        logger.info(f"Task truncated to {max_task_length} characters to reduce processing load")

    # Get maximum number of steps from configuration
    max_steps = BROWSER_CONFIG.get('max_steps', 5)

    # Split the task into steps (limited by configuration)
    step_texts = []

    # First try to split by explicit step indicators
    if " then " in task.lower():
        step_texts = re.split(r'\s+then\s+', task, flags=re.IGNORECASE)[:max_steps]
    # Then try to split by "and"
    elif " and " in task.lower():
        step_texts = re.split(r'\s+and\s+', task, flags=re.IGNORECASE)[:max_steps]
    # Finally try to split by commas
    elif "," in task:
        step_texts = [s.strip() for s in task.split(",")][:max_steps]

    # If we couldn't split, treat as a single step
    if not step_texts:
        step_texts = [task]

    logger.info(f"Task split into {len(step_texts)} steps")

    # Process each step
    steps = []

    # First step is often navigation
    first_step = step_texts[0].lower()
    if "go to" in first_step or "visit" in first_step or "navigate to" in first_step:
        # Extract URL
        url = extract_url(step_texts[0])
        if url:
            steps.append({"action": "navigate", "url": url})
        else:
            # Try to extract a website name
            website_match = re.search(r'(?:go to|visit|navigate to)\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', step_texts[0], re.IGNORECASE)
            if website_match:
                website = website_match.group(1)
                steps.append({"action": "navigate", "url": f"https://{website}"})
            else:
                # Fallback to search
                steps.append({"action": "navigate", "url": "https://www.google.com"})
                steps.append({"action": "type", "selector": "textarea[name='q']", "text": step_texts[0]})
                steps.append({"action": "press_key", "key": "enter"})

    # Process remaining steps (simplified to reduce complexity)
    for i, step_text in enumerate(step_texts[1:], 1):
        step_text = step_text.strip().lower()

        # Search step
        if "search" in step_text or "find" in step_text or "look for" in step_text:
            query = extract_search_query(step_text)
            # Use Google search for simplicity
            steps.append({"action": "type", "selector": "textarea[name='q'], input[name='q'], input[type='search']", "text": query})
            steps.append({"action": "press_key", "key": "enter"})

        # Click step
        elif "click" in step_text:
            # Simplified click handling
            text_to_click = step_text.replace("click", "").replace("on", "").replace("the", "").strip()
            steps.append({"action": "click", "text": text_to_click})

        # Type step
        elif "type" in step_text or "enter" in step_text or "input" in step_text:
            # Simplified type handling
            text_to_type = step_text.replace("type", "").replace("enter", "").replace("input", "").strip()
            steps.append({"action": "type", "selector": "input:visible, textarea:visible", "text": text_to_type})

        # Wait step (simplified)
        elif "wait" in step_text:
            steps.append({"action": "wait", "seconds": 2})

        # Default to search
        else:
            steps.append({"action": "type", "selector": "textarea[name='q'], input[name='q'], input[type='search']", "text": step_text})
            steps.append({"action": "press_key", "key": "enter"})

    # Add a screenshot at the end if screenshots are not disabled
    if not BROWSER_CONFIG.get('disable_screenshots', False):
        steps.append({"action": "screenshot"})

    # Limit total number of steps based on configuration
    max_steps = BROWSER_CONFIG.get('max_steps', 10)
    if len(steps) > max_steps:
        logger.warning(f"Too many steps ({len(steps)}). Limiting to {max_steps}.")
        if BROWSER_CONFIG.get('disable_screenshots', False):
            steps = steps[:max_steps]
        else:
            # Keep the screenshot step at the end
            steps = steps[:max_steps-1] + [{"action": "screenshot"}]

    # Add a small delay step if in lightweight mode to reduce CPU usage
    if BROWSER_CONFIG.get('lightweight_mode', False):
        steps.append({"action": "wait", "seconds": 1, "message": "Adding small delay to reduce CPU usage"})

    logger.info(f"Final step count: {len(steps)}")
    return steps

def parse_complex_task(task: str) -> Dict[str, Any]:
    """
    Parse a complex task and return a structured task plan.
    For complex tasks, tries to use LLM-powered parsing if available.

    Args:
        task: The complex task description.

    Returns:
        A dictionary containing the task plan.
    """
    # Check if this is a complex task that would benefit from LLM parsing
    is_complex = "," in task or " and " in task or " then " in task or len(task.split()) > 10

    if is_complex:
        try:
            # Try to import and use the LLM-powered parser
            from app.visual_browser.llm_task_parser import parse_complex_task_with_llm
            return parse_complex_task_with_llm(task)
        except ImportError:
            logger.warning("LLM task parser not available. Using rule-based parsing.")
        except Exception as e:
            logger.error(f"Error using LLM task parser: {e}")
            logger.warning("Falling back to rule-based parsing")

    # Fall back to rule-based parsing
    steps = parse_task(task)

    return {
        "original_task": task,
        "task_type": identify_task_type(task),
        "steps": steps,
        "total_steps": len(steps),
        "llm_powered": False
    }
