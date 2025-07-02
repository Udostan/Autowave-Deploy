#!/usr/bin/env python3
"""
Context 7 MCP Server for Prime Agent Advanced Tools.
This server handles the 10 new internet browsing and booking tools.
"""

import logging
import os
import sys
from typing import Dict, Any, List
from flask import Flask, request, jsonify

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import Context7Tools directly
from tools.context7_tools import Context7Tools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Context7MCPServer:
    """
    Context 7 MCP Server for advanced Prime Agent tools.
    """

    def __init__(self, port: int = 5012):
        self.port = port
        self.tools = {}
        self.tool_descriptions = {}
        self.context7_tools = Context7Tools()
        self.logger = logging.getLogger(__name__)

        # Register all Context 7 tools
        self._register_tools()

    def _register_tools(self):
        """Register all Context 7 tools."""
        tools_to_register = [
            ("restaurant_booker", self.context7_tools.book_restaurant,
             "Find and book restaurant reservations in real-time using OpenTable, Resy, and other platforms."),

            ("real_estate_scout", self.context7_tools.scout_real_estate,
             "Search global real estate platforms including Zillow, Realtor.com (US), Rightmove, Zoopla (UK), Idealista (Spain), SeLoger (France), Immobiliare.it (Italy), Daft.ie (Ireland), Property24 (South Africa), PropertyPro, NigeriaPropertyCentre, HutBay (Nigeria), and more for properties worldwide."),

            ("event_ticket_finder", self.context7_tools.find_event_tickets,
             "Find tickets for concerts, sports, theater with price comparison across multiple platforms."),

            ("job_application_assistant", self.context7_tools.assist_job_application,
             "Search job boards, auto-fill applications, and track applications across LinkedIn, Indeed, Glassdoor."),

            ("price_comparison_hunter", self.context7_tools.hunt_price_deals,
             "Compare prices across Amazon, eBay, retailers and find the best deals with price tracking."),

            ("medical_appointment_scheduler", self.context7_tools.schedule_medical_appointment,
             "Find available doctors, check insurance coverage, and book medical appointments."),

            ("government_services_navigator", self.context7_tools.navigate_government_services,
             "Navigate DMV, IRS, passport services, fill forms, and check application status."),

            ("social_media_manager", self.context7_tools.manage_social_media,
             "Post content, check analytics, and manage multiple social media accounts."),

            ("package_tracker", self.context7_tools.track_packages,
             "Track packages across UPS, FedEx, USPS, Amazon with unified interface and notifications."),

            ("financial_account_monitor", self.context7_tools.monitor_financial_accounts,
             "Check bank balances, credit scores, investment portfolios with secure authentication.")
        ]

        for tool_name, tool_func, description in tools_to_register:
            self.tools[tool_name] = tool_func
            self.tool_descriptions[tool_name] = description
            self.logger.info(f"Registered Context 7 tool: {tool_name}")

    def get_tool_descriptions(self) -> List[Dict[str, str]]:
        """Get descriptions of all available tools."""
        return [
            {"name": name, "description": desc}
            for name, desc in self.tool_descriptions.items()
        ]

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with the given parameters."""
        if tool_name not in self.tools:
            return {
                "status": "error",
                "error": f"Tool '{tool_name}' not found"
            }

        try:
            self.logger.info(f"Executing Context 7 tool: {tool_name} with params: {params}")
            result = self.tools[tool_name](**params)

            return {
                "status": "success",
                "result": result,
                "server": "context7"
            }
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "server": "context7"
            }

# Create the Context 7 MCP server instance
context7_server = Context7MCPServer()

# Create Flask app for HTTP API
app = Flask(__name__)

@app.route('/api/mcp/tools', methods=['GET'])
def get_tools():
    """Get a list of available Context 7 tools."""
    return jsonify({
        "tools": context7_server.get_tool_descriptions(),
        "server": "context7",
        "port": context7_server.port
    })

@app.route('/api/mcp/execute', methods=['POST'])
def execute_tool():
    """Execute a Context 7 tool."""
    try:
        data = request.get_json()
        tool_name = data.get('tool_name')
        params = data.get('params', {})

        if not tool_name:
            return jsonify({
                "status": "error",
                "error": "Missing tool_name parameter"
            }), 400

        result = context7_server.execute_tool(tool_name, params)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in execute_tool endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/mcp/status', methods=['GET'])
def get_status():
    """Get the status of the Context 7 MCP server."""
    return jsonify({
        "status": "success",
        "message": "Context 7 MCP server is running",
        "tool_count": len(context7_server.tools),
        "server": "context7",
        "port": context7_server.port
    })

def run_server():
    """Run the Context 7 MCP server."""
    logger.info(f"Starting Context 7 MCP server on port {context7_server.port}")
    app.run(host='0.0.0.0', port=context7_server.port, debug=False, threaded=True)

if __name__ == '__main__':
    run_server()
