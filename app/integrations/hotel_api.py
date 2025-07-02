"""
Hotel API Integration for Super Agent.

This module provides integration with hotel booking APIs.
"""

import os
import json
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class HotelAPI:
    """Integration with hotel booking APIs."""

    def __init__(self, api_key: Optional[str] = None, provider: str = "booking"):
        """
        Initialize the hotel API integration.

        Args:
            api_key (Optional[str]): The API key. Default is None.
            provider (str): The API provider. Default is "booking".
        """
        self.api_key = api_key or os.environ.get("HOTEL_API_KEY")
        self.provider = provider
        self.base_urls = {
            "booking": "https://booking-com.p.rapidapi.com",
            "amadeus": "https://test.api.amadeus.com/v2",
            "hotels": "https://hotels-com-provider.p.rapidapi.com/v1"
        }
        self.base_url = self.base_urls.get(provider, self.base_urls["booking"])
        self.session_token = None
        self.token_expiry = 0

    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers for API requests.

        Returns:
            Dict[str, str]: The headers.
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.provider == "booking" or self.provider == "hotels":
            headers["X-RapidAPI-Key"] = self.api_key
            headers["X-RapidAPI-Host"] = self.base_url.replace("https://", "")
        elif self.provider == "amadeus":
            headers["Authorization"] = f"Bearer {self.session_token}"
        
        return headers

    def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with the API provider.

        Returns:
            Dict[str, Any]: The authentication response.
        """
        if self.provider == "amadeus":
            try:
                # Amadeus requires OAuth2 authentication
                auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
                data = {
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": os.environ.get("AMADEUS_CLIENT_SECRET")
                }
                
                response = requests.post(auth_url, data=data)
                response.raise_for_status()
                
                token_data = response.json()
                self.session_token = token_data.get("access_token")
                self.token_expiry = time.time() + token_data.get("expires_in", 0)
                
                return {
                    "success": True,
                    "data": token_data
                }
            except Exception as e:
                print(f"Error authenticating with Amadeus: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
        else:
            # Other providers use API key authentication
            return {
                "success": True,
                "message": "API key authentication is used."
            }

    def is_token_valid(self) -> bool:
        """
        Check if the session token is valid.

        Returns:
            bool: Whether the session token is valid.
        """
        if self.provider == "amadeus":
            return self.session_token is not None and time.time() < self.token_expiry
        else:
            return self.api_key is not None

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                     data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the API.

        Args:
            method (str): The HTTP method.
            endpoint (str): The API endpoint.
            params (Optional[Dict[str, Any]]): The query parameters. Default is None.
            data (Optional[Dict[str, Any]]): The request body. Default is None.

        Returns:
            Dict[str, Any]: The API response.
        """
        if not self.is_token_valid():
            auth_result = self.authenticate()
            if not auth_result.get("success", False):
                return auth_result
        
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            headers = self._get_headers()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported HTTP method: {method}"
                }
            
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            print(f"Error making request to {self.provider} API: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def search_hotels(self, location: str, check_in: str, check_out: str, 
                     adults: int = 2, children: int = 0, rooms: int = 1, 
                     min_price: Optional[float] = None, max_price: Optional[float] = None, 
                     star_rating: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for hotels.

        Args:
            location (str): The location (city, region, or coordinates).
            check_in (str): The check-in date (YYYY-MM-DD).
            check_out (str): The check-out date (YYYY-MM-DD).
            adults (int): The number of adults. Default is 2.
            children (int): The number of children. Default is 0.
            rooms (int): The number of rooms. Default is 1.
            min_price (Optional[float]): The minimum price per night. Default is None.
            max_price (Optional[float]): The maximum price per night. Default is None.
            star_rating (Optional[int]): The minimum star rating. Default is None.

        Returns:
            Dict[str, Any]: The search results.
        """
        if self.provider == "booking":
            endpoint = "v1/hotels/search"
            params = {
                "dest_id": location,
                "order_by": "popularity",
                "filter_by_currency": "USD",
                "locale": "en-us",
                "checkout_date": check_out,
                "checkin_date": check_in,
                "adults_number": adults,
                "room_number": rooms,
                "units": "metric",
                "page_number": "0",
                "include_adjacency": "true"
            }
            
            if children > 0:
                params["children_number"] = children
            
            if min_price is not None:
                params["price_min"] = min_price
            
            if max_price is not None:
                params["price_max"] = max_price
            
            if star_rating is not None:
                params["filter_by_review_score"] = star_rating
            
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "amadeus":
            endpoint = "shopping/hotel-offers"
            params = {
                "cityCode": location,
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "adults": adults,
                "roomQuantity": rooms,
                "currency": "USD"
            }
            
            if min_price is not None or max_price is not None:
                price_range = []
                if min_price is not None:
                    price_range.append(str(min_price))
                else:
                    price_range.append("0")
                
                if max_price is not None:
                    price_range.append(str(max_price))
                else:
                    price_range.append("100000")
                
                params["priceRange"] = "-".join(price_range)
            
            if star_rating is not None:
                params["ratings"] = star_rating
            
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "hotels":
            endpoint = "hotels/search"
            params = {
                "q": location,
                "locale": "en_US",
                "currency": "USD",
                "checkin_date": check_in,
                "checkout_date": check_out,
                "sort_order": "STAR_RATING_HIGHEST_FIRST",
                "adults_number": adults,
                "page_number": "1"
            }
            
            if children > 0:
                params["children_ages"] = ",".join(["10"] * children)
            
            if rooms > 1:
                params["rooms_number"] = rooms
            
            if star_rating is not None:
                params["star_rating_ids"] = ",".join([str(i) for i in range(star_rating, 6)])
            
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }

    def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """
        Get details of a hotel.

        Args:
            hotel_id (str): The hotel ID.

        Returns:
            Dict[str, Any]: The hotel details.
        """
        if self.provider == "booking":
            endpoint = "v1/hotels/data"
            params = {
                "hotel_id": hotel_id,
                "locale": "en-us"
            }
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "amadeus":
            endpoint = f"shopping/hotel-offers/by-hotel"
            params = {
                "hotelId": hotel_id
            }
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "hotels":
            endpoint = "hotels/get-details"
            params = {
                "hotel_id": hotel_id,
                "locale": "en_US",
                "currency": "USD"
            }
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }

    def get_hotel_photos(self, hotel_id: str) -> Dict[str, Any]:
        """
        Get photos of a hotel.

        Args:
            hotel_id (str): The hotel ID.

        Returns:
            Dict[str, Any]: The hotel photos.
        """
        if self.provider == "booking":
            endpoint = "v1/hotels/photos"
            params = {
                "hotel_id": hotel_id,
                "locale": "en-us"
            }
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "hotels":
            endpoint = "hotels/get-details"
            params = {
                "hotel_id": hotel_id,
                "locale": "en_US",
                "currency": "USD"
            }
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }

    def get_hotel_reviews(self, hotel_id: str, page: int = 1, 
                         page_size: int = 10) -> Dict[str, Any]:
        """
        Get reviews of a hotel.

        Args:
            hotel_id (str): The hotel ID.
            page (int): The page number. Default is 1.
            page_size (int): The page size. Default is 10.

        Returns:
            Dict[str, Any]: The hotel reviews.
        """
        if self.provider == "booking":
            endpoint = "v1/hotels/reviews"
            params = {
                "hotel_id": hotel_id,
                "locale": "en-us",
                "sort_type": "SORT_MOST_RELEVANT",
                "page_number": page
            }
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "hotels":
            endpoint = "hotels/get-reviews"
            params = {
                "hotel_id": hotel_id,
                "locale": "en_US",
                "page_number": page
            }
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }

    def get_location_id(self, query: str) -> Dict[str, Any]:
        """
        Get location ID by query.

        Args:
            query (str): The location query.

        Returns:
            Dict[str, Any]: The location ID.
        """
        if self.provider == "booking":
            endpoint = "v1/hotels/locations"
            params = {
                "name": query,
                "locale": "en-us"
            }
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "amadeus":
            endpoint = "reference-data/locations/hotels"
            params = {
                "keyword": query,
                "subType": "HOTEL_LEISURE"
            }
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "hotels":
            endpoint = "locations/search"
            params = {
                "q": query,
                "locale": "en_US"
            }
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }

    def get_hotel_availability(self, hotel_id: str, check_in: str, 
                              check_out: str, adults: int = 2, 
                              children: int = 0, rooms: int = 1) -> Dict[str, Any]:
        """
        Get availability of a hotel.

        Args:
            hotel_id (str): The hotel ID.
            check_in (str): The check-in date (YYYY-MM-DD).
            check_out (str): The check-out date (YYYY-MM-DD).
            adults (int): The number of adults. Default is 2.
            children (int): The number of children. Default is 0.
            rooms (int): The number of rooms. Default is 1.

        Returns:
            Dict[str, Any]: The hotel availability.
        """
        if self.provider == "booking":
            endpoint = "v1/hotels/room-list"
            params = {
                "hotel_id": hotel_id,
                "locale": "en-us",
                "checkout_date": check_out,
                "checkin_date": check_in,
                "adults_number": adults,
                "currency": "USD",
                "units": "metric"
            }
            
            if children > 0:
                params["children_number"] = children
            
            if rooms > 1:
                params["room_number"] = rooms
            
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "amadeus":
            endpoint = "shopping/hotel-offers/by-hotel"
            params = {
                "hotelId": hotel_id,
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "adults": adults,
                "roomQuantity": rooms,
                "currency": "USD"
            }
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "hotels":
            endpoint = "hotels/get-offers"
            params = {
                "hotel_id": hotel_id,
                "locale": "en_US",
                "currency": "USD",
                "checkin_date": check_in,
                "checkout_date": check_out,
                "adults_number": adults
            }
            
            if children > 0:
                params["children_ages"] = ",".join(["10"] * children)
            
            if rooms > 1:
                params["rooms_number"] = rooms
            
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }
