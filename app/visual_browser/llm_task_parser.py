"""
LLM-powered Task Parser for Live Browser.

This module provides functionality to parse complex tasks into simple steps
using LLM intelligence from Gemini or Groq.
"""

import logging
import json
import os
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

# Import LLM APIs
try:
    from app.api.gemini import GeminiAPI
    from app.api.groq import GroqAPI
    LLM_AVAILABLE = True
except ImportError:
    logger.warning("LLM APIs not available. Using rule-based parsing only.")
    LLM_AVAILABLE = False

def get_llm_client():
    """
    Get an LLM client (Gemini or Groq) based on available API keys.
    
    Returns:
        An instance of GeminiAPI, GroqAPI, or None if no API is available.
    """
    if not LLM_AVAILABLE:
        return None
        
    try:
        # Try Gemini first
        gemini_api = GeminiAPI()
        if gemini_api.model is not None:
            logger.info("Using Gemini API for task parsing")
            return gemini_api
    except Exception as e:
        logger.warning(f"Error initializing Gemini API: {e}")
    
    try:
        # Try Groq as fallback
        groq_api = GroqAPI()
        if groq_api.is_available():
            logger.info("Using Groq API for task parsing")
            return groq_api
    except Exception as e:
        logger.warning(f"Error initializing Groq API: {e}")
    
    logger.warning("No LLM API available for task parsing")
    return None

def parse_task_with_llm(task: str) -> List[Dict[str, Any]]:
    """
    Parse a complex task into simple steps using LLM intelligence.
    
    Args:
        task: The complex task description.
        
    Returns:
        A list of steps to execute.
    """
    logger.info(f"Parsing task with LLM: {task}")
    
    # Get LLM client
    llm_client = get_llm_client()
    if llm_client is None:
        logger.warning("No LLM client available. Falling back to rule-based parsing.")
        # Import the rule-based parser
        from app.visual_browser.task_parser import parse_task
        return parse_task(task)
    
    # Construct the prompt for the LLM
    prompt = f"""
    You are an AI assistant that helps break down complex web browsing tasks into simple steps.
    
    Given the following task: "{task}"
    
    Break this down into a sequence of simple browser automation steps. Each step should be one of:
    1. navigate - Go to a URL
    2. click - Click on an element (by selector or text)
    3. type - Type text into an input field
    4. press_key - Press a key (like Enter, Tab, etc.)
    5. scroll - Scroll the page (up, down, left, right)
    6. wait - Wait for a specific time or for an element to appear
    
    Return the steps as a JSON array where each step is an object with:
    - "action": The action to perform (one of the above)
    - Additional parameters specific to the action (e.g., "url" for navigate, "text" for type)
    
    For example:
    [
        {{"action": "navigate", "url": "https://www.google.com"}},
        {{"action": "type", "selector": "textarea[name='q']", "text": "weather in new york"}},
        {{"action": "press_key", "key": "enter"}}
    ]
    
    Ensure the steps are detailed enough to complete the task but not too complex.
    Limit to a maximum of {BROWSER_CONFIG.get('max_steps', 10)} steps.
    Only return the JSON array, nothing else.
    """
    
    try:
        # Generate the steps using the LLM
        if isinstance(llm_client, GeminiAPI):
            response = llm_client.generate_text(prompt, temperature=0.2)
        else:  # GroqAPI
            response = llm_client.generate_text(prompt, temperature=0.2)
        
        # Extract the JSON array from the response
        response = response.strip()
        
        # If the response is wrapped in ```json and ```, remove them
        if response.startswith("```json") and response.endswith("```"):
            response = response[7:-3].strip()
        elif response.startswith("```") and response.endswith("```"):
            response = response[3:-3].strip()
            
        # Parse the JSON array
        steps = json.loads(response)
        
        # Validate the steps
        if not isinstance(steps, list):
            raise ValueError("Response is not a list of steps")
        
        # Ensure each step has an action
        for step in steps:
            if not isinstance(step, dict) or "action" not in step:
                raise ValueError("Step is missing an action")
        
        # Limit the number of steps
        max_steps = BROWSER_CONFIG.get('max_steps', 10)
        if len(steps) > max_steps:
            logger.warning(f"Too many steps ({len(steps)}). Limiting to {max_steps}.")
            steps = steps[:max_steps]
        
        # Add a screenshot step at the end if screenshots are not disabled
        if not BROWSER_CONFIG.get('disable_screenshots', False):
            steps.append({"action": "screenshot"})
            
        logger.info(f"Successfully parsed task with LLM into {len(steps)} steps")
        return steps
        
    except Exception as e:
        logger.error(f"Error parsing task with LLM: {e}")
        # Fall back to rule-based parsing
        logger.warning("Falling back to rule-based parsing")
        from app.visual_browser.task_parser import parse_task
        return parse_task(task)

def parse_complex_task_with_llm(task: str) -> Dict[str, Any]:
    """
    Parse a complex task and return a structured task plan using LLM intelligence.
    
    Args:
        task: The complex task description.
        
    Returns:
        A dictionary containing the task plan.
    """
    steps = parse_task_with_llm(task)
    
    # Determine task type based on the first step
    task_type = "complex"
    if steps and steps[0].get("action") == "navigate":
        task_type = "navigate"
    elif any(step.get("action") == "type" and "search" in step.get("text", "").lower() for step in steps):
        task_type = "search"
        
    return {
        "original_task": task,
        "task_type": task_type,
        "steps": steps,
        "total_steps": len(steps),
        "llm_powered": True
    }
