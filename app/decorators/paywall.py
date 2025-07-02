"""
AutoWave Paywall Decorators
Provides decorators for protecting features behind subscription paywalls
"""

import json
import logging
from functools import wraps
from flask import request, jsonify, session, redirect, url_for
from typing import Optional, Dict, Any, Callable
from ..services.subscription_service import SubscriptionService
from ..services.admin_service import admin_service

logger = logging.getLogger(__name__)

def require_subscription(min_plan: str = 'free'):
    """
    Decorator to require a minimum subscription level
    
    Args:
        min_plan: Minimum plan required ('free', 'plus', 'pro', 'enterprise')
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user ID from session
            user_id = session.get('user_id')
            user_email = session.get('user_email')

            # Check for admin bypass first
            if user_email and admin_service.is_admin(user_email):
                logger.info(f"Admin bypass for subscription requirement: {user_email}")
                return f(*args, **kwargs)

            if not user_id:
                return jsonify({
                    'error': 'Authentication required',
                    'redirect': '/auth/login'
                }), 401
            
            subscription_service = SubscriptionService()
            user_subscription = subscription_service.get_user_subscription(user_id)
            
            if not user_subscription:
                # Create free subscription for new users
                if min_plan == 'free':
                    subscription_service.create_free_subscription(user_id)
                    return f(*args, **kwargs)
                else:
                    return jsonify({
                        'error': 'Subscription required',
                        'required_plan': min_plan,
                        'redirect': '/pricing'
                    }), 402
            
            # Check plan hierarchy
            plan_hierarchy = {'free': 0, 'plus': 1, 'pro': 2, 'enterprise': 3}
            
            # Get user's plan name
            plan_response = subscription_service.supabase.table('subscription_plans').select('plan_name').eq('id', user_subscription.plan_id).single().execute()
            
            if not plan_response.data:
                return jsonify({'error': 'Invalid subscription plan'}), 500
            
            user_plan = plan_response.data['plan_name']
            
            if plan_hierarchy.get(user_plan, 0) < plan_hierarchy.get(min_plan, 0):
                return jsonify({
                    'error': f'{min_plan.title()} plan required',
                    'current_plan': user_plan,
                    'required_plan': min_plan,
                    'redirect': '/pricing'
                }), 402
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_credits(credits_needed: int, agent_type: str, action_type: str, skip_for_guests: bool = True):
    """
    Decorator to require sufficient credits for an action

    Args:
        credits_needed: Number of credits required
        agent_type: Type of agent consuming credits
        action_type: Type of action being performed
        skip_for_guests: Whether to skip credit checking for guest users
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            user_email = session.get('user_email')

            # Check for admin bypass first
            if user_email and admin_service.is_admin(user_email):
                logger.info(f"Admin bypass for credits: {user_email}")
                return f(*args, **kwargs)

            # Skip credit checking for guest users if allowed
            if not user_id and skip_for_guests:
                # Guest users are handled by trial_limit decorator
                return f(*args, **kwargs)

            # Use anonymous for credit service if no user_id
            credit_user_id = user_id or 'anonymous'

            # Use new credit service
            from app.services.credit_service import credit_service

            # Map agent_type to task_type for new credit service
            task_type_mapping = {
                'code_wave': 'code_wave_simple',
                'agent_wave': 'agent_wave_document',
                'prime_agent': 'prime_agent_basic',
                'autowave_chat': 'autowave_chat_basic'
            }

            task_type = task_type_mapping.get(agent_type, agent_type)

            # Check and consume credits
            credit_result = credit_service.consume_credits(credit_user_id, task_type, credits_needed)

            if not credit_result['success']:
                return jsonify({
                    'error': credit_result['error'],
                    'credits_needed': credit_result.get('credits_needed'),
                    'credits_available': credit_result.get('credits_available'),
                    'redirect': '/pricing'
                }), 402

            # Execute the function
            result = f(*args, **kwargs)

            # Add credit consumption info to response if it's a JSON response
            if hasattr(result, 'status_code') and result.status_code == 200:
                try:
                    if hasattr(result, 'get_json') and result.get_json():
                        response_data = result.get_json()
                        response_data['credits_consumed'] = credit_result['credits_consumed']
                        response_data['remaining_credits'] = credit_result['remaining_credits']
                        result.data = json.dumps(response_data)
                except Exception as e:
                    logger.error(f"Error adding credit info to response: {e}")

            return result

        return decorated_function
    return decorator

