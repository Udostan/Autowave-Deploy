"""
Run the MCP server.
"""

import os
import sys
import logging
import json
from flask import Flask, request, jsonify
from app.mcp.server import MCPServer
from app.mcp.tool_registry import register_tools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the MCP server
mcp_server = MCPServer()
register_tools(mcp_server)

# Create the Flask app
app = Flask(__name__)

@app.route('/api/mcp/execute', methods=['POST'])
def execute_tool():
    """Execute a tool with the given parameters."""
    try:
        data = request.json
        tool_name = data.get('tool_name')
        params = data.get('params', {})
        
        if not tool_name:
            return jsonify({
                "status": "error",
                "error": "Tool name is required"
            }), 400
        
        logger.info(f"Executing tool: {tool_name} with params: {params}")
        result = mcp_server.execute_tool(tool_name, params)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error executing tool: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/mcp/tools', methods=['GET'])
def get_tools():
    """Get a list of available tools."""
    try:
        tools = mcp_server.get_tool_descriptions()
        return jsonify({
            "status": "success",
            "tools": tools
        })
    except Exception as e:
        logger.error(f"Error getting tools: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/mcp/clear-cache', methods=['POST'])
def clear_cache():
    """Clear the tool execution cache."""
    try:
        mcp_server.clear_cache()
        return jsonify({
            "status": "success",
            "message": "Cache cleared"
        })
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/mcp/status', methods=['GET'])
def get_status():
    """Get the status of the MCP server."""
    try:
        return jsonify({
            "status": "success",
            "message": "MCP server is running",
            "tool_count": len(mcp_server.tools)
        })
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Get the port from the environment or use the default
    port = int(os.environ.get('MCP_PORT', 5011))
    
    # Run the app
    logger.info(f"Starting MCP server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
