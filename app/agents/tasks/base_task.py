"""
Base Task for Super Agent.

This module provides a base class for all task-specific handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BaseTask(ABC):
    """Base class for all task-specific handlers."""

    def __init__(self, task_description: str, **kwargs):
        """
        Initialize the base task.

        Args:
            task_description (str): The task description.
            **kwargs: Additional arguments.
        """
        self.task_description = task_description
        self.kwargs = kwargs
        self.result = {
            "task_description": task_description,
            "steps": [],
            "results": [],
            "step_summaries": [],
            "success": False
        }

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Execute the task.

        Returns:
            Dict[str, Any]: The task execution result.
        """
        pass

    def add_step(self, action: str, **params) -> None:
        """
        Add a step to the task execution.

        Args:
            action (str): The action to perform.
            **params: Additional parameters for the action.
        """
        step = {"action": action}
        step.update(params)
        self.result["steps"].append(step)

    def add_result(self, step: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Add a result to the task execution.

        Args:
            step (Dict[str, Any]): The step that produced the result.
            result (Dict[str, Any]): The result of the step.
        """
        self.result["results"].append({
            "step": step,
            "result": result
        })

    def add_step_summary(self, description: str, summary: str, success: bool) -> None:
        """
        Add a step summary to the task execution.

        Args:
            description (str): The step description.
            summary (str): The step summary.
            success (bool): Whether the step was successful.
        """
        self.result["step_summaries"].append({
            "description": description,
            "summary": summary,
            "success": success
        })

    def set_task_summary(self, summary: str) -> None:
        """
        Set the task summary.

        Args:
            summary (str): The task summary.
        """
        self.result["task_summary"] = summary

    def set_success(self, success: bool) -> None:
        """
        Set the task success status.

        Args:
            success (bool): Whether the task was successful.
        """
        self.result["success"] = success

    def get_result(self) -> Dict[str, Any]:
        """
        Get the task execution result.

        Returns:
            Dict[str, Any]: The task execution result.
        """
        return self.result
