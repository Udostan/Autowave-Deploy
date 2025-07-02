"""
API endpoints for the MCP server.
"""

import logging
from flask import Blueprint, request, jsonify, current_app

from app.mcp.server import MCPServer
from app.mcp.tool_registry import register_tools

# Create blueprint
mcp_bp = Blueprint('mcp', __name__)

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp_server = MCPServer()

# Register tools with error handling for optional dependencies
try:
    register_tools(mcp_server)
    logger.info("MCP tools registered successfully")
except Exception as e:
    logger.error(f"Error registering MCP tools: {e}")
    logger.warning("Some MCP tools may not be available due to missing dependencies")

@mcp_bp.route('/api/mcp/tools', methods=['GET'])
def get_tools():
    """Get a list of available tools."""
    return jsonify({
        "tools": mcp_server.get_tool_descriptions()
    })

@mcp_bp.route('/api/mcp/execute', methods=['POST'])
def execute_tool():
    """Execute a tool with the given parameters."""
    data = request.json
    
    if not data:
        return jsonify({
            "status": "error",
            "error": "No data provided"
        }), 400
    
    tool_name = data.get('tool')
    params = data.get('params', {})
    
    if not tool_name:
        return jsonify({
            "status": "error",
            "error": "No tool specified"
        }), 400
    
    result = mcp_server.execute_tool(tool_name, params)
    return jsonify(result)

@mcp_bp.route('/api/mcp/clear-cache', methods=['POST'])
def clear_cache():
    """Clear the tool execution cache."""
    mcp_server.clear_cache()
    return jsonify({
        "status": "success",
        "message": "Cache cleared"
    })
