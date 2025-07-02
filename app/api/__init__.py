"""
API package for the application.
"""

from flask import Blueprint

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Import and register blueprints
from app.api.chat import chat_bp
from app.api.document_generator import document_generator_bp

api_bp.register_blueprint(chat_bp)
api_bp.register_blueprint(document_generator_bp)

# Conditionally import and register data analysis blueprint
import os
if os.getenv('DISABLE_DATA_ANALYSIS', 'false').lower() != 'true':
    try:
        from app.api.data_analysis import data_analysis_bp
        api_bp.register_blueprint(data_analysis_bp)
    except ImportError:
        pass  # Data analysis dependencies not available
