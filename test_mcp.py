"""
Test script for the MCP server.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Load environment variables
load_dotenv()

from app.mcp.server import MCPServer
from app.mcp.tool_registry import register_tools

def test_mcp_server():
    """Test the MCP server functionality."""
    print("Testing MCP server...")
    
    # Create MCP server
    mcp_server = MCPServer()
    
    # Register tools
    register_tools(mcp_server)
    
    # Get tool descriptions
    tools = mcp_server.get_tool_descriptions()
    print(f"Registered tools: {json.dumps(tools, indent=2)}")
    
    # Test image search
    print("\nTesting image search...")
    result = mcp_server.execute_tool("image_search", {
        "query": "Eiffel Tower",
        "num_results": 2
    })
    print(f"Image search result: {json.dumps(result, indent=2)}")
    
    # Test web search
    print("\nTesting web search...")
    result = mcp_server.execute_tool("web_search", {
        "query": "Paris tourist attractions",
        "num_results": 2
    })
    print(f"Web search result: {json.dumps(result, indent=2)}")
    
    print("\nMCP server tests completed.")

if __name__ == "__main__":
    test_mcp_server()
