"""
Authentication Routes
Clean, classic authentication endpoints with AutoWave theme.
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from .supabase_auth import supabase_auth
import logging

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Display login page with AutoWave theme."""
    # Check if user is already logged in with valid session
    if session.get('user_id') and session.get('access_token'):
        # Verify token is still valid
        if supabase_auth.verify_token(session['access_token']):
            return redirect(url_for('index'))
        else:
            # Clear invalid session
            session.clear()

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    """Display registration page with AutoWave theme."""
    # Check if user is already logged in with valid session
    if session.get('user_id') and session.get('access_token'):
        # Verify token is still valid
        if supabase_auth.verify_token(session['access_token']):
            return redirect(url_for('index'))
        else:
            # Clear invalid session
            session.clear()

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login."""
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400

        # Attempt to sign in
        result = supabase_auth.sign_in_with_email(email, password)

        if result['success']:
            # Store user session
            user_data = result['user']
            session_data = result['session']

            session['user_id'] = user_data['id']
            session['user_email'] = user_data['email']
            session['access_token'] = session_data['access_token']
            session['refresh_token'] = session_data['refresh_token']
            session['email_confirmed'] = user_data['email_confirmed']

            # Log successful login
            logger.info(f"User logged in: {email}")

            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': {
                        'id': user_data['id'],
                        'email': user_data['email'],
                        'email_confirmed': user_data['email_confirmed']
                    },
                    'redirect_url': url_for('index')
                })
            else:
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
        else:
            if request.is_json:
                return jsonify(result), 401
            else:
                flash(result.get('error', 'Login failed'), 'error')
                return redirect(url_for('auth.login_page'))

    except Exception as e:
        logger.error(f"Login error: {e}")
        error_msg = 'An error occurred during login'

        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('auth.login_page'))

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle user registration."""
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        full_name = data.get('full_name', '').strip()

        # Validation
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400

        if password != confirm_password:
            return jsonify({
                'success': False,
                'error': 'Passwords do not match'
            }), 400

        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Password must be at least 6 characters long'
            }), 400

        # Prepare user metadata
        user_data = {
            'full_name': full_name,
            'display_name': full_name or email.split('@')[0],
            'registration_source': 'autowave_web'
        }

        # Attempt to register
        result = supabase_auth.sign_up_with_email(email, password, user_data)

        if result['success']:
            # Log successful registration
            logger.info(f"User registered: {email}")

            # Set up session for the new user
            user_data = result['user']
            session['user_id'] = user_data['id']
            session['user_email'] = email
            session['user_name'] = full_name
            session['email_confirmed'] = user_data.get('email_confirmed', False)
            session.permanent = True

            # Create free subscription for new user
            try:
                from ..services.subscription_service import SubscriptionService
                subscription_service = SubscriptionService()
                subscription_created = subscription_service.create_free_subscription(user_data['id'])
                if subscription_created:
                    logger.info(f"Free subscription created for user: {email}")
                else:
                    logger.warning(f"Failed to create free subscription for user: {email}")
            except Exception as e:
                logger.error(f"Error creating free subscription for {email}: {str(e)}")

            logger.info(f"User session created for: {email}")

            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': result.get('message', 'Registration successful'),
                    'user': result['user'],
                    'email_confirmation_required': not result['user']['email_confirmed'],
                    'auto_login': True
                })
            else:
                flash(result.get('message', 'Registration successful! Please check your email.'), 'success')
                return redirect(url_for('index'))  # Redirect to dashboard instead of login
        else:
            if request.is_json:
                return jsonify(result), 400
            else:
                flash(result.get('error', 'Registration failed'), 'error')
                return redirect(url_for('auth.register_page'))

    except Exception as e:
        logger.error(f"Registration error: {e}")
        error_msg = 'An error occurred during registration'

        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('auth.register_page'))

@auth_bp.route('/google', methods=['GET'])
def google_auth():
    """Initiate Google OAuth authentication."""
    try:
        redirect_url = request.args.get('redirect_url') or url_for('auth.callback', _external=True)
        result = supabase_auth.sign_in_with_google(redirect_url)

        if result['success']:
            return redirect(result['auth_url'])
        else:
            flash(result.get('error', 'Google authentication failed'), 'error')
            return redirect(url_for('auth.login_page'))

    except Exception as e:
        logger.error(f"Google auth error: {e}")
        flash('Google authentication is not available', 'error')
        return redirect(url_for('auth.login_page'))

