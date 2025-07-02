"""
Data Analysis Tools Wrapper
Handles conditional loading of data analysis tools based on environment variables.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Check if data analysis should be disabled
DISABLE_DATA_ANALYSIS = os.getenv('DISABLE_DATA_ANALYSIS', 'false').lower() == 'true'

def get_data_analysis_tools():
    """
    Conditionally import and return DataAnalysisTools class.
    Returns None if disabled or import fails.
    """
    if DISABLE_DATA_ANALYSIS:
        logger.info("📊 Data analysis tools disabled via DISABLE_DATA_ANALYSIS environment variable")
        return None
    
    try:
        from app.mcp.tools.data_analysis_tools import DataAnalysisTools
        logger.info("📊 Data analysis tools loaded successfully")
        return DataAnalysisTools
    except ImportError as e:
        logger.warning(f"⚠️  Data analysis tools not available: {e}")
        return None

def is_data_analysis_available():
    """Check if data analysis tools are available."""
    return not DISABLE_DATA_ANALYSIS and get_data_analysis_tools() is not None
