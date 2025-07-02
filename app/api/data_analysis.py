"""
API endpoints for data analysis.
"""

import logging
import json
import io
import csv
import base64
import time
from flask import Blueprint, request, jsonify, current_app, session
from app.utils.mcp_client import MCPClient
from app.services.activity_logger import activity_logger

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
data_analysis_bp = Blueprint('data_analysis', __name__)

# Initialize MCP client
mcp_client = MCPClient()

@data_analysis_bp.route('/api/data-analysis/analyze', methods=['POST'])
def analyze_data():
    """
    Analyze data and generate visualizations.

    Returns:
        Response: JSON response with the analysis results.
    """
    start_time = time.time()
    try:
        data = request.get_json()

        # Get user_id from session for activity logging
        user_id = session.get('user_id')
        
        # Extract parameters
        dataset = data.get('data', '')
        analysis_type = data.get('analysis_type', 'summary')
        chart_type = data.get('chart_type', 'bar')
        title = data.get('title', 'Data Analysis')
        x_column = data.get('x_column')
        y_column = data.get('y_column')
        group_by = data.get('group_by')
        filters = data.get('filters', {})
        
        if not dataset:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            })
        
        # Call the MCP server to analyze the data
        result = mcp_client.execute_tool("analyze_data", {
            "data": dataset,
            "analysis_type": analysis_type,
            "chart_type": chart_type,
            "title": title,
            "x_column": x_column,
            "y_column": y_column,
            "group_by": group_by,
            "filters": filters
        })
        
        if result.get("status") == "success":
            analysis_result = result.get("result", {})
            
            # Format the analysis HTML
            analysis_html = format_analysis_html(analysis_result)

            # Log activity if user_id is available
            if user_id:
                try:
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    activity_logger.log_activity(
                        user_id=user_id,
                        agent_type='data_analysis',
                        activity_type='data_analysis',
                        input_data={
                            'analysis_type': analysis_type,
                            'chart_type': chart_type,
                            'title': title,
                            'data_size': len(str(dataset))
                        },
                        output_data={
                            'success': True,
                            'has_visualizations': bool(analysis_result.get('visualizations')),
                            'summary_length': len(analysis_result.get('summary', ''))
                        },
                        processing_time_ms=processing_time_ms,
                        success=True
                    )
                except Exception as e:
                    logger.error(f"Failed to log data analysis activity: {e}")

            return jsonify({
                'success': True,
                'analysis_html': analysis_html,
                'visualizations': analysis_result.get('visualizations', {}),
                'summary': analysis_result.get('summary', '')
            })
        else:
            logger.error(f"Error analyzing data: {result.get('error', 'Unknown error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            })
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@data_analysis_bp.route('/api/data-analysis/sample-data', methods=['GET'])
def get_sample_data():
    """
    Get sample data for testing.
    
    Returns:
        Response: JSON response with sample data.
    """
    try:
        data_type = request.args.get('type', 'sales')
        
        if data_type == 'sales':
            # Sample sales data
            data = {
                'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                         '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10'],
                'product': ['Product A', 'Product B', 'Product A', 'Product C', 'Product B',
                            'Product A', 'Product C', 'Product B', 'Product A', 'Product C'],
                'category': ['Electronics', 'Clothing', 'Electronics', 'Home', 'Clothing',
                             'Electronics', 'Home', 'Clothing', 'Electronics', 'Home'],
                'sales': [1200, 950, 1100, 800, 1050, 1300, 750, 900, 1150, 850],
                'units': [5, 10, 4, 8, 12, 6, 7, 9, 5, 8]
            }
        elif data_type == 'weather':
            # Sample weather data
            data = {
                'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                         '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10'],
                'city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
                         'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
                'temperature': [32, 68, 28, 55, 72, 30, 70, 25, 58, 75],
                'humidity': [65, 50, 70, 60, 40, 68, 48, 72, 62, 38],
                'precipitation': [0.5, 0.0, 0.8, 0.2, 0.0, 0.3, 0.0, 1.0, 0.1, 0.0]
            }
        elif data_type == 'finance':
            # Sample financial data
            data = {
                'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                         '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10'],
                'stock': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META',
                          'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META'],
                'price': [180.5, 135.2, 340.8, 145.6, 290.3, 182.1, 136.5, 338.2, 147.8, 292.5],
                'volume': [12500, 8900, 10200, 15600, 7800, 11800, 9200, 9800, 16200, 8100],
                'change': [1.2, -0.8, 2.5, 0.5, -1.3, 1.6, 1.3, -2.6, 2.2, 2.2]
            }
        else:
            return jsonify({
                'success': False,
                'error': f"Unknown data type: {data_type}"
            })
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting sample data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def format_analysis_html(analysis_result):
    """
    Format the analysis results as HTML.
    
    Args:
        analysis_result: The analysis results
        
    Returns:
        HTML string
    """
    title = analysis_result.get('title', 'Data Analysis')
    summary = analysis_result.get('summary', '')
    visualizations = analysis_result.get('visualizations', {})
    
    # Create HTML with proper structure
    html = f"""
    <div class="analysis-container">
        <div class="analysis-header">
            <h2 class="analysis-title">{title}</h2>
        </div>
        
        <div class="visualization-section">
            <div class="chart-container">
                <img src="data:image/png;base64,{visualizations.get('image', '')}" alt="Data Visualization" class="chart-image">
            </div>
        </div>
        
        <div class="analysis-summary">
            <div class="markdown-content">
                {summary}
            </div>
        </div>
    </div>
    """
    
    return html
