"""
Enterprise Authentication Manager
Multi-layer authentication with JWT, API keys, and session management.
"""

import jwt
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
import os
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """Enterprise-grade authentication and authorization manager."""
    
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        self.api_keys = self._load_api_keys()
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1 hour
        self.max_login_attempts = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
        self.lockout_duration = int(os.getenv('LOCKOUT_DURATION', 900))  # 15 minutes
        self.failed_attempts = {}
        
    def _load_api_keys(self):
        """Load authorized API keys from environment."""
        api_keys = {}
        
        # Load from environment variables
        for i in range(1, 11):  # Support up to 10 API keys
            key_name = f'AUTOWAVE_API_KEY_{i}'
            key_value = os.getenv(key_name)
            if key_value:
                api_keys[key_value] = {
                    'name': f'api_key_{i}',
                    'permissions': ['read', 'write'],
                    'created': datetime.now().isoformat()
                }
        
        # Default admin key if none provided
        if not api_keys:
            default_key = os.getenv('AUTOWAVE_ADMIN_KEY', 'autowave_' + secrets.token_urlsafe(32))
            api_keys[default_key] = {
                'name': 'admin',
                'permissions': ['read', 'write', 'admin'],
                'created': datetime.now().isoformat()
            }
            logger.warning(f"Using default admin key: {default_key}")
        
        return api_keys
    
    def generate_jwt_token(self, user_id, permissions=None):
        """Generate JWT token for authenticated user."""
        if permissions is None:
            permissions = ['read', 'write']
            
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=self.session_timeout)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def verify_jwt_token(self, token):
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_api_key(self, api_key):
        """Verify API key and return permissions."""
        if api_key in self.api_keys:
            return self.api_keys[api_key]
        return None
    
    def is_ip_locked(self, ip_address):
        """Check if IP address is locked due to failed attempts."""
        if ip_address in self.failed_attempts:
            attempts_data = self.failed_attempts[ip_address]
            if attempts_data['count'] >= self.max_login_attempts:
                if time.time() - attempts_data['last_attempt'] < self.lockout_duration:
                    return True
                else:
                    # Reset after lockout period
                    del self.failed_attempts[ip_address]
        return False
    
    def record_failed_attempt(self, ip_address):
        """Record failed authentication attempt."""
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = {'count': 0, 'last_attempt': 0}
        
        self.failed_attempts[ip_address]['count'] += 1
        self.failed_attempts[ip_address]['last_attempt'] = time.time()
    
    def reset_failed_attempts(self, ip_address):
        """Reset failed attempts for IP address."""
        if ip_address in self.failed_attempts:
            del self.failed_attempts[ip_address]

# Authentication decorators
def require_auth(permissions=None):
    """Decorator to require authentication for endpoints."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_manager = AuthManager()
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            # Check if IP is locked
            if auth_manager.is_ip_locked(client_ip):
                return jsonify({
                    'error': 'IP address temporarily locked due to failed attempts',
                    'retry_after': auth_manager.lockout_duration
                }), 429
            
            # Check for API key in headers
            api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
            
            if api_key:
                key_data = auth_manager.verify_api_key(api_key)
                if key_data:
                    # Check permissions
                    if permissions:
                        if not any(perm in key_data['permissions'] for perm in permissions):
                            return jsonify({'error': 'Insufficient permissions'}), 403
                    
                    auth_manager.reset_failed_attempts(client_ip)
                    request.auth_data = key_data
                    return f(*args, **kwargs)
            
            # Check for JWT token
            jwt_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if jwt_token:
                payload = auth_manager.verify_jwt_token(jwt_token)
                if payload:
                    # Check permissions
                    if permissions:
                        if not any(perm in payload.get('permissions', []) for perm in permissions):
                            return jsonify({'error': 'Insufficient permissions'}), 403

                    auth_manager.reset_failed_attempts(client_ip)
                    request.auth_data = payload
                    return f(*args, **kwargs)

            # Check for session-based authentication (for web interface)
            from flask import session
            user_id = session.get('user_id')
            user_email = session.get('user_email')

            if user_id and user_email:
                # User is authenticated via session
                auth_manager.reset_failed_attempts(client_ip)
                request.auth_data = {
                    'user_id': user_id,
                    'email': user_email,
                    'name': session.get('user_name', ''),
                    'auth_type': 'session'
                }
                return f(*args, **kwargs)

            # Authentication failed
            auth_manager.record_failed_attempt(client_ip)
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this feature'
            }), 401
        
        return decorated_function
    return decorator

def require_admin():
    """Decorator to require admin permissions."""
    return require_auth(['admin'])

# Global auth manager instance
auth_manager = AuthManager()
