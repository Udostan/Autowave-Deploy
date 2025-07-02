"""
Feedback API for collecting user feedback.

This module provides endpoints for collecting and storing user feedback.
"""

import os
import json
import logging
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
feedback_api = Blueprint('feedback_api', __name__)

# Feedback storage directory
FEEDBACK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'feedback')

# Ensure feedback directory exists
os.makedirs(FEEDBACK_DIR, exist_ok=True)

@feedback_api.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit user feedback.
    
    Accepts feedback data and stores it in a JSON file.
    """
    try:
        data = request.json or {}
        
        # Validate required fields
        required_fields = ['feature', 'rating', 'text']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                })
        
        # Add timestamp if not provided
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        # Add user agent
        data['user_agent'] = request.headers.get('User-Agent', 'Unknown')
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"feedback_{timestamp}_{data['feature']}.json"
        filepath = os.path.join(FEEDBACK_DIR, filename)
        
        # Save feedback to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Feedback saved to {filepath}")
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully'
        })
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@feedback_api.route('/api/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """
    Get feedback statistics.
    
    Returns statistics about collected feedback.
    """
    try:
        # Get all feedback files
        feedback_files = [f for f in os.listdir(FEEDBACK_DIR) if f.endswith('.json')]
        
        # Initialize stats
        stats = {
            'total_count': len(feedback_files),
            'feature_counts': {},
            'rating_avg': {},
            'recent_feedback': []
        }
        
        # Process each feedback file
        for filename in feedback_files:
            filepath = os.path.join(FEEDBACK_DIR, filename)
            
            with open(filepath, 'r') as f:
                feedback = json.load(f)
            
            # Update feature counts
            feature = feedback.get('feature', 'unknown')
            stats['feature_counts'][feature] = stats['feature_counts'].get(feature, 0) + 1
            
            # Update rating averages
            if 'rating' in feedback:
                if feature not in stats['rating_avg']:
                    stats['rating_avg'][feature] = {'sum': 0, 'count': 0}
                
                stats['rating_avg'][feature]['sum'] += feedback['rating']
                stats['rating_avg'][feature]['count'] += 1
            
            # Add to recent feedback (limit to 10)
            if len(stats['recent_feedback']) < 10:
                stats['recent_feedback'].append({
                    'feature': feature,
                    'rating': feedback.get('rating'),
                    'text': feedback.get('text'),
                    'timestamp': feedback.get('timestamp')
                })
        
        # Calculate average ratings
        for feature, data in stats['rating_avg'].items():
            if data['count'] > 0:
                stats['rating_avg'][feature] = round(data['sum'] / data['count'], 1)
            else:
                stats['rating_avg'][feature] = 0
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting feedback stats: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })
