"""
Execute complex task method for LiveBrowser class.

This module provides the execute_complex_task method for the LiveBrowser class.
"""

import time
import json
import logging
import threading
import traceback
import resource
import queue
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
