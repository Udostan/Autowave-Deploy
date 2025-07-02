"""
LLM-Powered Tools API Endpoints

This module provides dedicated API endpoints for the LLM-powered tools:
- Email Campaign Manager
- SEO Content Optimizer
- Learning Path Generator
"""

import logging
import time
from flask import Blueprint, request, jsonify, session
from typing import Dict, Any

# Import the tools using relative imports
from ..mcp.tools.email_tools import EmailTools
from ..mcp.tools.seo_tools import SEOTools
from ..mcp.tools.learning_tools import LearningTools
from ..services.activity_logger import activity_logger

logger = logging.getLogger(__name__)

# Create Blueprint
llm_tools_bp = Blueprint('llm_tools', __name__, url_prefix='/api/llm-tools')

# Initialize tool instances
email_tools = EmailTools()
seo_tools = SEOTools()
learning_tools = LearningTools()

@llm_tools_bp.route('/email-campaign', methods=['POST'])
def create_email_campaign():
    """Create an email campaign using LLM-powered content generation."""
    start_time = time.time()
    try:
        data = request.get_json()

        # Extract parameters
        topic = data.get('topic', '')
        audience = data.get('audience', 'general audience')
        campaign_type = data.get('campaign_type', 'promotional')
        tone = data.get('tone', 'professional')

        # Validate required parameters
        if not topic:
            return jsonify({
                'error': 'Topic is required',
                'status': 'error'
            }), 400

        # Check and consume credits before processing
        from flask import session
        from ..services.credit_service import credit_service

        user_id = session.get('user_id', 'anonymous')

        # Consume credits for email campaign generation
        credit_result = credit_service.consume_credits(user_id, 'agent_wave_email')

        if not credit_result['success']:
            return jsonify({
                'error': credit_result['error'],
                'status': 'error',
                'credits_needed': credit_result.get('credits_needed'),
                'credits_available': credit_result.get('credits_available')
            }), 402

        # Generate email campaign
        result = email_tools.create_email_campaign(
            campaign_topic=topic,
            target_audience=audience,
            campaign_type=campaign_type,
            tone=tone
        )

        if 'error' in result:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 500

        # Log activity if user_id is available
        if user_id and user_id != 'anonymous':
            try:
                processing_time_ms = int((time.time() - start_time) * 1000)
                activity_logger.log_activity(
                    user_id=user_id,
                    agent_type='agent_wave',
                    activity_type='email_campaign',
                    input_data={
                        'topic': topic,
                        'audience': audience,
                        'campaign_type': campaign_type,
                        'tone': tone
                    },
                    output_data={
                        'success': True,
                        'campaign_generated': True,
                        'subject_lines_count': len(result.get('subject_lines', [])),
                        'has_content': bool(result.get('email_content'))
                    },
                    processing_time_ms=processing_time_ms,
                    success=True
                )
            except Exception as e:
                logger.error(f"Failed to log email campaign activity: {e}")

        return jsonify({
            'data': result,
            'status': 'success',
            'message': 'Email campaign generated successfully',
            'credits_consumed': credit_result['credits_consumed'],
            'remaining_credits': credit_result['remaining_credits']
        })

    except Exception as e:
        logger.error(f"Error in email campaign generation: {str(e)}")
        return jsonify({
            'error': f'Failed to generate email campaign: {str(e)}',
            'status': 'error'
        }), 500

@llm_tools_bp.route('/seo-optimize', methods=['POST'])
def optimize_content_for_seo():
    """Optimize content for SEO using LLM-powered analysis and optimization."""
    start_time = time.time()
    try:
        data = request.get_json()

        # Extract parameters
        content = data.get('content', '')
        target_keywords = data.get('target_keywords', [])
        content_type = data.get('content_type', 'article')

        # Validate required parameters
        if not content:
            return jsonify({
                'error': 'Content is required',
                'status': 'error'
            }), 400

        # Check and consume credits before processing
        from flask import session
        from ..services.credit_service import credit_service

        user_id = session.get('user_id', 'anonymous')

        # Consume credits for SEO optimization
        credit_result = credit_service.consume_credits(user_id, 'agent_wave_seo')

        if not credit_result['success']:
            return jsonify({
                'error': credit_result['error'],
                'status': 'error',
                'credits_needed': credit_result.get('credits_needed'),
                'credits_available': credit_result.get('credits_available')
            }), 402

        # Optimize content for SEO
        result = seo_tools.optimize_seo_content(
            content=content,
            target_keywords=target_keywords,
            content_type=content_type
        )

        if 'error' in result:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 500

        # Log activity if user_id is available
        if user_id and user_id != 'anonymous':
            try:
                processing_time_ms = int((time.time() - start_time) * 1000)
                activity_logger.log_activity(
                    user_id=user_id,
                    agent_type='agent_wave',
                    activity_type='seo_optimization',
                    input_data={
                        'content_length': len(content),
                        'target_keywords': target_keywords,
                        'content_type': content_type
                    },
                    output_data={
                        'success': True,
                        'optimized': True,
                        'has_recommendations': bool(result.get('recommendations'))
                    },
                    processing_time_ms=processing_time_ms,
                    success=True
                )
            except Exception as e:
                logger.error(f"Failed to log SEO optimization activity: {e}")

        return jsonify({
            'data': result,
            'status': 'success',
            'message': 'Content optimized for SEO successfully',
            'credits_consumed': credit_result['credits_consumed'],
            'remaining_credits': credit_result['remaining_credits']
        })

    except Exception as e:
        logger.error(f"Error in SEO optimization: {str(e)}")
        return jsonify({
            'error': f'Failed to optimize content for SEO: {str(e)}',
            'status': 'error'
        }), 500

