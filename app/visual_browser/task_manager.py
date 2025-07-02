"""
Task Manager for Live Browser.

This module provides functionality to manage tasks in the Live Browser.
"""

import time
import json
import logging
import threading
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Task storage
tasks = {}
tasks_lock = threading.Lock()

def add_task(task_id: str, task_data: Dict[str, Any]) -> None:
    """
    Add a task to the task manager.
    
    Args:
        task_id: The ID of the task.
        task_data: The task data.
    """
    with tasks_lock:
        tasks[task_id] = {
            **task_data,
            'status': task_data.get('status', 'queued'),
            'timestamp': task_data.get('timestamp', time.time()),
            'progress': []
        }
    logger.info(f"Added task {task_id}: {task_data.get('task', 'Unknown task')}")

def update_task_status(task_id: str, status: str, data: Dict[str, Any] = None) -> None:
    """
    Update the status of a task.
    
    Args:
        task_id: The ID of the task.
        status: The new status of the task.
        data: Additional data to update.
    """
    if data is None:
        data = {}
        
    with tasks_lock:
        if task_id not in tasks:
            logger.warning(f"Task {task_id} not found")
            return
            
        tasks[task_id]['status'] = status
        tasks[task_id]['last_updated'] = time.time()
        
        # Add progress message if provided
        if 'message' in data:
            tasks[task_id]['progress'].append({
                'message': data['message'],
                'timestamp': time.time()
            })
            
        # Update other data
        for key, value in data.items():
            if key != 'message':
                tasks[task_id][key] = value
                
    logger.info(f"Updated task {task_id} status to {status}")

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a task by ID.
    
    Args:
        task_id: The ID of the task.
        
    Returns:
        The task data or None if not found.
    """
    with tasks_lock:
        return tasks.get(task_id)

def get_all_tasks() -> List[Dict[str, Any]]:
    """
    Get all tasks.
    
    Returns:
        A list of all tasks.
    """
    with tasks_lock:
        return list(tasks.values())

def clean_old_tasks(max_age_seconds: int = 3600) -> None:
    """
    Clean up old tasks.
    
    Args:
        max_age_seconds: The maximum age of tasks to keep.
    """
    current_time = time.time()
    with tasks_lock:
        task_ids = list(tasks.keys())
        for task_id in task_ids:
            task = tasks[task_id]
            if current_time - task.get('timestamp', 0) > max_age_seconds:
                del tasks[task_id]
                logger.info(f"Removed old task {task_id}")

# Start a background thread to clean up old tasks periodically
def start_cleanup_thread():
    """
    Start a background thread to clean up old tasks periodically.
    """
    def cleanup_loop():
        while True:
            try:
                clean_old_tasks()
            except Exception as e:
                logger.error(f"Error cleaning up old tasks: {str(e)}")
            time.sleep(3600)  # Clean up every hour
            
    cleanup_thread = threading.Thread(target=cleanup_loop)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    logger.info("Started task cleanup thread")

# Start the cleanup thread
start_cleanup_thread()
