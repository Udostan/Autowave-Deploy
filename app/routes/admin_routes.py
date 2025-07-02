"""
AutoWave Admin Routes
Special routes for admin testing and management
"""

import logging
from flask import Blueprint, request, jsonify, session, render_template
from ..services.admin_service import admin_service
from ..services.subscription_service import SubscriptionService
from ..decorators.paywall import get_user_plan_info
from ..security.auth_manager import require_auth

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/setup', methods=['POST'])
def setup_admin_access():
    """Set up admin access for designated admin emails"""
    try:
        # Check if request is from an admin email (basic security)
        data = request.get_json() or {}
        admin_email = data.get('admin_email', '')
        
        if not admin_service.is_admin(admin_email):
            return jsonify({
                'success': False,
                'error': 'Unauthorized: Not an admin email'
            }), 403
        
        # Set up admin users
        results = admin_service.setup_admin_users()
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error setting up admin access: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to set up admin access'
        }), 500

@admin_bp.route('/status', methods=['GET'])
@require_auth()
def check_admin_status():
    """Check current user's admin status"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        status = admin_service.check_user_admin_status(user_id)
        
        return jsonify({
            'success': True,
            'admin_status': status
        })
        
    except Exception as e:
        logger.error(f"Error checking admin status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to check admin status'
        }), 500

@admin_bp.route('/grant-access', methods=['POST'])
@require_auth()
def grant_admin_access():
    """Grant admin access to current user (if they're an admin email)"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get user email from session or database
        subscription_service = SubscriptionService()
        user_response = subscription_service.supabase.table('user_profiles').select('email').eq('id', user_id).single().execute()
        
        if not user_response.data:
            return jsonify({'error': 'User profile not found'}), 404
        
        email = user_response.data['email']
        
        # Grant admin access
        if admin_service.grant_admin_access(user_id, email):
            return jsonify({
                'success': True,
                'message': f'Admin access granted to {email}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to grant admin access or not an admin email'
            }), 403
        
    except Exception as e:
        logger.error(f"Error granting admin access: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to grant admin access'
        }), 500

@admin_bp.route('/test-paywall', methods=['GET'])
@require_auth()
def test_paywall():
    """Test paywall functionality for admins"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get comprehensive user info
        plan_info = get_user_plan_info(user_id)
        admin_status = admin_service.check_user_admin_status(user_id)
        
        # Get subscription plans
        subscription_service = SubscriptionService()
        plans = subscription_service.get_subscription_plans()
        
        plans_data = []
        for plan in plans:
            plans_data.append({
                'id': plan.id,
                'name': plan.plan_name,
                'display_name': plan.display_name,
                'monthly_price': plan.monthly_price_usd,
                'annual_price': plan.annual_price_usd,
                'monthly_credits': plan.monthly_credits,
                'features': plan.features,
                'is_active': plan.is_active
            })
        
        return jsonify({
            'success': True,
            'user_plan_info': plan_info,
            'admin_status': admin_status,
            'available_plans': plans_data,
            'test_results': {
                'has_subscription': plan_info.get('has_subscription', False),
                'plan_name': plan_info.get('plan_name', 'none'),
                'credits': plan_info.get('credits', {}),
                'is_admin': admin_status.get('is_admin', False),
                'has_unlimited_access': admin_status.get('has_unlimited_credits', False)
            }
        })
        
    except Exception as e:
        logger.error(f"Error testing paywall: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to test paywall'
        }), 500

@admin_bp.route('/dashboard', methods=['GET'])
@require_auth()
def admin_dashboard():
    """Admin dashboard for testing and monitoring"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return render_template('error.html', error='Authentication required')
        
        # Check if user is admin
        admin_status = admin_service.check_user_admin_status(user_id)
        
        if not admin_status.get('is_admin', False):
            return render_template('error.html', error='Admin access required')
        
        return render_template('admin_dashboard.html', admin_status=admin_status)
        
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        return render_template('error.html', error='Failed to load admin dashboard')

@admin_bp.route('/simulate-usage', methods=['POST'])
@require_auth()
def simulate_usage():
    """Simulate agent usage for testing credit consumption"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        agent_type = data.get('agent_type', 'test_agent')
        action_type = data.get('action_type', 'test_action')
        credits_to_consume = data.get('credits', 1)
        
        # Check if user is admin
        admin_status = admin_service.check_user_admin_status(user_id)
        
        if not admin_status.get('is_admin', False):
            return jsonify({'error': 'Admin access required'}), 403
        
        # Simulate credit consumption
        subscription_service = SubscriptionService()
        
        if admin_status.get('has_unlimited_credits', False):
            # For admins with unlimited credits, just log the usage
            usage_data = {
                'user_id': user_id,
                'agent_type': agent_type,
                'action_type': action_type,
                'credits_consumed': credits_to_consume,
                'description': f'Admin test: {action_type} via {agent_type}'
            }
            
            subscription_service.supabase.table('credit_usage').insert(usage_data).execute()
            
            return jsonify({
                'success': True,
                'message': f'Simulated usage: {credits_to_consume} credits for {agent_type}',
                'unlimited_credits': True
            })
        else:
            # For non-unlimited users, actually consume credits
            success = subscription_service.consume_credits(
                user_id, credits_to_consume, agent_type, action_type, 
                f'Test usage: {action_type} via {agent_type}'
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Consumed {credits_to_consume} credits for {agent_type}',
                    'unlimited_credits': False
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to consume credits (insufficient balance?)'
                }), 400
        
    except Exception as e:
        logger.error(f"Error simulating usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to simulate usage'
        }), 500

@admin_bp.route('/reset-credits', methods=['POST'])
@require_auth()
def reset_credits():
    """Reset user credits for testing"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Check if user is admin
        admin_status = admin_service.check_user_admin_status(user_id)
        
        if not admin_status.get('is_admin', False):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        new_credits = data.get('credits', 100)
        
        # Reset credits
        subscription_service = SubscriptionService()
        
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        period_end = now + timedelta(days=30)
        
        credits_data = {
            'total_credits': new_credits,
            'used_credits': 0,
            'billing_period_start': now.isoformat(),
            'billing_period_end': period_end.isoformat(),
            'updated_at': now.isoformat()
        }
        
        subscription_service.supabase.table('user_credits').update(credits_data).eq('user_id', user_id).execute()
        
        return jsonify({
            'success': True,
            'message': f'Credits reset to {new_credits}',
            'new_credits': new_credits
        })
        
    except Exception as e:
        logger.error(f"Error resetting credits: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to reset credits'
        }), 500
