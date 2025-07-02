"""
Task Manager for Prime Agent.

This module provides a task manager for Prime Agent to track and update task progress.
"""

import os
import time
import json
import uuid
import logging
import threading
import traceback
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskManager:
    """
    A task manager for Prime Agent to track and update task progress.
    """

    def __init__(self):
        """
        Initialize the Task Manager.
        """
        self.tasks = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Task Manager initialized")

    def create_task(self, task: str, use_visual_browser: bool = False) -> str:
        """
        Create a new task.

        Args:
            task: The task to create.
            use_visual_browser: Whether to use the visual browser for this task.

        Returns:
            str: The ID of the created task.
        """
        try:
            task_id = str(uuid.uuid4())

            with self.lock:
                self.tasks[task_id] = {
                    "task": task,
                    "use_visual_browser": use_visual_browser,
                    "status": "pending",
                    "created_at": time.time(),
                    "updated_at": time.time(),
                    "progress": [],
                    "result": None
                }

            self.logger.info(f"Created task {task_id}: {task}")

            return task_id
        except Exception as e:
            self.logger.error(f"Error creating task: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by ID.

        Args:
            task_id: The ID of the task to get.

        Returns:
            Optional[Dict[str, Any]]: The task, or None if not found.
        """
        try:
            with self.lock:
                return self.tasks.get(task_id)
        except Exception as e:
            self.logger.error(f"Error getting task {task_id}: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def update_task_progress(self, task_id: str, status: str, message: str) -> bool:
        """
        Update the progress of a task.

        Args:
            task_id: The ID of the task to update.
            status: The status of the task ('pending', 'thinking', 'complete', 'error').
            message: The progress message.

        Returns:
            bool: True if the task was updated, False otherwise.
        """
        try:
            with self.lock:
                task = self.tasks.get(task_id)
                if not task:
                    return False

                task["status"] = status
                task["updated_at"] = time.time()

                # Check if this is a new message or if we already have this message
                is_new_message = True
                for progress_item in task["progress"]:
                    if progress_item["message"] == message and progress_item["status"] == status:
                        is_new_message = False
                        break

                # Only add the message if it's new
                if is_new_message:
                    task["progress"].append({
                        "status": status,
                        "message": message,
                        "timestamp": time.time()
                    })
                    self.logger.info(f"Updated task {task_id} progress: {status} - {message}")

            return True
        except Exception as e:
            self.logger.error(f"Error updating task {task_id} progress: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """
        Complete a task.

        Args:
            task_id: The ID of the task to complete.
            result: The result of the task.

        Returns:
            bool: True if the task was completed, False otherwise.
        """
        try:
            with self.lock:
                task = self.tasks.get(task_id)
                if not task:
                    return False

                task["status"] = "complete"
                task["updated_at"] = time.time()
                task["result"] = result
                task["progress"].append({
                    "status": "complete",
                    "message": "Task completed",
                    "timestamp": time.time()
                })

            self.logger.info(f"Completed task {task_id}")

            return True
        except Exception as e:
            self.logger.error(f"Error completing task {task_id}: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def fail_task(self, task_id: str, error: str) -> bool:
        """
        Fail a task.

        Args:
            task_id: The ID of the task to fail.
            error: The error message.

        Returns:
            bool: True if the task was failed, False otherwise.
        """
        try:
            with self.lock:
                task = self.tasks.get(task_id)
                if not task:
                    return False

                task["status"] = "error"
                task["updated_at"] = time.time()
                task["result"] = {"success": False, "error": error}
                task["progress"].append({
                    "status": "error",
                    "message": error,
                    "timestamp": time.time()
                })

            self.logger.info(f"Failed task {task_id}: {error}")

            return True
        except Exception as e:
            self.logger.error(f"Error failing task {task_id}: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def get_task_progress(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get the progress of a task.

        Args:
            task_id: The ID of the task to get progress for.

        Returns:
            List[Dict[str, Any]]: The progress of the task.
        """
        try:
            with self.lock:
                task = self.tasks.get(task_id)
                if not task:
                    return []

                return task["progress"]
        except Exception as e:
            self.logger.error(f"Error getting task {task_id} progress: {str(e)}")
            self.logger.error(traceback.format_exc())
            return []

    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Get the status of a task.

        Args:
            task_id: The ID of the task to get status for.

        Returns:
            Optional[str]: The status of the task, or None if not found.
        """
        try:
            with self.lock:
                task = self.tasks.get(task_id)
                if not task:
                    return None

                return task["status"]
        except Exception as e:
            self.logger.error(f"Error getting task {task_id} status: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the result of a task.

        Args:
            task_id: The ID of the task to get result for.

        Returns:
            Optional[Dict[str, Any]]: The result of the task, or None if not found or not complete.
        """
        try:
            with self.lock:
                task = self.tasks.get(task_id)
                if not task:
                    return None

                return task["result"]
        except Exception as e:
            self.logger.error(f"Error getting task {task_id} result: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None

# Create a singleton instance
task_manager = TaskManager()
