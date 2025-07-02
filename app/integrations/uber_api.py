"""
Uber API Integration for Super Agent.

This module provides integration with the Uber API.
"""

import os
import json
import time
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode


class UberAPI:
    """Integration with the Uber API."""

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize the Uber API integration.

        Args:
            client_id (Optional[str]): The Uber API client ID. Default is None.
            client_secret (Optional[str]): The Uber API client secret. Default is None.
        """
        self.client_id = client_id or os.environ.get("UBER_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("UBER_CLIENT_SECRET")
        self.base_url = "https://api.uber.com/v1.2"
        self.auth_url = "https://login.uber.com/oauth/v2/authorize"
        self.token_url = "https://login.uber.com/oauth/v2/token"
        self.access_token = None
        self.token_expiry = 0

    def get_auth_url(self, redirect_uri: str, scopes: List[str]) -> str:
        """
        Get the authorization URL for OAuth2 authentication.

        Args:
            redirect_uri (str): The redirect URI for the OAuth2 flow.
            scopes (List[str]): The requested scopes.

        Returns:
            str: The authorization URL.
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes)
        }
        
        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange an authorization code for an access token.

        Args:
            code (str): The authorization code.
            redirect_uri (str): The redirect URI used in the authorization request.

        Returns:
            Dict[str, Any]: The token response.
        """
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri
            }
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            self.token_expiry = time.time() + token_data.get("expires_in", 0)
            
            return token_data
        except Exception as e:
            print(f"Error exchanging code for token: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def set_access_token(self, access_token: str, expires_in: int = 3600) -> None:
        """
        Set the access token manually.

        Args:
            access_token (str): The access token.
            expires_in (int): The token expiry time in seconds. Default is 3600.
        """
        self.access_token = access_token
        self.token_expiry = time.time() + expires_in

    def is_token_valid(self) -> bool:
        """
        Check if the access token is valid.

        Returns:
            bool: Whether the access token is valid.
        """
        return self.access_token is not None and time.time() < self.token_expiry

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                     data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Uber API.

        Args:
            method (str): The HTTP method.
            endpoint (str): The API endpoint.
            params (Optional[Dict[str, Any]]): The query parameters. Default is None.
            data (Optional[Dict[str, Any]]): The request body. Default is None.

        Returns:
            Dict[str, Any]: The API response.
        """
        if not self.is_token_valid():
            return {
                "success": False,
                "error": "Access token is invalid or expired."
            }
        
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
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
            print(f"Error making request to Uber API: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_products(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get available Uber products at a location.

        Args:
            latitude (float): The latitude.
            longitude (float): The longitude.

        Returns:
            Dict[str, Any]: The available products.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude
        }
        
        return self._make_request("GET", "/products", params=params)

    def get_price_estimates(self, start_latitude: float, start_longitude: float, 
                           end_latitude: float, end_longitude: float) -> Dict[str, Any]:
        """
        Get price estimates for a trip.

        Args:
            start_latitude (float): The start latitude.
            start_longitude (float): The start longitude.
            end_latitude (float): The end latitude.
            end_longitude (float): The end longitude.

        Returns:
            Dict[str, Any]: The price estimates.
        """
        params = {
            "start_latitude": start_latitude,
            "start_longitude": start_longitude,
            "end_latitude": end_latitude,
            "end_longitude": end_longitude
        }
        
        return self._make_request("GET", "/estimates/price", params=params)

    def get_time_estimates(self, start_latitude: float, start_longitude: float, 
                          product_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get time estimates for a pickup.

        Args:
            start_latitude (float): The start latitude.
            start_longitude (float): The start longitude.
            product_id (Optional[str]): The product ID. Default is None.

        Returns:
            Dict[str, Any]: The time estimates.
        """
        params = {
            "start_latitude": start_latitude,
            "start_longitude": start_longitude
        }
        
        if product_id:
            params["product_id"] = product_id
        
        return self._make_request("GET", "/estimates/time", params=params)

    def request_ride(self, product_id: str, start_latitude: float, start_longitude: float, 
                    end_latitude: float, end_longitude: float, 
                    fare_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Request a ride.

        Args:
            product_id (str): The product ID.
            start_latitude (float): The start latitude.
            start_longitude (float): The start longitude.
            end_latitude (float): The end latitude.
            end_longitude (float): The end longitude.
            fare_id (Optional[str]): The fare ID. Default is None.

        Returns:
            Dict[str, Any]: The ride request response.
        """
        data = {
            "product_id": product_id,
            "start_latitude": start_latitude,
            "start_longitude": start_longitude,
            "end_latitude": end_latitude,
            "end_longitude": end_longitude
        }
        
        if fare_id:
            data["fare_id"] = fare_id
        
        return self._make_request("POST", "/requests", data=data)

    def get_ride_details(self, request_id: str) -> Dict[str, Any]:
        """
        Get details of a ride.

        Args:
            request_id (str): The ride request ID.

        Returns:
            Dict[str, Any]: The ride details.
        """
        return self._make_request("GET", f"/requests/{request_id}")

    def cancel_ride(self, request_id: str) -> Dict[str, Any]:
        """
        Cancel a ride.

        Args:
            request_id (str): The ride request ID.

        Returns:
            Dict[str, Any]: The cancellation response.
        """
        return self._make_request("DELETE", f"/requests/{request_id}")

    def get_ride_map(self, request_id: str) -> Dict[str, Any]:
        """
        Get the map for a ride.

        Args:
            request_id (str): The ride request ID.

        Returns:
            Dict[str, Any]: The ride map.
        """
        return self._make_request("GET", f"/requests/{request_id}/map")

    def get_ride_receipt(self, request_id: str) -> Dict[str, Any]:
        """
        Get the receipt for a ride.

        Args:
            request_id (str): The ride request ID.

        Returns:
            Dict[str, Any]: The ride receipt.
        """
        return self._make_request("GET", f"/requests/{request_id}/receipt")

    def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the user profile.

        Returns:
            Dict[str, Any]: The user profile.
        """
        return self._make_request("GET", "/me")

    def get_user_activity(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get the user's activity history.

        Args:
            limit (int): The maximum number of activities to return. Default is 50.
            offset (int): The offset for pagination. Default is 0.

        Returns:
            Dict[str, Any]: The user's activity history.
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        return self._make_request("GET", "/history", params=params)
