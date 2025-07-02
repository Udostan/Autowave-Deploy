"""
Enhanced MCP Client that supports both legacy MCP server and Context 7 MCP server.
This allows Prime Agent to use both existing tools and new advanced tools.
"""

import logging
import requests
from typing import Dict, Any, List
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)

class EnhancedMCPClient:
    """
    Enhanced MCP Client that routes tools between legacy and Context 7 servers.
    """
    
    def __init__(self, legacy_url: str = "http://localhost:5011", context7_url: str = "http://localhost:5012"):
        self.legacy_client = MCPClient(legacy_url)
        self.context7_url = context7_url
        self.logger = logging.getLogger(__name__)
        
        # Define which tools use Context 7
        self.context7_tools = {
            "restaurant_booker",
            "real_estate_scout", 
            "event_ticket_finder",
            "job_application_assistant",
            "price_comparison_hunter",
            "medical_appointment_scheduler",
            "government_services_navigator",
            "social_media_manager",
            "package_tracker",
            "financial_account_monitor"
        }
        
        # Check server availability
        self.context7_available = self._check_context7_availability()
        
        logger.info(f"Enhanced MCP Client initialized")
        logger.info(f"Legacy server: {legacy_url}")
        logger.info(f"Context 7 server: {context7_url} (Available: {self.context7_available})")
    
    def _check_context7_availability(self) -> bool:
        """Check if Context 7 server is available."""
        try:
            response = requests.get(f"{self.context7_url}/api/mcp/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("server") == "context7":
                    logger.info("✅ Context 7 MCP server is available")
                    return True
            return False
        except Exception as e:
            logger.warning(f"⚠️ Context 7 server not available: {e}")
            return False
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tools from both servers."""
        tools = []
        
        # Get legacy tools
        try:
            legacy_tools = self.legacy_client.get_tools()
            for tool in legacy_tools:
                tool["server"] = "legacy"
            tools.extend(legacy_tools)
        except Exception as e:
            logger.error(f"Error getting legacy tools: {e}")
        
        # Get Context 7 tools
        if self.context7_available:
            try:
                response = requests.get(f"{self.context7_url}/api/mcp/tools", timeout=5)
                if response.status_code == 200:
                    context7_tools = response.json().get("tools", [])
                    for tool in context7_tools:
                        tool["server"] = "context7"
                    tools.extend(context7_tools)
            except Exception as e:
                logger.error(f"Error getting Context 7 tools: {e}")
        
        logger.info(f"Total tools available: {len(tools)}")
        return tools
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool using the appropriate server."""
        
        # Route to Context 7 if it's a Context 7 tool and server is available
        if tool_name in self.context7_tools and self.context7_available:
            return self._execute_context7_tool(tool_name, params)
        
        # Route to legacy server for all other tools
        return self._execute_legacy_tool(tool_name, params)
    
    def _execute_context7_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on Context 7 server."""
        try:
            payload = {
                "tool_name": tool_name,
                "params": params
            }
            
            logger.info(f"Executing Context 7 tool: {tool_name}")
            response = requests.post(f"{self.context7_url}/api/mcp/execute", json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Context 7 tool {tool_name} executed successfully")
                return result
            else:
                error_msg = f"Context 7 server error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg,
                    "server": "context7"
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"Timeout executing Context 7 tool {tool_name}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "server": "context7"
            }
        except Exception as e:
            error_msg = f"Error executing Context 7 tool {tool_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "server": "context7"
            }
    
    def _execute_legacy_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on legacy server."""
        try:
            logger.info(f"Executing legacy tool: {tool_name}")
            result = self.legacy_client.execute_tool(tool_name, params)
            
            # Add server identifier
            if isinstance(result, dict):
                result["server"] = "legacy"
            
            logger.info(f"✅ Legacy tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Error executing legacy tool {tool_name}: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "server": "legacy"
            }
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get status of both servers."""
        status = {
            "legacy_server": {
                "available": False,
                "url": self.legacy_client.base_url,
                "tools_count": 0
            },
            "context7_server": {
                "available": self.context7_available,
                "url": self.context7_url,
                "tools_count": 0
            }
        }
        
        # Check legacy server
        try:
            legacy_tools = self.legacy_client.get_tools()
            status["legacy_server"]["available"] = True
            status["legacy_server"]["tools_count"] = len(legacy_tools)
        except Exception as e:
            logger.error(f"Legacy server check failed: {e}")
        
        # Check Context 7 server
        if self.context7_available:
            try:
                response = requests.get(f"{self.context7_url}/api/mcp/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    status["context7_server"]["tools_count"] = data.get("tool_count", 0)
            except Exception as e:
                logger.error(f"Context 7 server check failed: {e}")
                status["context7_server"]["available"] = False
        
        return status
    
    def is_context7_tool(self, tool_name: str) -> bool:
        """Check if a tool should use Context 7 server."""
        return tool_name in self.context7_tools
    
    def get_tool_routing_info(self) -> Dict[str, str]:
        """Get information about which tools use which server."""
        routing = {}
        
        # Get all tools
        all_tools = self.get_tools()
        
        for tool in all_tools:
            tool_name = tool.get("name", "unknown")
            server = tool.get("server", "unknown")
            routing[tool_name] = server
        
        return routing
