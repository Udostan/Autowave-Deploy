"""
AutoWave Coupon Routes
Handles coupon validation, application, and management
"""

import logging
from flask import Blueprint, request, jsonify, session
from ..services.coupon_service import coupon_service
from ..security.auth_manager import require_auth

logger = logging.getLogger(__name__)

coupon_bp = Blueprint('coupon', __name__, url_prefix='/api/coupon')

@coupon_bp.route('/validate', methods=['POST'])
def validate_coupon():
    """Validate a coupon code without applying it"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        plan_name = data.get('plan_name', '')
        amount = float(data.get('amount', 0))
        
        if not code:
            return jsonify({
                'valid': False,
                'error': 'Coupon code is required'
            }), 400
        
        if not plan_name or amount <= 0:
            return jsonify({
                'valid': False,
                'error': 'Valid plan and amount are required'
            }), 400
        
        # Validate coupon
        result = coupon_service.validate_coupon(code, plan_name, amount)
        
        return jsonify(result)
        
    except ValueError:
        return jsonify({
            'valid': False,
            'error': 'Invalid amount format'
        }), 400
    except Exception as e:
        logger.error(f"Error validating coupon: {str(e)}")
        return jsonify({
            'valid': False,
            'error': 'Failed to validate coupon'
        }), 500

@coupon_bp.route('/apply', methods=['POST'])
@require_auth()
def apply_coupon():
    """Apply a coupon code to a subscription"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        code = data.get('code', '').strip()
        plan_name = data.get('plan_name', '')
        amount = float(data.get('amount', 0))
        
        if not code:
            return jsonify({
                'success': False,
                'error': 'Coupon code is required'
            }), 400
        
        if not plan_name or amount <= 0:
            return jsonify({
                'success': False,
                'error': 'Valid plan and amount are required'
            }), 400
        
        # Apply coupon
        result = coupon_service.apply_coupon(code, plan_name, amount, user_id)
        
        if result.get('valid') and result.get('applied'):
            return jsonify({
                'success': True,
                'message': f"Coupon {code} applied successfully!",
                'coupon': result.get('coupon'),
                'discount_amount': result.get('discount_amount'),
                'final_amount': result.get('final_amount'),
                'savings_percentage': result.get('savings_percentage'),
                'bonus_credits': result.get('bonus_credits', 0)
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to apply coupon')
            }), 400
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid amount format'
        }), 400
    except Exception as e:
        logger.error(f"Error applying coupon: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to apply coupon'
        }), 500

@coupon_bp.route('/list', methods=['GET'])
def list_active_coupons():
    """List all active promotional coupons (public info only)"""
    try:
        active_coupons = []
        
        for code, coupon in coupon_service.coupons.items():
            if coupon.status.value == 'active' and coupon.current_uses < coupon.max_uses:
                # Only return public information
                active_coupons.append({
                    'code': coupon.code,
                    'type': coupon.type.value,
                    'value': coupon.value,
                    'description': coupon.description,
                    'applicable_plans': coupon.applicable_plans,
                    'minimum_amount': coupon.minimum_amount,
                    'valid_until': coupon.valid_until.isoformat(),
                    'usage_remaining': coupon.max_uses - coupon.current_uses
                })
        
        return jsonify({
            'success': True,
            'coupons': active_coupons,
            'total_active': len(active_coupons)
        })
        
    except Exception as e:
        logger.error(f"Error listing coupons: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to list coupons'
        }), 500

@coupon_bp.route('/check/<code>', methods=['GET'])
def check_coupon_info(code):
    """Get basic information about a coupon code"""
    try:
        code = code.upper().strip()
        
        if code not in coupon_service.coupons:
            return jsonify({
                'exists': False,
                'message': 'Coupon code not found'
            }), 404
        
        coupon = coupon_service.coupons[code]
        
        # Return basic info without validating usage
        return jsonify({
            'exists': True,
            'code': coupon.code,
            'type': coupon.type.value,
            'value': coupon.value,
            'description': coupon.description,
            'applicable_plans': coupon.applicable_plans,
            'minimum_amount': coupon.minimum_amount,
            'valid_until': coupon.valid_until.isoformat(),
            'status': coupon.status.value,
            'usage_remaining': max(0, coupon.max_uses - coupon.current_uses)
        })
        
    except Exception as e:
        logger.error(f"Error checking coupon {code}: {str(e)}")
        return jsonify({
            'exists': False,
            'error': 'Failed to check coupon'
        }), 500

@coupon_bp.route('/stats', methods=['GET'])
@require_auth()
def get_coupon_stats():
    """Get coupon usage statistics (admin only)"""
    try:
        user_id = session.get('user_id')
        
        # In production, add admin role check here
        # For now, return basic stats
        
        total_coupons = len(coupon_service.coupons)
        active_coupons = sum(1 for c in coupon_service.coupons.values() if c.status.value == 'active')
        total_uses = sum(c.current_uses for c in coupon_service.coupons.values())
        
        return jsonify({
            'success': True,
            'stats': {
                'total_coupons': total_coupons,
                'active_coupons': active_coupons,
                'total_uses': total_uses,
                'usage_history_count': len(coupon_service.usage_history)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting coupon stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get coupon statistics'
        }), 500
