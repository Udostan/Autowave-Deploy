"""
Supabase Authentication Integration
Professional user management with email/Gmail authentication.
"""

import os
import logging
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta

# Optional Supabase import
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None
    Client = None

logger = logging.getLogger(__name__)

class SupabaseAuth:
    """Supabase authentication manager for AutoWave."""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        self.client = None
        self.admin_client = None

        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase package not available. Authentication disabled.")
            return

        if self.supabase_url and self.supabase_key:
            try:
                # Public client for user operations
                self.client = create_client(self.supabase_url, self.supabase_key)

                # Admin client for administrative operations
                if self.supabase_service_key:
                    self.admin_client = create_client(self.supabase_url, self.supabase_service_key)

                logger.info("Supabase authentication initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
        else:
            logger.warning("Supabase credentials not found. Authentication disabled.")

    def is_available(self) -> bool:
        """Check if Supabase authentication is available."""
        return self.client is not None

    def sign_up_with_email(self, email: str, password: str, user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Sign up a new user with email and password."""
        if not self.client:
            return {'success': False, 'error': 'Authentication service not available'}

        try:
            # Prepare user metadata
            metadata = user_data or {}
            metadata.update({
                'created_at': datetime.now().isoformat(),
                'platform': 'autowave',
                'auth_method': 'email'
            })

            # Sign up user
            response = self.client.auth.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'data': metadata
                }
            })

            if response.user:
                return {
                    'success': True,
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'email_confirmed': response.user.email_confirmed_at is not None,
                        'created_at': response.user.created_at,
                        'metadata': response.user.user_metadata
                    },
                    'session': {
                        'access_token': response.session.access_token if response.session else None,
                        'refresh_token': response.session.refresh_token if response.session else None
                    },
                    'message': 'Account created successfully. Please check your email for verification.'
                }
            else:
                return {'success': False, 'error': 'Failed to create account'}

        except Exception as e:
            logger.error(f"Sign up error: {e}")
            error_message = str(e)

            # Handle specific Supabase errors
            if "captcha verification process failed" in error_message.lower():
                return {
                    'success': False,
                    'error': 'Captcha verification failed. Please disable captcha in Supabase dashboard: Authentication → Settings → Security → Disable "Enable Captcha protection"',
                    'error_type': 'captcha_required'
                }
            elif "email rate limit exceeded" in error_message.lower():
                return {
                    'success': False,
                    'error': 'Too many signup attempts. Please wait a few minutes before trying again.',
                    'error_type': 'rate_limit'
                }
            elif "user already registered" in error_message.lower():
                return {
                    'success': False,
                    'error': 'An account with this email already exists. Please try logging in instead.',
                    'error_type': 'user_exists'
                }
            else:
                return {'success': False, 'error': error_message}

    def sign_in_with_email(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user with email and password."""
        if not self.client:
            return {'success': False, 'error': 'Authentication service not available'}

        try:
            response = self.client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })

            if response.user and response.session:
                return {
                    'success': True,
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'email_confirmed': response.user.email_confirmed_at is not None,
                        'last_sign_in': response.user.last_sign_in_at,
                        'metadata': response.user.user_metadata
                    },
                    'session': {
                        'access_token': response.session.access_token,
                        'refresh_token': response.session.refresh_token,
                        'expires_at': response.session.expires_at
                    },
                    'message': 'Signed in successfully'
                }
            else:
                return {'success': False, 'error': 'Invalid email or password'}

        except Exception as e:
            logger.error(f"Sign in error: {e}")
            return {'success': False, 'error': 'Invalid email or password'}

    def sign_in_with_google(self, redirect_url: str = None) -> Dict[str, Any]:
        """Initiate Google OAuth sign in."""
        if not self.client:
            return {'success': False, 'error': 'Authentication service not available'}

        try:
            redirect_to = redirect_url or f"{os.getenv('APP_URL', 'http://localhost:5001')}/auth/callback"

            response = self.client.auth.sign_in_with_oauth({
                'provider': 'google',
                'options': {
                    'redirect_to': redirect_to
                }
            })

            return {
                'success': True,
                'auth_url': response.url,
                'message': 'Redirect to Google for authentication'
            }

        except Exception as e:
            logger.error(f"Google OAuth error: {e}")
            return {'success': False, 'error': str(e)}

    def exchange_code_for_session(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token and user session."""
        if not self.client:
            return {'success': False, 'error': 'Authentication service not available'}

        try:
            # Exchange the authorization code for a session
            response = self.client.auth.exchange_code_for_session({
                'auth_code': code
            })

            if response.user and response.session:
                return {
                    'success': True,
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token,
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'email_confirmed': response.user.email_confirmed_at is not None,
                        'created_at': response.user.created_at,
                        'user_metadata': response.user.user_metadata or {}
                    }
                }
            else:
                return {'success': False, 'error': 'Failed to exchange code for session'}

        except Exception as e:
            logger.error(f"Code exchange error: {e}")
            return {'success': False, 'error': str(e)}

    def sign_out(self, access_token: str = None) -> Dict[str, Any]:
        """Sign out user."""
        if not self.client:
            return {'success': False, 'error': 'Authentication service not available'}

        try:
            if access_token:
                # Set the session for the client
                self.client.auth.set_session(access_token, '')

            response = self.client.auth.sign_out()
            return {'success': True, 'message': 'Signed out successfully'}

        except Exception as e:
            logger.error(f"Sign out error: {e}")
            return {'success': False, 'error': str(e)}

    def get_user(self, access_token: str) -> Dict[str, Any]:
        """Get user information from access token."""
        if not self.client:
            return {'success': False, 'error': 'Authentication service not available'}

        try:
            # Set the session
            self.client.auth.set_session(access_token, '')

            # Get user
            response = self.client.auth.get_user()

            if response and hasattr(response, 'user') and response.user:
                return {
                    'success': True,
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'email_confirmed': response.user.email_confirmed_at is not None,
                        'last_sign_in': response.user.last_sign_in_at,
                        'metadata': response.user.user_metadata,
                        'app_metadata': response.user.app_metadata
                    }
                }
            else:
                logger.error(f"Get user error: response={response}, has user attr={hasattr(response, 'user') if response else False}")
                return {'success': False, 'error': 'User not found'}

        except Exception as e:
            logger.error(f"Get user error: {e}")
            return {'success': False, 'error': 'Invalid or expired token'}

    def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh user session."""
        if not self.client:
            return {'success': False, 'error': 'Authentication service not available'}

        try:
            response = self.client.auth.refresh_session(refresh_token)

            if response.session:
                return {
                    'success': True,
                    'session': {
                        'access_token': response.session.access_token,
                        'refresh_token': response.session.refresh_token,
                        'expires_at': response.session.expires_at
                    },
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'metadata': response.user.user_metadata
                    } if response.user else None
                }
            else:
                return {'success': False, 'error': 'Failed to refresh session'}

        except Exception as e:
            logger.error(f"Refresh session error: {e}")
            return {'success': False, 'error': 'Invalid refresh token'}

    def reset_password(self, email: str) -> Dict[str, Any]:
        """Send password reset email."""
        if not self.client:
            return {'success': False, 'error': 'Authentication service not available'}

        try:
            response = self.client.auth.reset_password_email(email)
            return {
                'success': True,
                'message': 'Password reset email sent. Please check your inbox.'
            }

        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return {'success': False, 'error': 'Failed to send password reset email'}

    def update_user(self, access_token: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information."""
        if not self.client:
            return {'success': False, 'error': 'Authentication service not available'}

        try:
            # Set the session
            self.client.auth.set_session(access_token, '')

            # Update user
            response = self.client.auth.update_user(updates)

            if response.user:
                return {
                    'success': True,
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'metadata': response.user.user_metadata
                    },
                    'message': 'User updated successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to update user'}

        except Exception as e:
            logger.error(f"Update user error: {e}")
            return {'success': False, 'error': str(e)}

    def verify_token(self, access_token: str) -> bool:
        """Verify if access token is valid."""
        try:
            result = self.get_user(access_token)
            return result.get('success', False)
        except:
            return False

# Global Supabase auth instance
supabase_auth = SupabaseAuth()