def require_feature_access(feature_name: str, consume_usage: bool = True):
    """
    Decorator to check feature access and usage limits
    
    Args:
        feature_name: Name of the feature to check
        consume_usage: Whether to consume a usage count on success
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({
                    'error': 'Authentication required',
                    'redirect': '/auth/login'
                }), 401
            
            subscription_service = SubscriptionService()
            access_info = subscription_service.check_feature_access(user_id, feature_name)
            
            if not access_info.get('has_access', False):
                return jsonify({
                    'error': f'Access denied to {feature_name}',
                    'reason': access_info.get('reason', 'Feature not available'),
                    'redirect': '/pricing'
                }), 402
            
            # Check usage limits for non-unlimited features
            if not access_info.get('unlimited', False):
                remaining = access_info.get('remaining', 0)
                if remaining <= 0:
                    return jsonify({
                        'error': f'Daily limit reached for {feature_name}',
                        'limit': access_info.get('limit', 0),
                        'used': access_info.get('used', 0),
                        'redirect': '/pricing'
                    }), 402
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Record usage after successful execution
            if consume_usage and hasattr(result, 'status_code') and result.status_code == 200:
                if not access_info.get('unlimited', False):
                    subscription_service.record_feature_usage(user_id, feature_name)
            
            return result
        
        return decorated_function
    return decorator

def trial_limit(feature_name: str, daily_limit: int, allow_guest: bool = False, guest_limit: int = 1):
    """
    Decorator for trial features with daily limits (Free plan)

    Args:
        feature_name: Name of the trial feature
        daily_limit: Maximum uses per day
        allow_guest: Whether to allow guest/anonymous access
        guest_limit: Maximum uses for guest users per session
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            user_email = session.get('user_email')

            # Check for admin bypass first
            if user_email and admin_service.is_admin(user_email):
                logger.info(f"Admin bypass for trial limit: {user_email}")
                return f(*args, **kwargs)

            # Handle guest access if allowed
            if not user_id and allow_guest:
                # Create a guest session identifier
                guest_id = session.get('guest_id')
                if not guest_id:
                    import uuid
                    guest_id = f"guest_{uuid.uuid4().hex[:8]}"
                    session['guest_id'] = guest_id
                    session['guest_usage'] = {}

                # Check guest usage
                guest_usage = session.get('guest_usage', {})
                feature_usage = guest_usage.get(feature_name, 0)

                if feature_usage >= guest_limit:
                    return jsonify({
                        'error': 'Guest trial limit reached',
                        'message': f'You have used all {guest_limit} guest trials. Please sign up for more access.',
                        'limit': guest_limit,
                        'remaining': 0,
                        'redirect': '/auth/register',
                        'guest_mode': True
                    }), 402

                # Execute function for guest
                result = f(*args, **kwargs)

                # Record guest usage if successful
                if hasattr(result, 'status_code') and result.status_code == 200:
                    guest_usage[feature_name] = feature_usage + 1
                    session['guest_usage'] = guest_usage

                return result

            # Require authentication for non-guest access
            if not user_id:
                return jsonify({
                    'error': 'Authentication required',
                    'redirect': '/auth/login'
                }), 401
            
            subscription_service = SubscriptionService()
            
            # Check if user has paid plan (bypass trial limits)
            user_subscription = subscription_service.get_user_subscription(user_id)
            if user_subscription:
                plan_response = subscription_service.supabase.table('subscription_plans').select('plan_name').eq('id', user_subscription.plan_id).single().execute()
                
                if plan_response.data and plan_response.data['plan_name'] != 'free':
                    # Paid plan - no trial limits
                    return f(*args, **kwargs)
            
            # Check trial usage for free plan
            access_info = subscription_service.check_feature_access(user_id, feature_name)
            
            if not access_info.get('has_access', False):
                remaining = access_info.get('remaining', 0)
                return jsonify({
                    'error': f'Daily trial limit reached for {feature_name}',
                    'message': f'You have used all {daily_limit} daily trials. Upgrade to continue using this feature.',
                    'limit': daily_limit,
                    'remaining': remaining,
                    'redirect': '/pricing'
                }), 402
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Record trial usage
            if hasattr(result, 'status_code') and result.status_code == 200:
                subscription_service.record_feature_usage(user_id, feature_name)
            
            return result
        
        return decorated_function
    return decorator

def get_user_plan_info(user_id: str) -> Dict[str, Any]:
    """
    Helper function to get user's current plan information
    
    Args:
        user_id: User ID
        
    Returns:
        Dict containing plan information
    """
    try:
        subscription_service = SubscriptionService()
        
        # Get subscription
        subscription = subscription_service.get_user_subscription(user_id)
        if not subscription:
            return {
                'plan_name': 'none',
                'display_name': 'No Plan',
                'has_subscription': False
            }
        
        # Get plan details
        plan_response = subscription_service.supabase.table('subscription_plans').select('*').eq('id', subscription.plan_id).single().execute()
        
        if not plan_response.data:
            return {
                'plan_name': 'unknown',
                'display_name': 'Unknown Plan',
                'has_subscription': True
            }
        
        plan = plan_response.data
        
        # Get credits
        credits = subscription_service.get_user_credits(user_id)
        
        return {
            'plan_name': plan['plan_name'],
            'display_name': plan['display_name'],
            'has_subscription': True,
            'features': plan['features'],
            'credits': {
                'total': credits.total_credits if credits else 0,
                'used': credits.used_credits if credits else 0,
                'remaining': credits.remaining_credits if credits else 0,
                'unlimited': credits.total_credits == -1 if credits else False
            },
            'subscription': {
                'status': subscription.status,
                'current_period_end': subscription.current_period_end.isoformat(),
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user plan info: {str(e)}")
        return {
            'plan_name': 'error',
            'display_name': 'Error',
            'has_subscription': False,
            'error': str(e)
        }
