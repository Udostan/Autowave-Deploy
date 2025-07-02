"""
Security Management API
Endpoints for managing security settings, monitoring, and administration.
"""

from flask import Blueprint, request, jsonify
from .auth_manager import require_admin, require_auth, auth_manager
from .firewall import security_firewall
from .rate_limiter import rate_limiter
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Create security blueprint
security_bp = Blueprint('security', __name__, url_prefix='/api/security')

@security_bp.route('/status', methods=['GET'])
@require_auth(['read'])
def security_status():
    """Get overall security system status."""
    try:
        return jsonify({
            'success': True,
            'status': 'active',
            'components': {
                'authentication': 'active',
                'firewall': 'active',
                'rate_limiter': 'active',
                'threat_detection': 'active'
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/blocked-ips', methods=['GET'])
@require_admin()
def get_blocked_ips():
    """Get list of blocked IP addresses."""
    try:
        blocked_ips = list(security_firewall.blocked_ips)
        return jsonify({
            'success': True,
            'blocked_ips': blocked_ips,
            'count': len(blocked_ips),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/block-ip', methods=['POST'])
@require_admin()
def block_ip():
    """Block an IP address."""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        reason = data.get('reason', 'Manual block by admin')
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'IP address required'}), 400
        
        security_firewall.block_ip(ip_address, reason)
        
        return jsonify({
            'success': True,
            'message': f'IP {ip_address} has been blocked',
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error blocking IP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/unblock-ip', methods=['POST'])
@require_admin()
def unblock_ip():
    """Unblock an IP address."""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'IP address required'}), 400
        
        security_firewall.unblock_ip(ip_address)
        
        return jsonify({
            'success': True,
            'message': f'IP {ip_address} has been unblocked',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/threat-scores', methods=['GET'])
@require_admin()
def get_threat_scores():
    """Get threat scores for all IPs."""
    try:
        threat_scores = dict(security_firewall.threat_scores)
        
        # Sort by threat score (highest first)
        sorted_scores = sorted(threat_scores.items(), key=lambda x: x[1], reverse=True)
        
        return jsonify({
            'success': True,
            'threat_scores': sorted_scores[:50],  # Top 50 threats
            'total_ips': len(threat_scores),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting threat scores: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/rate-limit-info', methods=['GET'])
@require_auth(['read'])
def get_rate_limit_info():
    """Get rate limit information for current client."""
    try:
        info = rate_limiter.get_rate_limit_info(request)
        return jsonify({
            'success': True,
            'rate_limit_info': info,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting rate limit info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/failed-attempts', methods=['GET'])
@require_admin()
def get_failed_attempts():
    """Get failed authentication attempts."""
    try:
        failed_attempts = dict(auth_manager.failed_attempts)
        
        # Convert to more readable format
        formatted_attempts = []
        for ip, data in failed_attempts.items():
            formatted_attempts.append({
                'ip_address': ip,
                'failed_count': data['count'],
                'last_attempt': datetime.fromtimestamp(data['last_attempt']).isoformat(),
                'is_locked': auth_manager.is_ip_locked(ip)
            })
        
        # Sort by failed count (highest first)
        formatted_attempts.sort(key=lambda x: x['failed_count'], reverse=True)
        
        return jsonify({
            'success': True,
            'failed_attempts': formatted_attempts,
            'total_ips': len(formatted_attempts),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting failed attempts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/reset-failed-attempts', methods=['POST'])
@require_admin()
def reset_failed_attempts():
    """Reset failed attempts for an IP address."""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        
        if not ip_address:
            return jsonify({'success': False, 'error': 'IP address required'}), 400
        
        auth_manager.reset_failed_attempts(ip_address)
        
        return jsonify({
            'success': True,
            'message': f'Failed attempts reset for IP {ip_address}',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error resetting failed attempts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/generate-api-key', methods=['POST'])
@require_admin()
def generate_api_key():
    """Generate a new API key."""
    try:
        data = request.get_json()
        key_name = data.get('name', f'api_key_{int(time.time())}')
        permissions = data.get('permissions', ['read', 'write'])
        
        # Generate new API key
        import secrets
        new_key = f'autowave_{secrets.token_urlsafe(32)}'
        
        # Add to auth manager
        auth_manager.api_keys[new_key] = {
            'name': key_name,
            'permissions': permissions,
            'created': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'api_key': new_key,
            'name': key_name,
            'permissions': permissions,
            'message': 'New API key generated successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error generating API key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/revoke-api-key', methods=['POST'])
@require_admin()
def revoke_api_key():
    """Revoke an API key."""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API key required'}), 400
        
        if api_key in auth_manager.api_keys:
            del auth_manager.api_keys[api_key]
            return jsonify({
                'success': True,
                'message': 'API key revoked successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'success': False, 'error': 'API key not found'}), 404
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/api-keys', methods=['GET'])
@require_admin()
def list_api_keys():
    """List all API keys (without revealing the actual keys)."""
    try:
        api_keys_info = []
        for key, data in auth_manager.api_keys.items():
            api_keys_info.append({
                'key_preview': key[:12] + '...' + key[-4:],  # Show partial key
                'name': data['name'],
                'permissions': data['permissions'],
                'created': data['created']
            })
        
        return jsonify({
            'success': True,
            'api_keys': api_keys_info,
            'count': len(api_keys_info),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/security-stats', methods=['GET'])
@require_auth(['read'])
def get_security_stats():
    """Get comprehensive security statistics."""
    try:
        stats = {
            'blocked_ips_count': len(security_firewall.blocked_ips),
            'threat_scores_count': len(security_firewall.threat_scores),
            'failed_attempts_count': len(auth_manager.failed_attempts),
            'api_keys_count': len(auth_manager.api_keys),
            'high_threat_ips': len([ip for ip, score in security_firewall.threat_scores.items() if score > 50]),
            'locked_ips': len([ip for ip in auth_manager.failed_attempts.keys() if auth_manager.is_ip_locked(ip)]),
            'system_status': 'secure',
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'security_stats': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting security stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@security_bp.route('/test-security', methods=['POST'])
@require_auth(['read'])
def test_security():
    """Test security system functionality."""
    try:
        # Test authentication
        auth_test = hasattr(request, 'auth_data') and request.auth_data is not None
        
        # Test firewall
        firewall_test, _ = security_firewall.process_request(request)
        
        # Test rate limiter
        rate_limit_test, _ = rate_limiter.check_rate_limit(request)
        
        return jsonify({
            'success': True,
            'security_tests': {
                'authentication': auth_test,
                'firewall': firewall_test,
                'rate_limiter': rate_limit_test,
                'overall_status': auth_test and firewall_test and rate_limit_test
            },
            'message': 'Security system is functioning correctly' if all([auth_test, firewall_test, rate_limit_test]) else 'Some security components may have issues',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error testing security: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