@llm_tools_bp.route('/learning-path', methods=['POST'])
def create_learning_path():
    """Create a personalized learning path using LLM-powered curriculum generation."""
    start_time = time.time()
    try:
        data = request.get_json()

        # Extract parameters
        subject = data.get('subject', '')
        skill_level = data.get('skill_level', 'beginner')
        learning_style = data.get('learning_style', 'mixed')
        time_commitment = data.get('time_commitment', 'moderate')
        goals = data.get('goals', [])

        # Validate required parameters
        if not subject:
            return jsonify({
                'error': 'Subject is required',
                'status': 'error'
            }), 400

        # Check and consume credits before processing
        from flask import session
        from ..services.credit_service import credit_service

        user_id = session.get('user_id', 'anonymous')

        # Consume credits for learning path generation
        credit_result = credit_service.consume_credits(user_id, 'agent_wave_learning')

        if not credit_result['success']:
            return jsonify({
                'error': credit_result['error'],
                'status': 'error',
                'credits_needed': credit_result.get('credits_needed'),
                'credits_available': credit_result.get('credits_available')
            }), 402

        # Create learning path
        result = learning_tools.create_learning_path(
            subject=subject,
            skill_level=skill_level,
            learning_style=learning_style,
            time_commitment=time_commitment,
            goals=goals
        )

        if 'error' in result:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 500

        # Log activity if user_id is available
        if user_id and user_id != 'anonymous':
            try:
                processing_time_ms = int((time.time() - start_time) * 1000)
                activity_logger.log_activity(
                    user_id=user_id,
                    agent_type='agent_wave',
                    activity_type='learning_path',
                    input_data={
                        'subject': subject,
                        'skill_level': skill_level,
                        'learning_style': learning_style,
                        'time_commitment': time_commitment,
                        'goals_count': len(goals)
                    },
                    output_data={
                        'success': True,
                        'path_created': True,
                        'modules_count': result.get('curriculum', {}).get('total_modules', 0),
                        'has_resources': bool(result.get('resources'))
                    },
                    processing_time_ms=processing_time_ms,
                    success=True
                )
            except Exception as e:
                logger.error(f"Failed to log learning path activity: {e}")

        return jsonify({
            'data': result,
            'status': 'success',
            'message': 'Learning path created successfully',
            'credits_consumed': credit_result['credits_consumed'],
            'remaining_credits': credit_result['remaining_credits']
        })

    except Exception as e:
        logger.error(f"Error in learning path creation: {str(e)}")
        return jsonify({
            'error': f'Failed to create learning path: {str(e)}',
            'status': 'error'
        }), 500

@llm_tools_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for LLM tools."""
    try:
        # Check if LLM APIs are available
        email_status = "available" if email_tools.llm_available else "template_mode"
        seo_status = "available" if seo_tools.llm_available else "template_mode"
        learning_status = "available" if learning_tools.llm_available else "template_mode"

        return jsonify({
            'status': 'healthy',
            'tools': {
                'email_campaign_manager': {
                    'status': email_status,
                    'llm_enabled': email_tools.llm_available
                },
                'seo_content_optimizer': {
                    'status': seo_status,
                    'llm_enabled': seo_tools.llm_available
                },
                'learning_path_generator': {
                    'status': learning_status,
                    'llm_enabled': learning_tools.llm_available
                }
            },
            'message': 'LLM tools are operational'
        })

    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@llm_tools_bp.route('/capabilities', methods=['GET'])
def get_capabilities():
    """Get capabilities and parameters for each LLM tool."""
    return jsonify({
        'tools': {
            'email_campaign_manager': {
                'endpoint': '/api/llm-tools/email-campaign',
                'method': 'POST',
                'parameters': {
                    'topic': {'type': 'string', 'required': True, 'description': 'Email campaign topic'},
                    'audience': {'type': 'string', 'required': False, 'default': 'general audience'},
                    'campaign_type': {'type': 'string', 'required': False, 'default': 'promotional', 'options': ['promotional', 'newsletter', 'welcome', 'announcement']},
                    'tone': {'type': 'string', 'required': False, 'default': 'professional', 'options': ['professional', 'casual', 'friendly', 'urgent', 'enthusiastic']}
                },
                'description': 'Generate comprehensive email campaigns with subject lines, content, and performance metrics'
            },
            'seo_content_optimizer': {
                'endpoint': '/api/llm-tools/seo-optimize',
                'method': 'POST',
                'parameters': {
                    'content': {'type': 'string', 'required': True, 'description': 'Content to optimize for SEO'},
                    'target_keywords': {'type': 'array', 'required': False, 'description': 'Target keywords for optimization'},
                    'content_type': {'type': 'string', 'required': False, 'default': 'article', 'options': ['article', 'blog_post', 'product_description', 'landing_page']}
                },
                'description': 'Optimize content for search engines with keyword integration and SEO recommendations'
            },
            'learning_path_generator': {
                'endpoint': '/api/llm-tools/learning-path',
                'method': 'POST',
                'parameters': {
                    'subject': {'type': 'string', 'required': True, 'description': 'Subject to create learning path for'},
                    'skill_level': {'type': 'string', 'required': False, 'default': 'beginner', 'options': ['beginner', 'intermediate', 'advanced']},
                    'learning_style': {'type': 'string', 'required': False, 'default': 'mixed', 'options': ['visual', 'auditory', 'kinesthetic', 'mixed']},
                    'time_commitment': {'type': 'string', 'required': False, 'default': 'moderate', 'options': ['light', 'moderate', 'intensive']},
                    'goals': {'type': 'array', 'required': False, 'description': 'Specific learning goals'}
                },
                'description': 'Create personalized learning paths with curriculum, resources, and progress tracking'
            }
        },
        'status': 'available'
    })
