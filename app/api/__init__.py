"""
API package for the application.
"""

from flask import Blueprint, jsonify, session

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Import and register blueprints
from app.api.chat import chat_bp
from app.api.document_generator import document_generator_bp

api_bp.register_blueprint(chat_bp)
api_bp.register_blueprint(document_generator_bp)

# Add user-info endpoint
@api_bp.route('/user-info', methods=['GET'])
def get_user_info():
    """Get user's current subscription and credit information for Universal Credit System"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            # Return default free plan info for non-authenticated users
            return jsonify({
                'success': True,
                'user_info': {
                    'plan_name': 'free',
                    'display_name': 'Free Plan',
                    'credits': {
                        'remaining': 50,
                        'total': 50,
                        'type': 'daily'
                    },
                    'authenticated': False,
                    'is_admin': False
                }
            })

        # Check if user is admin first
        from app.services.admin_service import admin_service
        user_email = session.get('user_email', '')
        is_admin_user = admin_service.is_admin(user_email)

        if is_admin_user:
            # Admin user with unlimited credits
            return jsonify({
                'success': True,
                'user_info': {
                    'plan_name': 'admin',
                    'display_name': 'Admin Plan',
                    'credits': {
                        'remaining': -1,  # Unlimited
                        'total': -1,      # Unlimited
                        'type': 'unlimited',
                        'percentage': 100,
                        'reset_date': None
                    },
                    'authenticated': True,
                    'subscription_status': 'active',
                    'is_admin': True
                }
            })
        else:
            # Regular user - use credit service
            from app.services.credit_service import credit_service
            credit_info = credit_service.get_user_credits(user_id)

            return jsonify({
                'success': True,
                'user_info': {
                    'plan_name': credit_info.get('plan', 'free'),
                    'display_name': credit_info.get('plan', 'free').title() + ' Plan',
                    'credits': {
                        'remaining': credit_info.get('remaining', 50),
                        'total': credit_info.get('total', 50),
                        'type': credit_info.get('type', 'daily'),
                        'percentage': credit_info.get('percentage', 100),
                        'reset_date': credit_info.get('reset_date')
                    },
                    'authenticated': True,
                    'subscription_status': 'active',
                    'is_admin': False
                }
            })

    except Exception as e:
        import logging
        logging.error(f"Error fetching user info: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch user information'
        }), 500

# Conditionally import and register data analysis blueprint
import os
if os.getenv('DISABLE_DATA_ANALYSIS', 'false').lower() != 'true':
    try:
        from app.api.data_analysis import data_analysis_bp
        api_bp.register_blueprint(data_analysis_bp)
    except ImportError:
        pass  # Data analysis dependencies not available
