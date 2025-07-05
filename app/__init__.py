from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import os
import time
import logging
from datetime import datetime

# Import agent classes
from app.agents.search_agent import SearchAgent
from app.agents.chat_agent import ChatAgent
from app.agents.super_agent import SuperAgent

# Import API endpoints
from app.api import super_agent as super_agent_api
from app.api.mcp import mcp_bp
from app.api.code_executor import code_executor_bp
# from app.api.visual_browser import visual_browser_api
# from app.api.visual_browser_simple import visual_browser_simple_api
from app.api.live_browser import live_browser_api
from app.api.prime_agent import prime_agent_api
from app.api.browser_proxy import browser_proxy_api
from app.api.feedback import feedback_api
from app.api.call_assistant import call_assistant_bp
from app.api.document_generator import document_generator_bp
from app.api.code_ide import code_ide_bp
from app.api.llm_tools import llm_tools_bp
# Code Wave chat removed
from app.api.context7_tools import context7_tools_bp
from app.api.memory_test import memory_test_bp
from app.api.enhanced_history import enhanced_history_bp
from app.security.security_api import security_bp
from app.auth.auth_routes import auth_bp
from app.api import api_bp
from app.routes.screen_recorder_routes import screen_recorder_bp
from app.routes.screen_recorder_ws import screen_recorder_ws_bp
# from app.visual_browser.websocket_server import start_websocket_server_thread
# from app.visual_browser.startup import start_visual_browser_services
from app.visual_browser.live_browser import live_browser

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Simple in-memory storage for search and chat history
# In a production app, this would be stored in a database
search_history = []
chat_history = []

