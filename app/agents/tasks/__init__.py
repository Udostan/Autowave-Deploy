"""
Task-specific handlers for Super Agent.
"""

from app.agents.tasks.base_task import BaseTask
from app.agents.tasks.flight_booking import FlightBookingTask
from app.agents.tasks.hotel_booking import HotelBookingTask
from app.agents.tasks.email_sender import EmailSenderTask
from app.agents.tasks.ride_hailing import RideHailingTask
from app.agents.tasks.task_factory import TaskFactory

__all__ = [
    'BaseTask',
    'FlightBookingTask',
    'HotelBookingTask',
    'EmailSenderTask',
    'RideHailingTask',
    'TaskFactory'
]
