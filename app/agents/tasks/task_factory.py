"""
Task Factory for Super Agent.

This module provides a factory for creating task-specific handlers based on the task description.
"""

import re
from typing import Dict, Any, Optional, List, Type

# Import task handlers
from app.agents.tasks.flight_booking import FlightBookingTask
from app.agents.tasks.hotel_booking import HotelBookingTask
from app.agents.tasks.email_sender import EmailSenderTask
from app.agents.tasks.ride_hailing import RideHailingTask
from app.agents.tasks.design_task import DesignTask


class TaskFactory:
    """Factory for creating task-specific handlers."""

    def __init__(self):
        """Initialize the task factory."""
        # Register task handlers with their keywords
        self.task_handlers = {
            "flight_booking": {
                "handler": FlightBookingTask,
                "keywords": [
                    "book a flight", "flight booking", "book flight", "flight ticket",
                    "plane ticket", "air travel", "airline", "fly to", "flying to",
                    "flight from", "flight to", "book a plane", "book an airplane"
                ]
            },
            "hotel_booking": {
                "handler": HotelBookingTask,
                "keywords": [
                    "book a hotel", "hotel booking", "book hotel", "find hotel",
                    "accommodation", "place to stay", "room booking", "book a room",
                    "hotel reservation", "find accommodation", "book accommodation",
                    "hotel in", "hotels in", "stay in", "lodging", "motel", "hostel",
                    "airbnb", "vacation rental"
                ]
            },
            "email_sender": {
                "handler": EmailSenderTask,
                "keywords": [
                    "send an email", "send email", "compose email", "write email",
                    "email to", "send a message", "compose a message", "write a message",
                    "send mail", "compose mail", "write mail", "email someone"
                ]
            },
            "ride_hailing": {
                "handler": RideHailingTask,
                "keywords": [
                    "book a ride", "order a ride", "call a taxi", "get a taxi",
                    "uber ride", "lyft ride", "taxi service", "ride service",
                    "book a taxi", "order a taxi", "get a ride", "book a car",
                    "order a car", "ride to", "taxi to", "uber to", "lyft to"
                ]
            },
            "design": {
                "handler": DesignTask,
                "keywords": [
                    "create a webpage", "build a webpage", "design a webpage", "make a website",
                    "develop a website", "html", "css", "website", "webpage", "landing page",
                    "create a diagram", "draw a diagram", "make a diagram", "design a diagram",
                    "flowchart", "sequence diagram", "class diagram", "er diagram",
                    "entity relationship", "uml", "mindmap", "gantt",
                    "create a pdf", "generate a pdf", "make a pdf", "pdf document", "pdf report"
                ]
            }
        }

    def get_task_handler(self, task_description: str) -> Optional[Type]:
        """
        Get the appropriate task handler for the given task description.

        Args:
            task_description (str): The task description.

        Returns:
            Optional[Type]: The task handler class, or None if no handler is found.
        """
        task_description = task_description.lower()

        # Check for each task type
        for task_type, task_info in self.task_handlers.items():
            for keyword in task_info["keywords"]:
                if keyword.lower() in task_description:
                    return task_info["handler"]

        # No specific handler found
        return None

    def create_task(self, task_description: str, **kwargs) -> Any:
        """
        Create a task handler for the given task description.

        Args:
            task_description (str): The task description.
            **kwargs: Additional arguments to pass to the task handler.

        Returns:
            Any: The task handler instance, or None if no handler is found.
        """
        handler_class = self.get_task_handler(task_description)
        if handler_class:
            return handler_class(task_description=task_description, **kwargs)
        return None