def create_app():
    app = Flask(__name__)

    # Production optimizations
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'autowave_default_secret_key_change_in_production')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache for static files
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

    # Database connection pooling and optimization
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }

    # Enable CORS for all routes with production settings
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Add custom Jinja2 filters
    @app.template_filter('format_datetime')
    def format_datetime(value):
        """Format datetime string for display."""
        if not value:
            return ''
        try:
            # Handle ISO format datetime strings
            if isinstance(value, str):
                # Remove timezone info and microseconds for cleaner display
                clean_value = value.split('.')[0].replace('T', ' at ')
                return clean_value
            return str(value)
        except Exception:
            return str(value)

    # Check if Gemini API key is set
    if not os.environ.get('GEMINI_API_KEY'):
        app.logger.warning("GEMINI_API_KEY environment variable is not set. Some features may not work.")

    # Register blueprints
    app.register_blueprint(mcp_bp)
    app.register_blueprint(code_executor_bp)
    # app.register_blueprint(visual_browser_api, url_prefix='/api/visual-browser')
    # app.register_blueprint(visual_browser_simple_api, url_prefix='/api/visual-browser-simple')
    app.register_blueprint(live_browser_api, url_prefix='/api/live-browser')
    app.register_blueprint(prime_agent_api)
    app.register_blueprint(browser_proxy_api)
    app.register_blueprint(feedback_api)
    app.register_blueprint(call_assistant_bp)
    app.register_blueprint(document_generator_bp)
    app.register_blueprint(code_ide_bp)
    app.register_blueprint(llm_tools_bp)
    # Code Wave chat blueprint removed
    app.register_blueprint(context7_tools_bp, url_prefix='/api/context7-tools')
    app.register_blueprint(enhanced_history_bp)
    app.register_blueprint(memory_test_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(screen_recorder_bp)
    app.register_blueprint(screen_recorder_ws_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register Agentic Code blueprint
    from app.api.agentic_code import agentic_code_bp
    app.register_blueprint(agentic_code_bp, url_prefix='/api/agentic-code')

    # Register Payment routes
    from app.routes.payment_routes import payment_bp
    app.register_blueprint(payment_bp)

    # Register Coupon routes
    from app.routes.coupon_routes import coupon_bp
    app.register_blueprint(coupon_bp)

    # Register Admin routes
    from app.routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp)

    # Register Health routes
    from app.routes.health_routes import health_bp
    app.register_blueprint(health_bp)

    # Register Referral routes
    from app.routes.referral_routes import referral_bp
    app.register_blueprint(referral_bp)

    # Start the Visual Browser services
    # try:
    #     print("Starting Visual Browser services...")
    #     start_visual_browser_services()
    #     print("Visual Browser services started successfully")
    # except Exception as e:
    #     print(f"Error starting Visual Browser services: {str(e)}")
    #     import traceback
    #     print(traceback.format_exc())

    @app.route('/')
    def index():
        # Handle UTM parameters for referral tracking
        utm_params = {}
        utm_keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']

        for key in utm_keys:
            value = request.args.get(key)
            if value:
                utm_params[key] = value

        # If UTM parameters are present, track the referral
        if utm_params:
            try:
                from app.services.referral_service import ReferralService
                referral_service = ReferralService()
                referral_data = referral_service.process_referral(utm_params)

                if referral_data.influencer_id:
                    # Store referral data in session
                    session['referral_data'] = {
                        'influencer_id': referral_data.influencer_id,
                        'utm_source': referral_data.utm_source,
                        'utm_medium': referral_data.utm_medium,
                        'utm_campaign': referral_data.utm_campaign,
                        'utm_content': referral_data.utm_content,
                        'utm_term': referral_data.utm_term,
                        'referral_code': referral_data.referral_code,
                        'discount_percentage': referral_data.discount_percentage,
                        'bonus_credits': referral_data.bonus_credits,
                        'created_at': datetime.utcnow().isoformat()
                    }

                    # Track the visit
                    user_id = session.get('user_id')
                    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
                    referral_service.track_referral_visit(referral_data, user_id, ip_address)

                    logger.info(f"Referral tracked on homepage: {referral_data.utm_source}")
            except Exception as e:
                logger.error(f"Error tracking referral on homepage: {e}")

        # TEMPORARY: Bypass authentication for testing history sidebar
        # TODO: Re-enable authentication after testing
        # if not session.get('user_id') or not session.get('user_email'):
        #     return redirect(url_for('auth.login_page'))

        return render_template('index.html')

    @app.route('/search', methods=['GET', 'POST'])
    def search():
        """
        ARCHIVED: Old search page - use Research Lab instead.
        This route has been archived because Research Lab now handles all research functionality.
        """
        # Show archived message
        return render_template('search.html', error="This search page has been archived. Please use Research Lab for research functionality.")

    @app.route('/chat', methods=['GET', 'POST'])
    def chat():
        """
        ARCHIVED: Old chat page - use Research Lab instead.
        This route has been archived because Research Lab now handles all chat functionality.
        """
        # Show archived message
        return render_template('chat.html', error="This chat page has been archived. Please use Research Lab for chat functionality.")

    @app.route('/history')
    def history():
        # Check if user is authenticated
        if not session.get('user_id') or not session.get('user_email'):
            return redirect(url_for('auth.login_page'))

        # ARCHIVED: Old history page - redirect to home with professional history sidebar
        # The new professional history system is accessible via the history icon on all pages
        return redirect(url_for('index'))

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # WARNING: ONLY WORK ON THE AUTOWAVE TEMPLATE FOR ALL UI CHANGES
    # All other templates should be considered archived and should not be modified
    # Do not create new templates - only use autowave.html for all frontend development
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # Prime Agent route - our enhanced AI assistant
    @app.route('/autowave')
    def autowave_page():
        # TEMPORARY: Bypass authentication for testing history sidebar
        # TODO: Re-enable authentication after testing
        # if not session.get('user_id') or not session.get('user_email'):
        #     return redirect(url_for('auth.login_page'))
        # Force fresh content with cache-busting headers
        response = make_response(render_template('autowave.html'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # Agent Wave route - user's preferred name for the autowave interface
    @app.route('/agent-wave')
    def agent_wave_page():
        # Check if user is authenticated
        if not session.get('user_id') or not session.get('user_email'):
            return redirect(url_for('auth.login_page'))
        # Force fresh content with cache-busting headers
        response = make_response(render_template('autowave.html'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # Redirect old super-agent route to autowave for backward compatibility
    @app.route('/super-agent')
    def super_agent_page():
        return redirect('/autowave')

    # Dark Chat route - completely separate dark-themed chat interface
    @app.route('/dark-chat')
    def dark_chat_page():
        return render_template('dark_chat.html')

    # Deep Research route - dark-themed academic research interface
    @app.route('/deep-research')
    def deep_research_page():
        # Force fresh content with cache-busting headers
        response = make_response(render_template('deep_research.html'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # Call Assistant route - dark-themed call assistant interface
    @app.route('/call-assistant')
    def call_assistant_page():
        return render_template('call_assistant.html')

    # Document Generator route - dark-themed document generation interface
    @app.route('/document-generator')
    def document_generator_page():
        return render_template('document_generator.html')

    # Code Wave routes removed - using Agentic Code instead

    # Context 7 Tools route - clean environment for Context 7 tools only
    @app.route('/context7-tools')
    def context7_tools_page():
        # Get task parameter from URL if provided
        task = request.args.get('task', '')
        return render_template('context7_tools.html', initial_task=task)

    # Agentic Code route - enhanced code editor with conversational AI capabilities
    @app.route('/agentic-code')
    def agentic_code_page():
        # Get message parameter from URL if provided
        message = request.args.get('message', '')
        # Force fresh content with cache-busting headers
        response = make_response(render_template('agentic_code.html', initial_message=message))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # Pricing route - subscription plans and billing (publicly accessible)
    @app.route('/pricing')
    def pricing_page():
        return render_template('pricing.html')

    # Footer navigation pages
    @app.route('/about')
    def about_page():
        return render_template('about.html')

    @app.route('/blog')
    def blog_page():
        return render_template('blog.html')

    @app.route('/privacy')
    def privacy_page():
        return render_template('privacy.html')

    @app.route('/terms')
    def terms_page():
        return render_template('terms.html')

    # Apple Pay domain verification route
    @app.route('/.well-known/<path:filename>')
    def well_known_files(filename):
        """Serve files from .well-known directory"""
        if filename == 'apple-developer-merchantid-domain-association':
            try:
                # Serve the verification file from static/.well-known/
                return send_from_directory(
                    os.path.join(app.root_path, 'static', '.well-known'),
                    'apple-developer-merchantid-domain-association',
                    mimetype='text/plain'
                )
            except FileNotFoundError:
                # Return a placeholder response if file doesn't exist yet
                return """This file will be provided by Paystack when you enable Apple Pay in your dashboard.

Steps to set up:
1. Log into Paystack dashboard
2. Go to Settings → Payment Methods → Apple Pay
3. Enable Apple Pay and add your domain
4. Download the verification file
5. Upload it to /static/.well-known/ in your project""", 200, {'Content-Type': 'text/plain'}
        else:
            # For other .well-known files, return 404
            return "File not found", 404

    @app.route('/test')
    def test_page():
        return render_template('test.html')

    @app.route('/test-js')
    def test_js_page():
        return render_template('test_js.html')

    @app.route('/test-agentic')
    def test_agentic_page():
        return send_from_directory('.', 'test_agentic_capability.html')

    @app.route('/test-ui')
    def test_ui_page():
        return send_from_directory('.', 'test_ui_functionality.html')

    @app.route('/google-frame')
    def google_frame():
        return render_template('google_frame.html')

    @app.route('/chrome-simulation')
    def chrome_simulation():
        return render_template('chrome_simulation.html')

    # API endpoints for AJAX requests
    @app.route('/api/search', methods=['POST'])
    def api_search():
        """
        Search API for Research Lab functionality.
        This API is used by the Research Lab page (/deep-research).
        """
        data = request.get_json()
        query = data.get('query', '')
        if not query:
            return jsonify({'error': 'No query provided'}), 400

        # Get user ID from session for credit consumption
        user_id = session.get('user_id', 'anonymous')

        # Import the search API
        from app.api.search import do_search

        # Process search using the search API with user_id for credit consumption
        response = do_search(query, user_id=user_id)

        return jsonify(response)

    @app.route('/api/research-feedback', methods=['POST'])
    def api_research_feedback():
        data = request.get_json()
        feedback_type = data.get('feedback_type', '')
        query = data.get('query', '')
        results = data.get('results', '')

        if not feedback_type or not query:
            return jsonify({'error': 'Missing required parameters'}), 400

        # Import the feedback function from search.py
        from app.api.search import save_research_feedback

        # Save the feedback
        response = save_research_feedback(feedback_type, query, results)

        return jsonify(response)

    @app.route('/api/chat', methods=['POST'])
    def api_chat():
        """
        Chat API for AutoWave Chat functionality.
        This API is used by the AutoWave Chat page (/dark-chat).
        """
        start_time = time.time()
        data = request.get_json()
        message = data.get('message', '')
        user_id = data.get('user_id')  # Get user_id from request if available
        session_id = data.get('session_id')  # Get session_id from request if available

        if not message:
            return jsonify({'error': 'No message provided'}), 400

        # Get user_id from session if not provided in request
        if not user_id:
            user_id = session.get('user_id', 'anonymous')

        # Check and consume credits before processing
        from app.services.credit_service import credit_service

        # Determine credit cost based on message complexity (Genspark-style: 1-3 credits)
        if len(message) > 500 or any(keyword in message.lower() for keyword in ['analyze', 'research', 'detailed', 'comprehensive']):
            task_type = 'autowave_chat_advanced'  # 3 credits
        else:
            task_type = 'autowave_chat_basic'     # 1 credit

        # Consume credits
        credit_result = credit_service.consume_credits(user_id, task_type)

        if not credit_result['success']:
            return jsonify({
                'success': False,
                'error': credit_result.get('error', 'Insufficient credits'),
                'credits_needed': credit_result.get('credits_needed'),
                'credits_available': credit_result.get('credits_available')
            }), 402

        # Import the chat API and activity logger
        from app.api.chat import do_chat
        from app.services.activity_logger import log_chat_activity

        # Process chat using the chat API
        response = do_chat(message)

        # Add credit consumption info to response
        if isinstance(response, dict):
            response['credits_consumed'] = credit_result['credits_consumed']
            response['remaining_credits'] = credit_result['remaining_credits']
        else:
            response = {
                'response': response,
                'credits_consumed': credit_result['credits_consumed'],
                'remaining_credits': credit_result['remaining_credits']
            }

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log activity if user_id is available
        if user_id and user_id != 'anonymous':
            try:
                log_chat_activity(
                    user_id=user_id,
                    message=message,
                    response=response.get('response', ''),
                    processing_time_ms=processing_time_ms,
                    session_id=session_id
                )
            except Exception as e:
                logger.error(f"Failed to log chat activity: {e}")

        return jsonify(response)

    # Prime Agent API endpoints
    # Keep the old super-agent endpoints for backward compatibility
    @app.route('/api/super-agent/browse', methods=['POST'])
    def api_super_agent_browse():
        return super_agent_api.browse_web()

    @app.route('/api/super-agent/analyze', methods=['POST'])
    def api_super_agent_analyze():
        return super_agent_api.analyze_webpage()

    @app.route('/api/super-agent/submit-form', methods=['POST'])
    def api_super_agent_submit_form():
        return super_agent_api.submit_form()

    @app.route('/api/super-agent/follow-link', methods=['POST'])
    def api_super_agent_follow_link():
        return super_agent_api.follow_link()

    @app.route('/api/super-agent/generate-code', methods=['POST'])
    def api_super_agent_generate_code():
        return super_agent_api.generate_code()

    @app.route('/api/super-agent/execute-task', methods=['POST'])
    def api_super_agent_execute_task():
        return super_agent_api.execute_task()

    @app.route('/api/super-agent/session-history', methods=['GET'])
    def api_super_agent_session_history():
        return super_agent_api.get_session_history()

    @app.route('/api/super-agent/clear-session', methods=['POST'])
    def api_super_agent_clear_session():
        return super_agent_api.clear_session()

    @app.route('/api/super-agent/code-snippets', methods=['GET'])
    def api_super_agent_code_snippets():
        return super_agent_api.get_code_snippets()

    @app.route('/api/super-agent/reset', methods=['POST'])
    def api_super_agent_reset():
        return super_agent_api.reset_agent()

    @app.route('/api/super-agent/generate-project', methods=['POST'])
    def api_super_agent_generate_project():
        return super_agent_api.generate_project()

    @app.route('/api/super-agent/task-status', methods=['GET'])
    def api_super_agent_task_status():
        return super_agent_api.get_task_status()

    return app
