"""
Image search and fetch tools for the MCP server.
"""

import os
import json
import logging
import requests
import base64
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class ImageTools:
    """
    Tools for searching and fetching images.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.serper_api_key = os.environ.get("SERPER_API_KEY", "")
        self.google_api_key = os.environ.get("GOOGLE_API_KEY", "")
        self.google_cx = os.environ.get("GOOGLE_CX", "")
        self.unsplash_api_key = os.environ.get("UNSPLASH_API_KEY", "")

        # Check if we have at least one API key
        if not self.serper_api_key and not (self.google_api_key and self.google_cx) and not self.unsplash_api_key:
            self.logger.warning("No API keys found for image search. Using fallback methods.")

    def search_images(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for images using available APIs.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of image results with URLs and metadata
        """
        # Enhance the query for better image results
        enhanced_query = self._enhance_image_query(query)
        self.logger.info(f"Enhanced image query: {enhanced_query}")

        # Try different APIs in order of preference
        results = []

        # Try to get images from multiple sources for diversity
        if self.serper_api_key:
            serper_results = self._search_images_serper(enhanced_query, num_results)
            if serper_results:
                results.extend(serper_results)

        if self.google_api_key and self.google_cx and (not results or len(results) < num_results):
            google_results = self._search_images_google(enhanced_query, num_results)
            if google_results:
                # Add only new images that aren't already in results
                existing_urls = {r.get('src') for r in results}
                new_results = [r for r in google_results if r.get('src') not in existing_urls]
                results.extend(new_results)

        if self.unsplash_api_key and (not results or len(results) < num_results):
            unsplash_results = self._search_images_unsplash(enhanced_query, num_results)
            if unsplash_results:
                # Add only new images that aren't already in results
                existing_urls = {r.get('src') for r in results}
                new_results = [r for r in unsplash_results if r.get('src') not in existing_urls]
                results.extend(new_results)

        # If we still don't have enough results, use fallback
        if not results:
            results = self._search_images_fallback(enhanced_query, num_results)

        # Filter out low-quality or irrelevant images
        filtered_results = self._filter_image_results(results, query)

        # Return the requested number of results
        return filtered_results[:num_results]

    def _search_images_serper(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for images using Serper API.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of image results
        """
        try:
            url = "https://google.serper.dev/images"
            payload = json.dumps({
                "q": query,
                "num": num_results
            })
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status()

            data = response.json()
            images = data.get("images", [])

            results = []
            for img in images:
                results.append({
                    "src": img.get("imageUrl", ""),
                    "alt": img.get("title", query),
                    "title": img.get("title", ""),
                    "source": img.get("source", ""),
                    "width": img.get("width", 0),
                    "height": img.get("height", 0)
                })

            return results
        except Exception as e:
            self.logger.error(f"Error searching images with Serper: {str(e)}")
            return []

    def _search_images_google(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for images using Google Custom Search API.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of image results
        """
        try:
            url = f"https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_cx,
                "q": query,
                "searchType": "image",
                "num": min(num_results, 10)  # Google API max is 10
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            results = []
            for item in items:
                image = item.get("image", {})
                results.append({
                    "src": item.get("link", ""),
                    "alt": item.get("title", query),
                    "title": item.get("title", ""),
                    "source": item.get("displayLink", ""),
                    "width": image.get("width", 0),
                    "height": image.get("height", 0)
                })

            return results
        except Exception as e:
            self.logger.error(f"Error searching images with Google: {str(e)}")
            return []

    def _search_images_unsplash(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for images using Unsplash API.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of image results
        """
        try:
            url = f"https://api.unsplash.com/search/photos"
            params = {
                "client_id": self.unsplash_api_key,
                "query": query,
                "per_page": num_results
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("results", []):
                results.append({
                    "src": item.get("urls", {}).get("regular", ""),
                    "alt": item.get("alt_description", query),
                    "title": item.get("description", ""),
                    "source": "Unsplash",
                    "width": item.get("width", 0),
                    "height": item.get("height", 0),
                    "user": item.get("user", {}).get("name", "")
                })

            return results
        except Exception as e:
            self.logger.error(f"Error searching images with Unsplash: {str(e)}")
            return []

    def _search_images_fallback(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fallback method for image search when no API keys are available.
        Uses Unsplash source or placeholder images with the query text.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of image results
        """
        results = []
        encoded_query = quote_plus(query)

        # First try Unsplash Source which doesn't require an API key
        try:
            for i in range(min(num_results, 5)):
                # Add a random seed to get different images for the same query
                import random
                seed = random.randint(1, 1000)

                results.append({
                    "src": f"https://source.unsplash.com/800x400/?{encoded_query}&sig={seed}",
                    "alt": query,
                    "title": f"Image for {query}",
                    "source": "Unsplash Source",
                    "width": 800,
                    "height": 400
                })
        except Exception as e:
            self.logger.error(f"Error using Unsplash Source: {str(e)}")

        # If we couldn't get any results, use placeholder images as a last resort
        if not results:
            for i in range(min(num_results, 5)):
                # Use different colors for variety
                colors = ["f5f5f5/333333", "e0e0e0/555555", "d0d0d0/444444", "cccccc/666666", "bbbbbb/777777"]
                color = colors[i % len(colors)]

                results.append({
                    "src": f"https://placehold.co/800x400/{color}?text={encoded_query}",
                    "alt": query,
                    "title": f"Placeholder image for {query}",
                    "source": "Placeholder",
                    "width": 800,
                    "height": 400
                })

        return results

    def _enhance_image_query(self, query: str) -> str:
        """
        Enhance the image search query for better results.

        Args:
            query: The original search query

        Returns:
            An enhanced query for better image results
        """
        # Don't modify queries that are already specific
        if len(query.split()) > 8:
            return query

        # Add qualifiers for better image quality and relevance
        quality_terms = [
            'high quality',
            'professional',
            'high resolution',
            'detailed',
            'clear image',
            'stock photo',
            'professional photo'
        ]

        # Add a random quality term to the query
        import random
        selected_term = random.choice(quality_terms)

        # Check if the query is asking for a specific type of image
        if 'diagram' in query.lower() or 'chart' in query.lower():
            enhanced_query = f"{query} professional infographic"
        elif 'person' in query.lower() or 'people' in query.lower():
            enhanced_query = f"{query} professional portrait"
        elif 'product' in query.lower():
            enhanced_query = f"{query} professional product photo"
        elif 'landscape' in query.lower() or 'scenery' in query.lower():
            enhanced_query = f"{query} scenic view high resolution"
        elif 'building' in query.lower() or 'architecture' in query.lower():
            enhanced_query = f"{query} architectural photography"
        elif 'food' in query.lower() or 'meal' in query.lower() or 'dish' in query.lower():
            enhanced_query = f"{query} professional food photography"
        else:
            enhanced_query = f"{query} {selected_term}"

        return enhanced_query

    def _filter_image_results(self, results: List[Dict[str, Any]], original_query: str) -> List[Dict[str, Any]]:
        """
        Filter image results to remove low-quality or irrelevant images.

        Args:
            results: The list of image results to filter
            original_query: The original search query

        Returns:
            A filtered list of image results
        """
        if not results:
            return []

        filtered_results = []

        # Extract keywords from the original query
        keywords = set(original_query.lower().split())

        for result in results:
            # Skip images without a source URL
            if not result.get('src'):
                continue

            # Check if the image has a title or alt text
            title = result.get('title', '').lower()
            alt = result.get('alt', '').lower()

            # Check if the image has dimensions
            width = result.get('width', 0)
            height = result.get('height', 0)

            # Skip very small images
            if width and height and (width < 200 or height < 200):
                continue

            # Check if the image title or alt text contains any keywords from the query
            relevant = False
            for keyword in keywords:
                if len(keyword) > 3 and (keyword in title or keyword in alt):
                    relevant = True
                    break

            # If the image is relevant or we don't have title/alt to check, include it
            if relevant or (not title and not alt):
                filtered_results.append(result)

        # If filtering removed too many results, return the original results
        if len(filtered_results) < len(results) / 2:
            return results

        return filtered_results

    def fetch_image(self, url: str, include_base64: bool = False) -> Dict[str, Any]:
        """
        Fetch an image from a URL and return metadata.

        Args:
            url: The URL of the image to fetch
            include_base64: Whether to include the base64-encoded image data

        Returns:
            Image metadata and optionally the base64-encoded image
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                raise ValueError(f"URL does not point to an image: {content_type}")

            result = {
                "url": url,
                "content_type": content_type,
                "size": len(response.content)
            }

            if include_base64:
                base64_data = base64.b64encode(response.content).decode('utf-8')
                result["base64"] = f"data:{content_type};base64,{base64_data}"

            return result
        except Exception as e:
            self.logger.error(f"Error fetching image from {url}: {str(e)}")
            return {
                "url": url,
                "error": str(e)
            }
