"""
MCP (Model Context Protocol) Server implementation.
This server provides tools for AI models to interact with external services.
"""

import json
import logging
import traceback
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger(__name__)

class MCPServer:
    """
    Model Context Protocol Server that manages tools and their execution.
    """

    def __init__(self):
        self.tools = {}
        self.tool_descriptions = {}
        self.cache = {}
        self.logger = logging.getLogger(__name__)

    def register_tool(self, name: str, func: Callable, description: str) -> None:
        """
        Register a new tool with the MCP server.

        Args:
            name: The name of the tool
            func: The function to call when the tool is invoked
            description: A description of what the tool does
        """
        self.tools[name] = func
        self.tool_descriptions[name] = description
        self.logger.info(f"Registered tool: {name}")

    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """
        Get descriptions of all registered tools.

        Returns:
            A list of tool descriptions
        """
        return [
            {
                "name": name,
                "description": description
            }
            for name, description in self.tool_descriptions.items()
        ]

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with the given parameters.

        Args:
            tool_name: The name of the tool to execute
            params: The parameters to pass to the tool

        Returns:
            The result of the tool execution
        """
        if tool_name not in self.tools:
            return {
                "status": "error",
                "error": f"Tool '{tool_name}' not found"
            }

        try:
            # Create a cache key from the tool name and parameters
            cache_key = self._create_cache_key(tool_name, params)

            # Check if we have a cached result
            if cache_key in self.cache:
                self.logger.info(f"Using cached result for {tool_name}")
                return {
                    "status": "success",
                    "result": self.cache[cache_key],
                    "cached": True
                }

            # Execute the tool
            self.logger.info(f"Executing tool: {tool_name} with params: {params}")
            result = self.tools[tool_name](**params)

            # Cache the result
            self.cache[cache_key] = result

            # For the chat tool, we always want to return a success status
            # even if the result is an error message from one of the providers
            # This allows the fallback mechanism to work properly
            return {
                "status": "success",
                "result": result,
                "cached": False
            }
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            self.logger.error(traceback.format_exc())

            # For the chat tool, we want to return the error message as the result
            # This allows the fallback mechanism to work properly
            if tool_name == "chat":
                error_message = f"Error: {str(e)}"
                self.cache[cache_key] = error_message
                return {
                    "status": "success",
                    "result": error_message,
                    "cached": False,
                    "error_info": str(e)  # Include the error info for debugging
                }
            else:
                return {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }

    def _create_cache_key(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        Create a cache key from the tool name and parameters.

        Args:
            tool_name: The name of the tool
            params: The parameters passed to the tool

        Returns:
            A string cache key
        """
        # Sort the parameters to ensure consistent cache keys
        sorted_params = json.dumps(params, sort_keys=True)
        return f"{tool_name}:{sorted_params}"

    def clear_cache(self) -> None:
        """Clear the tool execution cache."""
        self.cache = {}
        self.logger.info("Cleared tool cache")
