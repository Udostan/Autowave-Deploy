"""
MCP Client for interacting with the MCP server.
"""

import logging
import requests
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Client for interacting with the MCP server.
    """

    def __init__(self, base_url: str = "http://localhost:5011"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        print(f"Initialized MCP client with base URL: {self.base_url}")

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get a list of available tools from the MCP server.

        Returns:
            A list of tool descriptions
        """
        try:
            response = requests.get(f"{self.base_url}/api/mcp/tools")
            response.raise_for_status()
            return response.json().get("tools", [])
        except Exception as e:
            self.logger.error(f"Error getting tools: {str(e)}")
            return []

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with the given parameters.

        Args:
            tool_name: The name of the tool to execute
            params: The parameters to pass to the tool

        Returns:
            The result of the tool execution
        """
        try:
            payload = {
                "tool_name": tool_name,
                "params": params
            }
            self.logger.info(f"Executing tool {tool_name} with params: {params}")

            # Add more detailed logging
            self.logger.info(f"Making request to MCP server at: {self.base_url}/api/mcp/execute")
            self.logger.info(f"With tool: {tool_name} and parameters: {params}")

            response = requests.post(f"{self.base_url}/api/mcp/execute", json=payload, timeout=10)

            self.logger.info(f"MCP server response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"MCP server response: {result}")

                # For chat tool, handle the case where the result is directly in the response
                if tool_name == "chat" and "result" not in result and isinstance(result, str):
                    return {"result": result}

                return result
            else:
                error_message = f"Error from MCP server: {response.status_code} - {response.text}"
                self.logger.error(error_message)
                return {
                    "status": "error",
                    "error": error_message
                }
        except requests.exceptions.Timeout:
            error_message = f"Timeout when calling MCP server (waited 10 seconds)"
            self.logger.error(error_message)
            return {
                "status": "error",
                "error": error_message,
                "result": "I'm currently experiencing technical difficulties. Please try again later."
            }
        except Exception as e:
            error_message = f"Error executing tool {tool_name}: {str(e)}"
            self.logger.error(error_message)
            self.logger.error(f"Exception when calling MCP server: {error_message}")
            return {
                "status": "error",
                "error": str(e),
                "result": "I'm currently experiencing technical difficulties. Please try again later."
            }

    def search_images(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for images using the MCP server.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of image results
        """
        result = self.execute_tool("image_search", {
            "query": query,
            "num_results": num_results
        })

        if result.get("status") == "success":
            return result.get("result", [])
        else:
            self.logger.error(f"Error searching images: {result.get('error', 'Unknown error')}")
            return []

    def fetch_image(self, url: str, include_base64: bool = False) -> Dict[str, Any]:
        """
        Fetch an image from a URL using the MCP server.

        Args:
            url: The URL of the image to fetch
            include_base64: Whether to include the base64-encoded image data

        Returns:
            Image metadata and optionally the base64-encoded image
        """
        result = self.execute_tool("fetch_image", {
            "url": url,
            "include_base64": include_base64
        })

        if result.get("status") == "success":
            return result.get("result", {})
        else:
            self.logger.error(f"Error fetching image: {result.get('error', 'Unknown error')}")
            return {
                "url": url,
                "error": result.get("error", "Unknown error")
            }

    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using the MCP server.

        Args:
            query: The search query
            num_results: The number of results to return

        Returns:
            A list of search results
        """
        result = self.execute_tool("web_search", {
            "query": query,
            "num_results": num_results
        })

        if result.get("status") == "success":
            return result.get("result", [])
        else:
            self.logger.error(f"Error searching web: {result.get('error', 'Unknown error')}")
            return []

    def fetch_webpage(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract content from a webpage using the MCP server.

        Args:
            url: The URL of the webpage to fetch

        Returns:
            The extracted content from the webpage
        """
        result = self.execute_tool("fetch_webpage", {
            "url": url
        })

        if result.get("status") == "success":
            return result.get("result", {})
        else:
            self.logger.error(f"Error fetching webpage: {result.get('error', 'Unknown error')}")
            return {
                "url": url,
                "error": result.get("error", "Unknown error")
            }

    def clear_cache(self) -> bool:
        """
        Clear the tool execution cache on the MCP server.

        Returns:
            True if the cache was cleared successfully, False otherwise
        """
        try:
            response = requests.post(f"{self.base_url}/api/mcp/clear-cache")
            response.raise_for_status()
            return response.json().get("status") == "success"
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return False
