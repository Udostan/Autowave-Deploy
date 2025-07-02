"""
Flight API Integration for Super Agent.

This module provides integration with flight booking APIs.
"""

import os
import json
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class FlightAPI:
    """Integration with flight booking APIs."""

    def __init__(self, api_key: Optional[str] = None, provider: str = "skyscanner"):
        """
        Initialize the flight API integration.

        Args:
            api_key (Optional[str]): The API key. Default is None.
            provider (str): The API provider. Default is "skyscanner".
        """
        self.api_key = api_key or os.environ.get("FLIGHT_API_KEY")
        self.provider = provider
        self.base_urls = {
            "skyscanner": "https://partners.api.skyscanner.net/apiservices",
            "amadeus": "https://test.api.amadeus.com/v2",
            "kiwi": "https://api.tequila.kiwi.com"
        }
        self.base_url = self.base_urls.get(provider, self.base_urls["skyscanner"])
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
        
        if self.provider == "skyscanner":
            headers["x-api-key"] = self.api_key
        elif self.provider == "amadeus":
            headers["Authorization"] = f"Bearer {self.session_token}"
        elif self.provider == "kiwi":
            headers["apikey"] = self.api_key
        
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

    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: Optional[str] = None, adults: int = 1, 
                      children: int = 0, infants: int = 0, 
                      cabin_class: str = "economy") -> Dict[str, Any]:
        """
        Search for flights.

        Args:
            origin (str): The origin location code (e.g., "LHR").
            destination (str): The destination location code (e.g., "JFK").
            departure_date (str): The departure date (YYYY-MM-DD).
            return_date (Optional[str]): The return date (YYYY-MM-DD). Default is None.
            adults (int): The number of adults. Default is 1.
            children (int): The number of children. Default is 0.
            infants (int): The number of infants. Default is 0.
            cabin_class (str): The cabin class. Default is "economy".

        Returns:
            Dict[str, Any]: The search results.
        """
        if self.provider == "skyscanner":
            endpoint = "flights/live/search/create"
            data = {
                "query": {
                    "market": "UK",
                    "locale": "en-GB",
                    "currency": "GBP",
                    "queryLegs": [
                        {
                            "originPlaceId": {"iata": origin},
                            "destinationPlaceId": {"iata": destination},
                            "date": {
                                "year": int(departure_date.split("-")[0]),
                                "month": int(departure_date.split("-")[1]),
                                "day": int(departure_date.split("-")[2])
                            }
                        }
                    ],
                    "adults": adults,
                    "childrenAges": [5] * children,
                    "cabinClass": cabin_class.upper(),
                    "excludedAgentsIds": [],
                    "excludedCarriersIds": [],
                    "includedAgentsIds": [],
                    "includedCarriersIds": []
                }
            }
            
            if return_date:
                data["query"]["queryLegs"].append({
                    "originPlaceId": {"iata": destination},
                    "destinationPlaceId": {"iata": origin},
                    "date": {
                        "year": int(return_date.split("-")[0]),
                        "month": int(return_date.split("-")[1]),
                        "day": int(return_date.split("-")[2])
                    }
                })
            
            return self._make_request("POST", endpoint, data=data)
        
        elif self.provider == "amadeus":
            endpoint = "shopping/flight-offers"
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "children": children,
                "infants": infants,
                "travelClass": cabin_class.upper()
            }
            
            if return_date:
                params["returnDate"] = return_date
            
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "kiwi":
            endpoint = "v2/search"
            params = {
                "fly_from": origin,
                "fly_to": destination,
                "date_from": departure_date,
                "date_to": departure_date,
                "adults": adults,
                "children": children,
                "infants": infants,
                "selected_cabins": cabin_class.lower(),
                "curr": "USD",
                "locale": "en"
            }
            
            if return_date:
                params["return_from"] = return_date
                params["return_to"] = return_date
            
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }

    def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """
        Get details of a flight.

        Args:
            flight_id (str): The flight ID.

        Returns:
            Dict[str, Any]: The flight details.
        """
        if self.provider == "skyscanner":
            endpoint = f"flights/live/search/poll/{flight_id}"
            return self._make_request("POST", endpoint)
        
        elif self.provider == "amadeus":
            endpoint = f"shopping/flight-offers/{flight_id}"
            return self._make_request("GET", endpoint)
        
        elif self.provider == "kiwi":
            endpoint = f"booking/check_flights"
            data = {
                "booking_token": flight_id,
                "bnum": 1,
                "pnum": 1
            }
            return self._make_request("POST", endpoint, data=data)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }

    def get_cheapest_quotes(self, origin: str, destination: str, 
                           outbound_date: str, inbound_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the cheapest quotes for a route.

        Args:
            origin (str): The origin location code (e.g., "LHR").
            destination (str): The destination location code (e.g., "JFK").
            outbound_date (str): The outbound date (YYYY-MM-DD).
            inbound_date (Optional[str]): The inbound date (YYYY-MM-DD). Default is None.

        Returns:
            Dict[str, Any]: The cheapest quotes.
        """
        if self.provider == "skyscanner":
            endpoint = "browsequotes/v1.0/UK/GBP/en-GB"
            endpoint += f"/{origin}/{destination}/{outbound_date}"
            
            if inbound_date:
                endpoint += f"/{inbound_date}"
            
            return self._make_request("GET", endpoint)
        
        elif self.provider == "kiwi":
            endpoint = "v2/search"
            params = {
                "fly_from": origin,
                "fly_to": destination,
                "date_from": outbound_date,
                "date_to": outbound_date,
                "curr": "USD",
                "locale": "en",
                "sort": "price",
                "limit": 1
            }
            
            if inbound_date:
                params["return_from"] = inbound_date
                params["return_to"] = inbound_date
            
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }

    def get_routes(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        Get available routes between two locations.

        Args:
            origin (str): The origin location code (e.g., "LHR").
            destination (str): The destination location code (e.g., "JFK").

        Returns:
            Dict[str, Any]: The available routes.
        """
        if self.provider == "skyscanner":
            endpoint = f"browseroutes/v1.0/UK/GBP/en-GB/{origin}/{destination}/anytime/anytime"
            return self._make_request("GET", endpoint)
        
        elif self.provider == "kiwi":
            endpoint = "v2/search"
            params = {
                "fly_from": origin,
                "fly_to": destination,
                "date_from": (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y"),
                "date_to": (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y"),
                "curr": "USD",
                "locale": "en",
                "sort": "price",
                "limit": 10
            }
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }

    def get_dates(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        Get available dates for flights between two locations.

        Args:
            origin (str): The origin location code (e.g., "LHR").
            destination (str): The destination location code (e.g., "JFK").

        Returns:
            Dict[str, Any]: The available dates.
        """
        if self.provider == "skyscanner":
            endpoint = f"browsedates/v1.0/UK/GBP/en-GB/{origin}/{destination}/anytime/anytime"
            return self._make_request("GET", endpoint)
        
        elif self.provider == "kiwi":
            endpoint = "v2/search"
            params = {
                "fly_from": origin,
                "fly_to": destination,
                "date_from": (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y"),
                "date_to": (datetime.now() + timedelta(days=90)).strftime("%d/%m/%Y"),
                "curr": "USD",
                "locale": "en",
                "sort": "date",
                "limit": 30
            }
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }

    def get_location(self, query: str) -> Dict[str, Any]:
        """
        Get location information by query.

        Args:
            query (str): The location query.

        Returns:
            Dict[str, Any]: The location information.
        """
        if self.provider == "skyscanner":
            endpoint = "autosuggest/v1.0/UK/GBP/en-GB"
            params = {
                "query": query
            }
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "amadeus":
            endpoint = "reference-data/locations"
            params = {
                "keyword": query,
                "subType": "CITY,AIRPORT"
            }
            return self._make_request("GET", endpoint, params=params)
        
        elif self.provider == "kiwi":
            endpoint = "locations/query"
            params = {
                "term": query,
                "locale": "en-US",
                "location_types": "airport",
                "limit": 10
            }
            return self._make_request("GET", endpoint, params=params)
        
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {self.provider}"
            }