@auth_bp.route('/callback', methods=['GET'])
def callback():
    """Handle OAuth and email verification callback."""
    try:
        # DEBUG: Log all parameters received
        logger.info(f"Callback received - URL: {request.url}")
        logger.info(f"Query params: {dict(request.args)}")
        logger.info(f"Form data: {dict(request.form)}")

        # Check for email verification
        if request.args.get('type') == 'signup':
            # This is an email verification callback
            access_token = request.args.get('access_token')
            refresh_token = request.args.get('refresh_token')

            if access_token:
                # Get user information
                result = supabase_auth.get_user(access_token)

                if result['success']:
                    user_data = result['user']

                    # Store user session
                    session['user_id'] = user_data['id']
                    session['user_email'] = user_data['email']
                    session['access_token'] = access_token
                    session['refresh_token'] = refresh_token
                    session['email_confirmed'] = user_data['email_confirmed']

                    logger.info(f"Email verified and user logged in: {user_data['email']}")
                    flash('Email verified successfully! Welcome to AutoWave!', 'success')
                    return redirect(url_for('index'))

        # Handle OAuth callback - check for different parameter formats
        access_token = request.args.get('access_token') or request.args.get('token')
        refresh_token = request.args.get('refresh_token')
        code = request.args.get('code')

        # Also check for error parameters
        error = request.args.get('error')
        error_description = request.args.get('error_description')

        if error:
            logger.error(f"OAuth error: {error} - {error_description}")
            flash(f'Authentication failed: {error_description or error}', 'error')
            return redirect(url_for('auth.login_page'))

        # If we have an authorization code, exchange it for tokens
        if code and not access_token:
            logger.info(f"Authorization code received: {code[:20]}...")
            try:
                # Exchange code for session using Supabase
                result = supabase_auth.exchange_code_for_session(code)
                logger.info(f"Code exchange result: {result}")

                if result['success']:
                    access_token = result['access_token']
                    refresh_token = result['refresh_token']
                    user_data = result['user']

                    # Store user session
                    session['user_id'] = user_data['id']
                    session['user_email'] = user_data['email']
                    session['access_token'] = access_token
                    session['refresh_token'] = refresh_token
                    session['email_confirmed'] = user_data.get('email_confirmed', True)

                    logger.info(f"OAuth user logged in via code exchange: {user_data['email']}")
                    flash('Login successful!', 'success')
                    return redirect(url_for('index'))
                else:
                    logger.error(f"Failed to exchange code: {result}")
                    flash('Authentication failed during token exchange', 'error')
                    return redirect(url_for('auth.login_page'))
            except Exception as e:
                logger.error(f"Error exchanging code: {e}")
                flash('Authentication failed', 'error')
                return redirect(url_for('auth.login_page'))

        # Handle direct access token (fallback)
        if access_token:
            logger.info(f"Access token received: {access_token[:20]}...")
            # Get user information
            result = supabase_auth.get_user(access_token)
            logger.info(f"Get user result: {result}")

            if result['success']:
                user_data = result['user']

                # Store user session
                session['user_id'] = user_data['id']
                session['user_email'] = user_data['email']
                session['access_token'] = access_token
                session['refresh_token'] = refresh_token
                session['email_confirmed'] = user_data['email_confirmed']

                logger.info(f"OAuth user logged in: {user_data['email']}")
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                logger.error(f"Failed to get user data: {result}")
                flash('Failed to get user information', 'error')
                return redirect(url_for('auth.login_page'))
        else:
            logger.warning("No access token or code found in callback")
            flash('Authentication failed - no credentials received', 'error')
            return redirect(url_for('auth.login_page'))

    except Exception as e:
        logger.error(f"Callback error: {e}")
        flash('Authentication failed', 'error')
        return redirect(url_for('auth.login_page'))

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Handle user logout."""
    try:
        access_token = session.get('access_token')

        if access_token:
            # Sign out from Supabase
            supabase_auth.sign_out(access_token)

        # Clear session
        session.clear()

        logger.info("User logged out")

        if request.is_json:
            return jsonify({'success': True, 'message': 'Logged out successfully'})
        else:
            flash('Logged out successfully', 'success')
            return redirect(url_for('auth.login_page'))

    except Exception as e:
        logger.error(f"Logout error: {e}")
        session.clear()  # Clear session anyway

        if request.is_json:
            return jsonify({'success': True, 'message': 'Logged out'})
        else:
            return redirect(url_for('auth.login_page'))

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Handle password reset request."""
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400

        result = supabase_auth.reset_password(email)

        if request.is_json:
            return jsonify(result)
        else:
            if result['success']:
                flash(result['message'], 'success')
            else:
                flash(result.get('error', 'Password reset failed'), 'error')
            return redirect(url_for('auth.login_page'))

    except Exception as e:
        logger.error(f"Password reset error: {e}")
        error_msg = 'An error occurred during password reset'

        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('auth.login_page'))

@auth_bp.route('/profile', methods=['GET'])
def profile():
    """Display user profile page."""
    if not session.get('user_id'):
        return redirect(url_for('auth.login_page'))

    return render_template('auth/profile.html', user={
        'id': session.get('user_id'),
        'email': session.get('user_email'),
        'email_confirmed': session.get('email_confirmed', False)
    })

@auth_bp.route('/profile/update', methods=['POST'])
def update_profile():
    """Update user profile information."""
    try:
        if not session.get('user_id'):
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Get the display name from the request
        display_name = data.get('name', '').strip()

        # For now, we'll just store the display name in the session
        # In a full implementation, you'd update this in your user database
        session['user_display_name'] = display_name

        logger.info(f"Profile updated for user: {session.get('user_email')}")

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'id': session.get('user_id'),
                'email': session.get('user_email'),
                'name': display_name,
                'email_confirmed': session.get('email_confirmed', False)
            }
        })

    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return jsonify({'success': False, 'error': 'Failed to update profile'}), 500

@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """Get authentication status."""
    try:
        # For now, just check if user_id and email are in session
        # We'll improve token verification later
        if session.get('user_id') and session.get('user_email'):
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': session['user_id'],
                    'email': session['user_email'],
                    'name': session.get('user_display_name', ''),
                    'email_confirmed': session.get('email_confirmed', False)
                }
            })

        return jsonify({'authenticated': False})

    except Exception as e:
        logger.error(f"Auth status error: {e}")
        return jsonify({'authenticated': False})

@auth_bp.route('/test-login', methods=['GET'])
def test_login():
    """Temporary test login to bypass OAuth issues."""
    # Set a test session
    session['user_id'] = 'test-user-123'
    session['user_email'] = 'test@example.com'
    session['access_token'] = 'test-token'
    session['email_confirmed'] = True

    logger.info("Test login successful")
    flash('Test login successful!', 'success')
    return redirect(url_for('index'))
