"""
Health check routes for AutoWave platform.
"""

from flask import Blueprint, jsonify, request
import os
import time
import requests
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'service': 'AutoWave Platform'
    })

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with system status."""
    try:
        # Check MCP server
        mcp_status = False
        try:
            response = requests.get('http://localhost:5011/api/mcp/status', timeout=5)
            mcp_status = response.status_code == 200
        except:
            pass
        
        # Check database
        db_status = True  # Assume healthy for now
        
        # Check environment
        env_status = bool(os.getenv('GEMINI_API_KEY'))
        
        overall_status = all([mcp_status, db_status, env_status])
        
        return jsonify({
            'status': 'healthy' if overall_status else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'mcp_server': 'healthy' if mcp_status else 'unhealthy',
                'database': 'healthy' if db_status else 'unhealthy',
                'environment': 'healthy' if env_status else 'unhealthy'
            },
            'version': '1.0.0'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@health_bp.route('/api/user/credits', methods=['GET'])
def get_user_credits():
    """Get user credits endpoint for health check."""
    # This is a placeholder - in production this would check authentication
    return jsonify({
        'credits': 100,
        'plan': 'free',
        'status': 'active'
    })

@health_bp.route('/status', methods=['GET'])
def system_status():
    """System status endpoint."""
    return jsonify({
        'platform': 'AutoWave',
        'status': 'operational',
        'uptime': time.time(),
        'timestamp': datetime.now().isoformat()
    })
