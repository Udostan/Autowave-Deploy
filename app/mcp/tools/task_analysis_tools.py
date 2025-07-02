"""
Task analysis tools for the MCP server.
"""

import json
import logging
import time
from typing import Dict, Any, List

from app.api.gemini import GeminiAPI

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskAnalysisTools:
    """
    Tools for analyzing and breaking down complex tasks.
    """
    
    def __init__(self):
        """
        Initialize the Task Analysis tools.
        """
        self.logger = logging.getLogger(__name__)
        self.gemini_api = GeminiAPI()
        self.logger.info("Task Analysis tools initialized")
    
    def analyze_web_task(self, task: str) -> Dict[str, Any]:
        """
        Analyze a web browsing task and break it down into steps.
        
        Args:
            task: The task to analyze
            
        Returns:
            A dictionary containing the analysis results
        """
        try:
            self.logger.info(f"Analyzing web task: {task}")
            
            # Create a prompt for the LLM
            prompt = f"""
            Analyze this web browsing task and break it down into specific browser automation steps:
            
            TASK: "{task}"
            
            Return a JSON object with:
            1. task_type: "complex" for multi-step tasks or "search" for simple search
            2. task_description: Brief description of the task
            3. fallback_search_query: Search query to use if the task fails
            4. steps: Array of steps with these actions:
               - navigate: Go to a URL
               - click: Click on an element
               - type: Type text into a field
               - press_key: Press a keyboard key
               - scroll: Scroll the page
               - wait: Wait for a specified time
               - extract: Extract data from the page
            
            Each step should include an action, relevant parameters (url, selector, text, etc.), 
            and a description explaining what the step accomplishes.
            
            For complex e-commerce tasks (Amazon, etc.), include steps to navigate, search, filter, and extract data.
            For booking tasks, include steps to navigate to the booking site, enter details, and search.
            
            Return ONLY the JSON object without any additional text.
            """
            
            # Call the LLM to analyze the task
            response = self.gemini_api.generate_text(prompt, temperature=0.2)
            
            # Parse the response as JSON
            try:
                # Try to extract just the JSON part if there's extra text
                import re
                json_str = response
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Look for anything that looks like a JSON object
                    json_match = re.search(r'(\{.*\})', response.replace('\n', ' '), re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                
                task_plan = json.loads(json_str)
                
                # Validate the task plan
                if 'task_type' not in task_plan:
                    task_plan['task_type'] = 'search'
                
                if task_plan['task_type'] == 'complex' and ('steps' not in task_plan or not task_plan['steps']):
                    # If it's a complex task but no steps are provided, convert to search
                    task_plan['task_type'] = 'search'
                    task_plan['fallback_search_query'] = task
                
                if 'fallback_search_query' not in task_plan:
                    task_plan['fallback_search_query'] = task
                
                # Add metadata
                task_plan['_meta'] = {
                    'timestamp': time.time(),
                    'task': task,
                    'analysis_version': '1.0'
                }
                
                self.logger.info(f"Successfully analyzed task: {task}")
                return task_plan
                
            except json.JSONDecodeError as json_error:
                self.logger.error(f"Failed to parse JSON from response: {json_error}")
                # Return a fallback task plan
                return {
                    "task_type": "search",
                    "task_description": f"Search for information about: {task}",
                    "fallback_search_query": task,
                    "steps": [],
                    "_meta": {
                        'timestamp': time.time(),
                        'task': task,
                        'analysis_version': '1.0',
                        'error': 'JSON parsing failed'
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing web task: {str(e)}")
            # Return a fallback task plan
            return {
                "task_type": "search",
                "task_description": f"Search for information about: {task}",
                "fallback_search_query": task,
                "steps": [],
                "_meta": {
                    'timestamp': time.time(),
                    'task': task,
                    'analysis_version': '1.0',
                    'error': str(e)
                }
            }
