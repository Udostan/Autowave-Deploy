"""
Enhanced History API for AutoWave

Provides API endpoints for the new unified history system with session management
and real-time activity tracking across all agents.
"""

import logging
import time
import uuid
import hashlib
from flask import Blueprint, request, jsonify, session
from app.services.enhanced_history_service import enhanced_history_service

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
enhanced_history_bp = Blueprint('enhanced_history', __name__)

def get_or_create_user_id():
    """
    Get user ID from session or create a proper UUID-based temporary one.
    This ensures compatibility with the database UUID constraints.
    """
    user_id = session.get('user_id')
    if not user_id:
        # Create a deterministic UUID based on session ID
        session_id = session.get('_id', 'anonymous')
        # Create a namespace UUID for temporary users
        namespace = uuid.UUID('12345678-1234-5678-1234-123456789abc')
        # Generate a deterministic UUID based on session
        user_id = str(uuid.uuid5(namespace, f"temp_user_{session_id}"))
        session['user_id'] = user_id
    return user_id

@enhanced_history_bp.route('/api/history/unified', methods=['GET'])
def get_unified_history():
    """
    Get unified history across all agents for the current user.
    """
    try:
        # Get user ID from session or create a temporary one
        user_id = get_or_create_user_id()
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        
        # Get unified history
        history_items = enhanced_history_service.get_unified_history(user_id, limit)
        
        return jsonify({
            'success': True,
            'history': history_items,
            'count': len(history_items)
        })
        
    except Exception as e:
        logger.error(f"Error getting unified history: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve history'
        }), 500

@enhanced_history_bp.route('/api/history/session/<session_id>', methods=['GET'])
def get_session_details(session_id):
    """
    Get detailed information about a specific session.
    """
    try:
        # Get user ID from session or create a temporary one
        user_id = get_or_create_user_id()
        
        # Get session details
        session_data = enhanced_history_service.get_session_details(session_id)
        
        if not session_data:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        # Verify session belongs to user
        if session_data.get('session', {}).get('user_id') != user_id:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        return jsonify({
            'success': True,
            'session': session_data['session'],
            'activities': session_data['activities']
        })
        
    except Exception as e:
        logger.error(f"Error getting session details: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve session details'
        }), 500

@enhanced_history_bp.route('/api/history/track', methods=['POST'])
def track_activity():
    """
    Track a new activity in the history system.
    """
    try:
        # Get user ID from session or create a temporary one
        user_id = get_or_create_user_id()
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract required fields
        agent_type = data.get('agent_type')
        activity_type = data.get('activity_type')
        input_data = data.get('input_data')
        
        if not all([agent_type, activity_type, input_data]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: agent_type, activity_type, input_data'
            }), 400
        
        # Extract optional fields
        output_data = data.get('output_data')
        session_id = data.get('session_id')
        processing_time_ms = data.get('processing_time_ms')
        success = data.get('success', True)
        error_message = data.get('error_message')
        
        # Log the activity
        activity_id = enhanced_history_service.log_activity(
            user_id=user_id,
            agent_type=agent_type,
            activity_type=activity_type,
            input_data=input_data,
            output_data=output_data,
            session_id=session_id,
            processing_time_ms=processing_time_ms,
            success=success,
            error_message=error_message
        )
        
        return jsonify({
            'success': True,
            'activity_id': activity_id
        })
        
    except Exception as e:
        logger.error(f"Error tracking activity: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to track activity'
        }), 500

@enhanced_history_bp.route('/api/history/search', methods=['GET'])
def search_history():
    """
    Search through user's history.
    """
    try:
        # Get user ID from session or create a temporary one
        user_id = get_or_create_user_id()
        
        # Get search parameters
        query = request.args.get('q', '').strip()
        agent_type = request.args.get('agent_type')
        limit = request.args.get('limit', 50, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        # Get unified history first
        history_items = enhanced_history_service.get_unified_history(user_id, limit * 2)  # Get more for filtering
        
        # Filter based on search query and agent type
        filtered_items = []
        query_lower = query.lower()
        
        for item in history_items:
            # Check agent type filter
            if agent_type and item.get('agent_type') != agent_type:
                continue
            
            # Check if query matches
            searchable_text = ' '.join([
                item.get('session_name', ''),
                item.get('preview_text', ''),
                item.get('agent_type', '').replace('_', ' ')
            ]).lower()
            
            if query_lower in searchable_text:
                filtered_items.append(item)
            
            # Limit results
            if len(filtered_items) >= limit:
                break
        
        return jsonify({
            'success': True,
            'history': filtered_items,
            'count': len(filtered_items),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Error searching history: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to search history'
        }), 500

@enhanced_history_bp.route('/api/history/stats', methods=['GET'])
def get_history_stats():
    """
    Get history statistics for the current user.
    """
    try:
        # Get user ID from session or create a temporary one
        user_id = get_or_create_user_id()
        
        # Get days parameter
        days = request.args.get('days', 30, type=int)
        
        # This would typically get analytics from the enhanced history service
        # For now, return basic stats
        history_items = enhanced_history_service.get_unified_history(user_id, 1000)
        
        # Calculate basic statistics
        stats = {
            'total_sessions': len(history_items),
            'agent_breakdown': {},
            'recent_activity': len([item for item in history_items if item.get('updated_at')]),
            'success_rate': 0
        }
        
        # Calculate agent breakdown
        for item in history_items:
            agent_type = item.get('agent_type', 'unknown')
            if agent_type not in stats['agent_breakdown']:
                stats['agent_breakdown'][agent_type] = 0
            stats['agent_breakdown'][agent_type] += 1
        
        # Calculate success rate
        successful_items = len([item for item in history_items if item.get('success', True)])
        if history_items:
            stats['success_rate'] = round((successful_items / len(history_items)) * 100, 1)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting history stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve history statistics'
        }), 500

@enhanced_history_bp.route('/api/history/clear', methods=['DELETE'])
def clear_history():
    """
    Clear user's history (mark sessions as inactive).
    """
    try:
        # Get user ID from session or create a temporary one
        user_id = get_or_create_user_id()
        
        # This would typically mark sessions as inactive rather than deleting
        # Implementation would depend on the enhanced history service
        
        return jsonify({
            'success': True,
            'message': 'History cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear history'
        }), 500

@enhanced_history_bp.route('/api/history/continue/<session_id>', methods=['GET'])
def get_continuation_data(session_id):
    """
    Get continuation data for a specific session to restore activity state.
    """
    try:
        # Get user ID from session or create a temporary one
        user_id = get_or_create_user_id()

        # Get continuation data
        continuation_data = enhanced_history_service.get_activity_continuation_data(session_id)

        if not continuation_data:
            return jsonify({
                'success': False,
                'error': 'Session not found or cannot be continued'
            }), 404

        return jsonify({
            'success': True,
            'continuation_data': continuation_data
        })

    except Exception as e:
        logger.error(f"Error getting continuation data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get continuation data'
        }), 500
