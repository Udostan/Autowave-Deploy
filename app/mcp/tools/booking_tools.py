"""
Booking tools for the MCP server.
"""

import logging
from typing import Dict, Any, List, Optional

from app.utils.booking_handler import BookingHandler

logger = logging.getLogger(__name__)

class BookingTools:
    """
    Tools for handling booking-related tasks.
    """
    
    def __init__(self):
        """Initialize booking tools."""
        self.booking_handler = BookingHandler()
        self.logger = logging.getLogger(__name__)
    
    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for flights.
        
        Args:
            origin: Origin airport code or city
            destination: Destination airport code or city
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (optional)
            
        Returns:
            Flight search results and booking links
        """
        self.logger.info(f"Searching flights from {origin} to {destination}")
        return self.booking_handler.search_flights(origin, destination, departure_date, return_date)
    
    def search_hotels(self, location: str, check_in_date: str, check_out_date: str, 
                     guests: int = 2) -> Dict[str, Any]:
        """
        Search for hotels.
        
        Args:
            location: Hotel location (city)
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            guests: Number of guests (default: 2)
            
        Returns:
            Hotel search results and booking links
        """
        self.logger.info(f"Searching hotels in {location}")
        return self.booking_handler.search_hotels(location, check_in_date, check_out_date, guests)
    
    def estimate_ride(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        Estimate ride prices.
        
        Args:
            origin: Pickup location
            destination: Dropoff location
            
        Returns:
            Ride estimates and booking links
        """
        self.logger.info(f"Estimating ride from {origin} to {destination}")
        return self.booking_handler.estimate_ride(origin, destination)
