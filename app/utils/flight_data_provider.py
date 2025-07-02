"""
Flight data provider using SerpAPI and RapidAPI.
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class FlightDataProvider:
    """Provider for real-time flight data using SerpAPI and RapidAPI."""

    def __init__(self):
        """Initialize the flight data provider."""
        self.serper_api_key = os.environ.get("SERPER_API_KEY")
        self.rapid_api_key = os.environ.get("RAPID_API_KEY")
        
        # If RAPID_API_KEY is not set, we'll use only SerpAPI
        if not self.rapid_api_key:
            logger.warning("RAPID_API_KEY not set, using only SerpAPI for flight data")
        
        # Ensure we have at least SerpAPI key
        if not self.serper_api_key:
            logger.error("SERPER_API_KEY not set, flight data provider will not work")

    def get_flights(self, origin: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get flight data using SerpAPI to search Google Flights.
        
        Args:
            origin: Origin city or airport code
            destination: Destination city or airport code
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Optional return date in YYYY-MM-DD format
            
        Returns:
            List of flight options with details
        """
        # First try SerpAPI to get Google Flights data
        serp_results = self._search_with_serp_api(origin, destination, departure_date, return_date)
        
        # If we have results from SerpAPI, return them
        if serp_results and len(serp_results) > 0:
            logger.info(f"Found {len(serp_results)} flights using SerpAPI")
            return serp_results
        
        # If SerpAPI didn't return results and we have RapidAPI key, try that
        if self.rapid_api_key:
            rapid_results = self._search_with_rapid_api(origin, destination, departure_date, return_date)
            if rapid_results and len(rapid_results) > 0:
                logger.info(f"Found {len(rapid_results)} flights using RapidAPI")
                return rapid_results
        
        # If we still don't have results, return an empty list
        logger.warning(f"No flight results found for {origin} to {destination}")
        return []

    def _search_with_serp_api(self, origin: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for flights using SerpAPI's Google Flights integration.
        
        Args:
            origin: Origin city or airport code
            destination: Destination city or airport code
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Optional return date in YYYY-MM-DD format
            
        Returns:
            List of flight options with details
        """
        try:
            # Format the query for Google Flights
            query = f"flights from {origin} to {destination} on {departure_date}"
            if return_date:
                query += f" return {return_date}"
            
            # Make the request to SerpAPI
            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": query,
                "gl": "us",
                "hl": "en",
                "autocorrect": True
            })
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract flight information from the response
            flights = []
            
            # Check if we have flight boxes in the response
            if 'answerBox' in data and 'flights' in data['answerBox']:
                flight_data = data['answerBox']['flights']
                for flight in flight_data:
                    flights.append({
                        "airline": flight.get('airline', 'Unknown Airline'),
                        "price": flight.get('price', 'Price not available'),
                        "duration": flight.get('duration', 'Duration not available'),
                        "departure_time": flight.get('departureTime', 'Departure time not available'),
                        "arrival_time": flight.get('arrivalTime', 'Arrival time not available'),
                        "stops": flight.get('stops', 0),
                        "type": "flight",
                        "origin": origin,
                        "destination": destination
                    })
            
            # If we don't have flight boxes, try to extract from organic results
            if not flights and 'organic' in data:
                for result in data['organic']:
                    if 'price' in result.get('title', '').lower() or 'flight' in result.get('title', '').lower():
                        # Extract price from title or snippet
                        price_match = None
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        
                        # Look for price patterns like $123 or $1,234
                        import re
                        price_pattern = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
                        price_matches = re.findall(price_pattern, title + ' ' + snippet)
                        
                        if price_matches:
                            price = price_matches[0]
                        else:
                            price = 'Price not available'
                        
                        # Create a flight entry
                        flights.append({
                            "airline": "Multiple Airlines",
                            "price": price,
                            "duration": "Duration varies",
                            "departure_time": "Various times",
                            "arrival_time": "Various times",
                            "stops": "Varies",
                            "type": "flight",
                            "origin": origin,
                            "destination": destination
                        })
                        
                        # Limit to 3 results
                        if len(flights) >= 3:
                            break
            
            return flights
            
        except Exception as e:
            logger.error(f"Error searching flights with SerpAPI: {str(e)}")
            return []

    def _search_with_rapid_api(self, origin: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for flights using RapidAPI's flight data providers.
        
        Args:
            origin: Origin city or airport code
            destination: Destination city or airport code
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Optional return date in YYYY-MM-DD format
            
        Returns:
            List of flight options with details
        """
        try:
            # Format the date for the API (YYYY-MM-DD)
            formatted_date = departure_date
            
            # Make the request to RapidAPI
            url = "https://skyscanner44.p.rapidapi.com/search"
            querystring = {
                "adults":"1",
                "origin":origin,
                "destination":destination,
                "departureDate":formatted_date,
                "returnDate":return_date if return_date else "",
                "currency":"USD"
            }
            headers = {
                "X-RapidAPI-Key": self.rapid_api_key,
                "X-RapidAPI-Host": "skyscanner44.p.rapidapi.com"
            }
            
            response = requests.request("GET", url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            
            # Extract flight information from the response
            flights = []
            
            # Parse the response based on the API structure
            if 'itineraries' in data and 'buckets' in data['itineraries']:
                for bucket in data['itineraries']['buckets']:
                    if 'items' in bucket:
                        for item in bucket['items']:
                            price = item.get('price', {}).get('formatted', 'Price not available')
                            
                            # Get the first leg (outbound flight)
                            if 'legs' in item and len(item['legs']) > 0:
                                leg = item['legs'][0]
                                airline = leg.get('carriers', {}).get('marketing', [{}])[0].get('name', 'Unknown Airline')
                                departure_time = leg.get('departure', 'Departure time not available')
                                arrival_time = leg.get('arrival', 'Arrival time not available')
                                duration = leg.get('durationInMinutes', 0)
                                hours = duration // 60
                                minutes = duration % 60
                                duration_str = f"{hours}h {minutes}m"
                                stops = len(leg.get('stopCount', 0))
                                
                                flights.append({
                                    "airline": airline,
                                    "price": price,
                                    "duration": duration_str,
                                    "departure_time": departure_time,
                                    "arrival_time": arrival_time,
                                    "stops": stops,
                                    "type": "flight",
                                    "origin": origin,
                                    "destination": destination
                                })
                            
                            # Limit to 5 results
                            if len(flights) >= 5:
                                break
                    
                    # If we have enough flights, break out of the outer loop too
                    if len(flights) >= 5:
                        break
            
            return flights
            
        except Exception as e:
            logger.error(f"Error searching flights with RapidAPI: {str(e)}")
            return []

    def get_booking_links(self, origin: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Generate booking links for flights.
        
        Args:
            origin: Origin city or airport code
            destination: Destination city or airport code
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Optional return date in YYYY-MM-DD format
            
        Returns:
            List of booking links with descriptions
        """
        # Format the dates for URLs
        formatted_departure = departure_date.replace('-', '')
        formatted_return = return_date.replace('-', '') if return_date else ''
        
        # Create booking links for popular flight booking sites
        booking_links = [
            {
                "description": "Book on Google Flights",
                "url": f"https://www.google.com/travel/flights?q=Flights%20from%20{origin.replace(' ', '+')}%20to%20{destination.replace(' ', '+')}%20on%20{formatted_departure}"
            },
            {
                "description": "Book on Expedia",
                "url": f"https://www.expedia.com/Flights-Search?trip=roundtrip&leg1=from:{origin},to:{destination},departure:{departure_date}" + (f"&leg2=from:{destination},to:{origin},departure:{return_date}" if return_date else "")
            },
            {
                "description": "Book on Kayak",
                "url": f"https://www.kayak.com/flights/{origin.replace(' ', '')}-{destination.replace(' ', '')}/{formatted_departure}" + (f"/{formatted_return}" if formatted_return else "")
            },
            {
                "description": "Book on Skyscanner",
                "url": f"https://www.skyscanner.com/transport/flights/{origin[:3].lower()}/{destination[:3].lower()}/{formatted_departure}" + (f"/{formatted_return}" if formatted_return else "")
            }
        ]
        
        return booking_links
