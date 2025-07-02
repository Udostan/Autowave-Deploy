"""
Direct image search module using Serper API and Google Custom Search API.
This module provides direct access to image search services without relying on the MCP server.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class DirectImageSearch:
    """
    Direct image search using Serper API and Google Custom Search API.
    """

    def __init__(self):
        """
        Initialize the direct image search.
        """
        # Load API keys from environment variables
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cx_id = os.getenv("GOOGLE_CX_ID", "334c583c1e25345d1")  # Default CX ID provided by user
        
        # Check if API keys are available
        if self.serper_api_key:
            logger.info("Serper API key found")
        else:
            logger.warning("Serper API key not found")
            
        if self.google_api_key:
            logger.info("Google API key found")
        else:
            logger.warning("Google API key not found")
            
        logger.info("Initialized DirectImageSearch")

    def search_images(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for images using available APIs.
        
        Args:
            query (str): The search query
            num_results (int): Number of results to return
            
        Returns:
            List[Dict]: List of image results
        """
        # Try Serper API first
        if self.serper_api_key:
            try:
                logger.info(f"Searching images with Serper API: {query}")
                serper_results = self._search_serper_images(query, num_results)
                if serper_results:
                    logger.info(f"Found {len(serper_results)} images with Serper API")
                    return serper_results
            except Exception as e:
                logger.error(f"Error searching images with Serper API: {str(e)}")
        
        # Fall back to Google Custom Search API
        if self.google_api_key:
            try:
                logger.info(f"Searching images with Google Custom Search API: {query}")
                google_results = self._search_google_images(query, num_results)
                if google_results:
                    logger.info(f"Found {len(google_results)} images with Google Custom Search API")
                    return google_results
            except Exception as e:
                logger.error(f"Error searching images with Google Custom Search API: {str(e)}")
        
        # Return empty list if no results found
        logger.warning(f"No images found for query: {query}")
        return []

    def _search_serper_images(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for images using Serper API.
        
        Args:
            query (str): The search query
            num_results (int): Number of results to return
            
        Returns:
            List[Dict]: List of image results
        """
        url = "https://google.serper.dev/images"
        payload = json.dumps({
            "q": query,
            "num": num_results
        })
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        images = data.get('images', [])
        
        # Format results to match our expected format
        formatted_results = []
        for img in images:
            formatted_results.append({
                'src': img.get('imageUrl', ''),
                'alt': img.get('title', ''),
                'width': '',
                'height': '',
                'extraction_method': 'serper_api',
                'relevance_score': 8.0,  # High relevance for API results
                'source_url': img.get('sourceUrl', ''),
                'source_title': img.get('source', '')
            })
        
        return formatted_results

    def _search_google_images(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for images using Google Custom Search API.
        
        Args:
            query (str): The search query
            num_results (int): Number of results to return
            
        Returns:
            List[Dict]: List of image results
        """
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            'q': query,
            'cx': self.google_cx_id,
            'key': self.google_api_key,
            'searchType': 'image',
            'num': min(num_results, 10)  # Google API limits to 10 results per request
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        # Format results to match our expected format
        formatted_results = []
        for item in items:
            image = item.get('image', {})
            formatted_results.append({
                'src': item.get('link', ''),
                'alt': item.get('title', ''),
                'width': image.get('width', ''),
                'height': image.get('height', ''),
                'extraction_method': 'google_api',
                'relevance_score': 8.0,  # High relevance for API results
                'source_url': item.get('image', {}).get('contextLink', ''),
                'source_title': item.get('displayLink', '')
            })
        
        return formatted_results
