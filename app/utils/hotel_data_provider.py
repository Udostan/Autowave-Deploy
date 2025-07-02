"""
Hotel data provider using SerpAPI and RapidAPI.
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class HotelDataProvider:
    """Provider for real-time hotel data using SerpAPI and RapidAPI."""

    def __init__(self):
        """Initialize the hotel data provider."""
        self.serper_api_key = os.environ.get("SERPER_API_KEY")
        self.rapid_api_key = os.environ.get("RAPID_API_KEY")
        
        # If RAPID_API_KEY is not set, we'll use only SerpAPI
        if not self.rapid_api_key:
            logger.warning("RAPID_API_KEY not set, using only SerpAPI for hotel data")
        
        # Ensure we have at least SerpAPI key
        if not self.serper_api_key:
            logger.error("SERPER_API_KEY not set, hotel data provider will not work")

    def get_hotels(self, location: str, check_in_date: str, check_out_date: str, guests: int = 2) -> List[Dict[str, Any]]:
        """
        Get hotel data using SerpAPI to search Google Hotels.
        
        Args:
            location: Hotel location (city)
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            guests: Number of guests
            
        Returns:
            List of hotel options with details
        """
        # First try SerpAPI to get Google Hotels data
        serp_results = self._search_with_serp_api(location, check_in_date, check_out_date, guests)
        
        # If we have results from SerpAPI, return them
        if serp_results and len(serp_results) > 0:
            logger.info(f"Found {len(serp_results)} hotels using SerpAPI")
            return serp_results
        
        # If SerpAPI didn't return results and we have RapidAPI key, try that
        if self.rapid_api_key:
            rapid_results = self._search_with_rapid_api(location, check_in_date, check_out_date, guests)
            if rapid_results and len(rapid_results) > 0:
                logger.info(f"Found {len(rapid_results)} hotels using RapidAPI")
                return rapid_results
        
        # If we still don't have results, return an empty list
        logger.warning(f"No hotel results found for {location}")
        return []

    def _search_with_serp_api(self, location: str, check_in_date: str, check_out_date: str, guests: int = 2) -> List[Dict[str, Any]]:
        """
        Search for hotels using SerpAPI's Google Hotels integration.
        
        Args:
            location: Hotel location (city)
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            guests: Number of guests
            
        Returns:
            List of hotel options with details
        """
        try:
            # Format the query for Google Hotels
            query = f"hotels in {location} {check_in_date} to {check_out_date} {guests} guests"
            
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
            
            # Extract hotel information from the response
            hotels = []
            
            # Check if we have hotel boxes in the response
            if 'answerBox' in data and 'hotels' in data['answerBox']:
                hotel_data = data['answerBox']['hotels']
                for hotel in hotel_data:
                    hotels.append({
                        "name": hotel.get('name', 'Unknown Hotel'),
                        "price": hotel.get('price', 'Price not available'),
                        "rating": hotel.get('rating', 'Rating not available'),
                        "address": hotel.get('address', 'Address not available'),
                        "image_url": hotel.get('imageUrl', ''),
                        "type": "hotel",
                        "location": location
                    })
            
            # If we don't have hotel boxes, try to extract from organic results
            if not hotels and 'organic' in data:
                for result in data['organic']:
                    if 'hotel' in result.get('title', '').lower() or 'lodging' in result.get('title', '').lower():
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
                        
                        # Create a hotel entry
                        hotels.append({
                            "name": result.get('title', 'Unknown Hotel').split(' - ')[0],
                            "price": price,
                            "rating": "Rating not available",
                            "address": result.get('snippet', 'Address not available').split('\n')[0],
                            "image_url": result.get('imageUrl', ''),
                            "type": "hotel",
                            "location": location
                        })
                        
                        # Limit to 5 results
                        if len(hotels) >= 5:
                            break
            
            return hotels
            
        except Exception as e:
            logger.error(f"Error searching hotels with SerpAPI: {str(e)}")
            return []

    def _search_with_rapid_api(self, location: str, check_in_date: str, check_out_date: str, guests: int = 2) -> List[Dict[str, Any]]:
        """
        Search for hotels using RapidAPI's hotel data providers.
        
        Args:
            location: Hotel location (city)
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            guests: Number of guests
            
        Returns:
            List of hotel options with details
        """
        try:
            # Make the request to RapidAPI
            url = "https://booking-com.p.rapidapi.com/v1/hotels/search"
            querystring = {
                "checkin_date": check_in_date,
                "checkout_date": check_out_date,
                "adults_number": str(guests),
                "units": "metric",
                "order_by": "popularity",
                "filter_by_currency": "USD",
                "locale": "en-us",
                "dest_type": "city",
                "room_number": "1",
                "dest_id": location,
                "page_number": "0",
                "include_adjacency": "true"
            }
            headers = {
                "X-RapidAPI-Key": self.rapid_api_key,
                "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
            }
            
            response = requests.request("GET", url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()
            
            # Extract hotel information from the response
            hotels = []
            
            # Parse the response based on the API structure
            if 'result' in data:
                for hotel in data['result']:
                    price = hotel.get('price_breakdown', {}).get('gross_price', {}).get('value', 'Price not available')
                    if isinstance(price, (int, float)):
                        price = f"${price}"
                    
                    hotels.append({
                        "name": hotel.get('hotel_name', 'Unknown Hotel'),
                        "price": price,
                        "rating": f"{hotel.get('review_score', 'N/A')}/10",
                        "address": hotel.get('address', 'Address not available'),
                        "image_url": hotel.get('max_photo_url', ''),
                        "type": "hotel",
                        "location": location
                    })
                    
                    # Limit to 5 results
                    if len(hotels) >= 5:
                        break
            
            return hotels
            
        except Exception as e:
            logger.error(f"Error searching hotels with RapidAPI: {str(e)}")
            return []

    def get_booking_links(self, location: str, check_in_date: str, check_out_date: str, guests: int = 2) -> List[Dict[str, str]]:
        """
        Generate booking links for hotels.
        
        Args:
            location: Hotel location (city)
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            guests: Number of guests
            
        Returns:
            List of booking links with descriptions
        """
        # Create booking links for popular hotel booking sites
        booking_links = [
            {
                "description": "Book on Booking.com",
                "url": f"https://www.booking.com/searchresults.html?ss={location.replace(' ', '+')}&checkin={check_in_date}&checkout={check_out_date}&group_adults={guests}"
            },
            {
                "description": "Book on Hotels.com",
                "url": f"https://www.hotels.com/search.do?destination-id={location.replace(' ', '+')}&q-check-in={check_in_date}&q-check-out={check_out_date}&q-rooms=1&q-room-0-adults={guests}"
            },
            {
                "description": "Book on Expedia",
                "url": f"https://www.expedia.com/Hotel-Search?destination={location.replace(' ', '+')}&startDate={check_in_date}&endDate={check_out_date}&adults={guests}"
            }
        ]
        
        return booking_links
