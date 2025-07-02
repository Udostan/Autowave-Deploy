"""
Tool registry for the MCP server.
"""

import logging
from typing import Dict, Any

from app.mcp.server import MCPServer
from app.mcp.tools.image_tools import ImageTools
from app.mcp.tools.search_tools import SearchTools
from app.mcp.tools.booking_tools import BookingTools
from app.mcp.tools.design_tools import DesignTools
from app.mcp.tools.visual_browser_tools import VisualBrowserTools
from app.mcp.tools.task_analysis_tools import TaskAnalysisTools
from app.mcp.tools.chat_tools import ChatTools
from app.mcp.tools.document_tools import DocumentTools
# Data analysis tools - temporarily disabled for deployment stability
# from app.mcp.tools.data_analysis_wrapper import get_data_analysis_tools, is_data_analysis_available

# DataAnalysisTools = get_data_analysis_tools()
# DATA_ANALYSIS_AVAILABLE = is_data_analysis_available()
DataAnalysisTools = None
DATA_ANALYSIS_AVAILABLE = False
from app.mcp.tools.social_media_tools import SocialMediaTools
from app.mcp.tools.email_tools import EmailTools
from app.mcp.tools.seo_tools import SEOTools
from app.mcp.tools.learning_tools import LearningTools

logger = logging.getLogger(__name__)

def register_tools(mcp_server: MCPServer) -> None:
    """
    Register all tools with the MCP server.

    Args:
        mcp_server: The MCP server instance
    """
    # Initialize tool classes
    image_tools = ImageTools()
    search_tools = SearchTools()
    booking_tools = BookingTools()
    design_tools = DesignTools()
    visual_browser_tools = VisualBrowserTools()
    task_analysis_tools = TaskAnalysisTools()
    chat_tools = ChatTools()
    document_tools = DocumentTools()
    # data_analysis_tools = DataAnalysisTools() if DATA_ANALYSIS_AVAILABLE else None  # Disabled for deployment
    social_media_tools = SocialMediaTools()
    email_tools = EmailTools()
    seo_tools = SEOTools()
    learning_tools = LearningTools()

    # Register image tools
    mcp_server.register_tool(
        "image_search",
        image_tools.search_images,
        "Search for images based on a query. Returns a list of image results with URLs and metadata."
    )

    mcp_server.register_tool(
        "fetch_image",
        image_tools.fetch_image,
        "Fetch an image from a URL and return metadata. Optionally includes base64-encoded image data."
    )

    # Register search tools
    mcp_server.register_tool(
        "web_search",
        search_tools.search_web,
        "Search the web for information based on a query. Returns a list of search results with titles, links, and snippets."
    )

    mcp_server.register_tool(
        "fetch_webpage",
        search_tools.fetch_webpage,
        "Fetch and extract content from a webpage. Returns the title, description, and main content."
    )

    # Register booking tools
    mcp_server.register_tool(
        "search_flights",
        booking_tools.search_flights,
        "Search for flights and generate booking links. Requires origin, destination, departure_date, and optional return_date."
    )

    mcp_server.register_tool(
        "search_hotels",
        booking_tools.search_hotels,
        "Search for hotels and generate booking links. Requires location, check_in_date, check_out_date, and optional guests parameter."
    )

    mcp_server.register_tool(
        "estimate_ride",
        booking_tools.estimate_ride,
        "Estimate ride prices and generate booking links. Requires origin and destination locations."
    )

    # Register design tools
    mcp_server.register_tool(
        "generate_webpage",
        design_tools.generate_webpage,
        "Generate a complete webpage based on a description. Returns HTML, CSS, and JS code with a preview image."
    )

    mcp_server.register_tool(
        "generate_diagram",
        design_tools.generate_diagram,
        "Generate a diagram based on a description. Supports flowcharts, sequence diagrams, class diagrams, and more."
    )

    mcp_server.register_tool(
        "generate_pdf",
        design_tools.generate_pdf,
        "Generate a PDF document based on content. Returns PDF data and a preview image."
    )

    # Register visual browser tools
    mcp_server.register_tool(
        "visual_browser_start",
        visual_browser_tools.start_browser,
        "Start a new visual browser session. Returns a session ID for subsequent operations."
    )

    mcp_server.register_tool(
        "visual_browser_stop",
        visual_browser_tools.stop_browser,
        "Stop a visual browser session. If no session ID is provided, stops all sessions."
    )

    mcp_server.register_tool(
        "visual_browser_navigate",
        visual_browser_tools.navigate,
        "Navigate to a URL in the visual browser. Returns a screenshot of the page."
    )

    mcp_server.register_tool(
        "visual_browser_click",
        visual_browser_tools.click,
        "Click on an element or at specific coordinates in the visual browser."
    )

    mcp_server.register_tool(
        "visual_browser_type",
        visual_browser_tools.type_text,
        "Type text into an input field in the visual browser."
    )

    mcp_server.register_tool(
        "visual_browser_scroll",
        visual_browser_tools.scroll,
        "Scroll the page in the visual browser."
    )

    mcp_server.register_tool(
        "visual_browser_info",
        visual_browser_tools.get_page_info,
        "Get information about the current page in the visual browser."
    )

    mcp_server.register_tool(
        "visual_browser_screenshot",
        visual_browser_tools.take_screenshot,
        "Take a screenshot of the current page in the visual browser."
    )

    # Login to platform functionality is not implemented yet
    # mcp_server.register_tool(
    #     "visual_browser_login",
    #     visual_browser_tools.login_to_platform,
    #     "Login to a specific platform (e.g., Instagram, Twitter) in the visual browser."
    # )

    # Register task analysis tools
    mcp_server.register_tool(
        "web_task_analyze",
        task_analysis_tools.analyze_web_task,
        "Analyze a web browsing task and break it down into steps. Returns a structured task plan."
    )

    # Register chat tools
    mcp_server.register_tool(
        "chat",
        chat_tools.chat,
        "Generate a chat response using available LLM providers. Supports system prompts and chat history."
    )

    # Register document tools
    mcp_server.register_tool(
        "generate_document",
        document_tools.generate_document,
        "Generate professional documents (reports, essays, legal docs) with proper formatting and citations."
    )

    mcp_server.register_tool(
        "analyze_document",
        document_tools.analyze_document,
        "Analyze a document and provide insights on readability, structure, and potential improvements."
    )

    # Data analysis tools temporarily disabled for deployment stability
    logger.warning("Data analysis tools not available - skipping registration")

    # Register social media tools
    mcp_server.register_tool(
        "generate_social_content",
        social_media_tools.generate_content,
        "Create optimized content for different social platforms with hashtags and posting schedules."
    )

    # Register email tools
    mcp_server.register_tool(
        "create_email_campaign",
        email_tools.create_email_campaign,
        "Generate complete email campaigns with subject lines, body content, and A/B testing suggestions."
    )

    # Register SEO tools
    mcp_server.register_tool(
        "optimize_seo_content",
        seo_tools.optimize_seo_content,
        "Analyze and optimize content for search engines with keyword suggestions and readability improvements."
    )

    # Register learning tools
    mcp_server.register_tool(
        "create_learning_path",
        learning_tools.create_learning_path,
        "Create personalized learning paths for any subject with resource recommendations and progress tracking."
    )

    logger.info(f"Registered {len(mcp_server.tools)} tools with the MCP server")
