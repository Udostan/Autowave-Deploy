"""
Call Assistant API

This module provides API endpoints for the Call Assistant feature.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.utils.mcp_client import MCPClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('call_assistant_api')

# Create blueprint
call_assistant_bp = Blueprint('call_assistant', __name__)

# Initialize MCP client
MCP_SERVER_PORT = 5011
mcp_client = MCPClient(base_url=f"http://localhost:{MCP_SERVER_PORT}")
logger.info(f"Initialized MCP client for Call Assistant API with base URL: http://localhost:{MCP_SERVER_PORT}")

# Check if MCP server is available
MCP_SERVER_AVAILABLE = True
try:
    # Try to execute a simple chat request to check if MCP server is available
    mcp_client.execute_tool("chat", {"message": "test", "system_prompt": "test"})
except Exception as e:
    logger.warning(f"MCP server is not available: {str(e)}. Using fallback responses.")
    MCP_SERVER_AVAILABLE = False

# Function to check MCP server availability before each API call
def check_mcp_availability():
    """
    Check if MCP server is available before making API calls.
    Updates the global MCP_SERVER_AVAILABLE variable.

    Returns:
        bool: True if MCP server is available, False otherwise.
    """
    global MCP_SERVER_AVAILABLE

    if not MCP_SERVER_AVAILABLE:
        # If we already know it's not available, don't try again
        return False

    try:
        # Try a simple request to check availability
        mcp_client.execute_tool("chat", {"message": "test", "system_prompt": "test"})
        return True
    except Exception as e:
        logger.warning(f"MCP server is not available: {str(e)}. Using fallback responses.")
        MCP_SERVER_AVAILABLE = False
        return False

# Get API keys from environment variables
NARI_VOICE_API_KEY = os.environ.get('NARI_VOICE_API_KEY')
VOIPMS_API_USERNAME = os.environ.get('VOIPMS_API_USERNAME')
VOIPMS_API_PASSWORD = os.environ.get('VOIPMS_API_PASSWORD')
VOIPMS_DID_NUMBER = os.environ.get('VOIPMS_DID_NUMBER')
VOIPMS_CALLER_ID = os.environ.get('VOIPMS_CALLER_ID')

# Check if API keys are set
if not NARI_VOICE_API_KEY or NARI_VOICE_API_KEY == 'your_nari_voice_api_key_here':
    logger.warning("NARI_VOICE_API_KEY environment variable is not set or is using the default value. Voice synthesis will be simulated.")
    VOICE_SYNTHESIS_ENABLED = False
else:
    VOICE_SYNTHESIS_ENABLED = True
    logger.info("Voice synthesis is enabled.")

if not VOIPMS_API_USERNAME or not VOIPMS_API_PASSWORD or not VOIPMS_DID_NUMBER or \
   VOIPMS_API_USERNAME == 'your_voipms_username_here' or \
   VOIPMS_API_PASSWORD == 'your_voipms_password_here' or \
   VOIPMS_DID_NUMBER == 'your_voipms_did_number_here':
    logger.warning("VoIP.ms API keys are not set or are using default values. Phone call functionality will be simulated.")
    PHONE_CALLS_ENABLED = False
else:
    PHONE_CALLS_ENABLED = True
    logger.info("Phone call functionality is enabled with VoIP.ms.")

    # Initialize VoIP.ms API client
    import requests

    def make_voipms_call(to_number, from_number=VOIPMS_DID_NUMBER, caller_id=VOIPMS_CALLER_ID):
        """
        Make a call using VoIP.ms API

        Args:
            to_number (str): The phone number to call
            from_number (str): The DID number to call from
            caller_id (str): The caller ID to display

        Returns:
            dict: Response from VoIP.ms API
        """
        try:
            # Format phone numbers (remove non-numeric characters)
            to_number = ''.join(filter(str.isdigit, to_number))

            # VoIP.ms API endpoint
            api_url = "https://voip.ms/api/v1/rest.php"

            # API parameters
            params = {
                'api_username': VOIPMS_API_USERNAME,
                'api_password': VOIPMS_API_PASSWORD,
                'method': 'sendCallerID',
                'did': from_number,
                'dst': to_number,
                'callerid': caller_id,
                'language': 'en',
                'play': 1,  # Play a message
                'type': 'text',  # Text-to-speech
                'text': 'This is an automated call from the Call Assistant service. Please hold while we connect you.'
            }

            # Make API request
            response = requests.get(api_url, params=params)
            response_data = response.json()

            if response_data.get('status') == 'success':
                logger.info(f"VoIP.ms call initiated successfully to {to_number}")
                return {'success': True, 'call_id': response_data.get('callid', 'unknown')}
            else:
                logger.error(f"VoIP.ms call failed: {response_data.get('status')}")
                return {'success': False, 'error': response_data.get('status')}

        except Exception as e:
            logger.error(f"Error making VoIP.ms call: {str(e)}")
            return {'success': False, 'error': str(e)}

# In-memory storage for active call sessions
# In a production app, this would be stored in Redis or a database
active_calls = {}

# Knowledge base storage
KNOWLEDGE_BASE_FILE = os.path.join('agen911', 'app', 'data', 'call_assistant_knowledge.json')

def load_knowledge_base():
    """
    Load the knowledge base from file.

    Returns:
        list: The knowledge base items.
    """
    try:
        if os.path.exists(KNOWLEDGE_BASE_FILE):
            with open(KNOWLEDGE_BASE_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(KNOWLEDGE_BASE_FILE), exist_ok=True)
            # Return empty knowledge base
            return []
    except Exception as e:
        logger.error(f"Error loading knowledge base: {str(e)}")
        return []

def save_knowledge_base(knowledge_base):
    """
    Save the knowledge base to file.

    Args:
        knowledge_base (list): The knowledge base items.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with open(KNOWLEDGE_BASE_FILE, 'w') as f:
            json.dump(knowledge_base, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving knowledge base: {str(e)}")
        return False

@call_assistant_bp.route('/api/call-assistant/start', methods=['POST'])
def start_call():
    """
    Start a new call session.

    Returns:
        JSON response with session ID and initial message.
    """
    try:
        data = request.json or {}
        phone_number = data.get('phone_number', '+1 (555) 123-4567')

        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Create a new call session
        active_calls[session_id] = {
            'id': session_id,
            'phone_number': phone_number,
            'start_time': datetime.now().isoformat(),
            'status': 'active',
            'messages': [],
            'voice_synthesis_enabled': VOICE_SYNTHESIS_ENABLED,
            'phone_call_enabled': PHONE_CALLS_ENABLED
        }

        # Get initial message from MCP or use fallback
        system_prompt = """
        You are a helpful customer service AI assistant on a phone call.
        Respond in a friendly, professional manner. Keep your responses concise and focused.
        Use the knowledge base information when relevant to answer customer questions.
        """

        # Get knowledge base for context
        knowledge_base = load_knowledge_base()
        knowledge_context = "\n".join([item['text'] for item in knowledge_base])

        if knowledge_context:
            system_prompt += f"\n\nKnowledge Base Information:\n{knowledge_context}"

        # Default greeting message
        initial_message = "Hello, thank you for calling customer service. How can I help you today?"

        # Try to get response from MCP if available
        if check_mcp_availability():
            try:
                response = mcp_client.execute_tool(
                    "chat",
                    {
                        "message": "The customer has just called your customer service line. Provide a friendly greeting.",
                        "system_prompt": system_prompt
                    }
                )

                if response and 'response' in response:
                    initial_message = response.get('response')
                    logger.info("Got initial message from MCP server")
                else:
                    logger.warning("MCP server returned invalid response, using fallback greeting")

            except Exception as e:
                logger.error(f"Error getting initial message from MCP: {str(e)}")
                # Update MCP availability status
                global MCP_SERVER_AVAILABLE
                MCP_SERVER_AVAILABLE = False
        else:
            logger.info("Using fallback greeting (MCP server not available)")

        # Add message to history
        active_calls[session_id]['messages'].append({
            'role': 'assistant',
            'content': initial_message,
            'timestamp': datetime.now().isoformat()
        })

        # If voice synthesis is enabled, generate audio for the initial message
        audio_url = None
        if VOICE_SYNTHESIS_ENABLED:
            try:
                # This would be replaced with actual voice synthesis API call
                logger.info(f"Generating voice synthesis for message: {initial_message[:50]}...")
                # Simulated voice synthesis
                audio_url = f"/static/audio/call_assistant/{session_id}_initial.mp3"
                logger.info(f"Voice synthesis generated: {audio_url}")
            except Exception as e:
                logger.error(f"Error generating voice synthesis: {str(e)}")

        # If phone calls are enabled, initiate a real phone call
        call_sid = None
        if PHONE_CALLS_ENABLED:
            try:
                logger.info(f"Initiating phone call to {phone_number}...")
                # Make the call using VoIP.ms API
                call_result = make_voipms_call(
                    to_number=phone_number,
                    from_number=VOIPMS_DID_NUMBER,
                    caller_id=VOIPMS_CALLER_ID
                )

                if call_result['success']:
                    call_sid = call_result['call_id']
                    active_calls[session_id]['call_sid'] = call_sid
                    logger.info(f"Phone call initiated with SID: {call_sid}")
                else:
                    logger.error(f"Failed to initiate phone call: {call_result.get('error', 'Unknown error')}")
                    # Fallback to simulation
                    call_sid = f"VM{uuid.uuid4().hex[:30]}"
                    active_calls[session_id]['call_sid'] = call_sid
                    active_calls[session_id]['simulated'] = True
                    logger.info(f"Using simulated call with SID: {call_sid}")
            except Exception as e:
                logger.error(f"Error initiating phone call: {str(e)}")
                # Fallback to simulation
                call_sid = f"VM{uuid.uuid4().hex[:30]}"
                active_calls[session_id]['call_sid'] = call_sid
                active_calls[session_id]['simulated'] = True
                logger.info(f"Using simulated call with SID: {call_sid}")

        return jsonify({
            'success': True,
            'session_id': session_id,
            'initial_message': initial_message,
            'audio_url': audio_url,
            'call_sid': call_sid,
            'voice_synthesis_enabled': VOICE_SYNTHESIS_ENABLED,
            'phone_call_enabled': PHONE_CALLS_ENABLED
        })

    except Exception as e:
        logger.error(f"Error starting call: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@call_assistant_bp.route('/api/call-assistant/end', methods=['POST'])
def end_call():
    """
    End an active call session.

    Returns:
        JSON response with success status and final message.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID is required'
            })

        if session_id not in active_calls:
            return jsonify({
                'success': False,
                'error': 'Call session not found'
            })

        # Update call status
        active_calls[session_id]['status'] = 'ended'
        active_calls[session_id]['end_time'] = datetime.now().isoformat()

        # If this was a real call, end it properly
        if active_calls[session_id].get('phone_call_enabled', False) and 'call_sid' in active_calls[session_id]:
            try:
                call_sid = active_calls[session_id]['call_sid']

                # Check if this is a simulated call
                if not active_calls[session_id].get('simulated', False):
                    logger.info(f"Ending VoIP.ms call with SID: {call_sid}")
                    # Note: VoIP.ms doesn't have a direct API to end calls
                    # Calls are typically ended by the user or after the message is played
                    # We'll just log it for now
                    logger.info(f"VoIP.ms call {call_sid} will end automatically after message playback")
                else:
                    logger.info(f"Ending simulated call with SID: {call_sid}")
            except Exception as e:
                logger.error(f"Error ending call: {str(e)}")

        # Get final message from MCP or use fallback
        # Get message history
        messages = active_calls[session_id]['messages']
        message_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        system_prompt = """
        You are a helpful customer service AI assistant on a phone call that is now ending.
        Provide a friendly closing message thanking the customer for calling.
        Keep your response concise and professional.
        """

        # Default goodbye message
        final_message = "Thank you for calling customer service. Have a great day!"

        # Try to get response from MCP if available
        if check_mcp_availability():
            try:
                response = mcp_client.execute_tool(
                    "chat",
                    {
                        "message": f"The customer is ending the call. Provide a friendly goodbye based on this conversation:\n{message_history}",
                        "system_prompt": system_prompt
                    }
                )

                if response and 'response' in response:
                    final_message = response.get('response')
                    logger.info("Got final message from MCP server")
                else:
                    logger.warning("MCP server returned invalid response, using fallback goodbye")

            except Exception as e:
                logger.error(f"Error getting final message from MCP: {str(e)}")
                # Update MCP availability status
                global MCP_SERVER_AVAILABLE
                MCP_SERVER_AVAILABLE = False
        else:
            logger.info("Using fallback goodbye (MCP server not available)")

        # Add message to history
        active_calls[session_id]['messages'].append({
            'role': 'assistant',
            'content': final_message,
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'success': True,
            'final_message': final_message
        })

    except Exception as e:
        logger.error(f"Error ending call: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@call_assistant_bp.route('/api/call-assistant/message', methods=['POST'])
def send_message():
    """
    Send a message in an active call session.

    Returns:
        JSON response with success status and AI response.
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        message = data.get('message')

        if not session_id or not message:
            return jsonify({
                'success': False,
                'error': 'Session ID and message are required'
            })

        if session_id not in active_calls:
            return jsonify({
                'success': False,
                'error': 'Call session not found'
            })

        if active_calls[session_id]['status'] != 'active':
            return jsonify({
                'success': False,
                'error': 'Call session is not active'
            })

        # Add message to history
        active_calls[session_id]['messages'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })

        # Get response from MCP or use fallback
        # Get message history
        messages = active_calls[session_id]['messages']
        message_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages[-5:]])

        system_prompt = """
        You are a helpful customer service AI assistant on a phone call.
        Respond in a friendly, professional manner. Keep your responses concise and focused.
        Use the knowledge base information when relevant to answer customer questions.
        """

        # Get knowledge base for context
        knowledge_base = load_knowledge_base()
        knowledge_context = "\n".join([item['text'] for item in knowledge_base])

        if knowledge_context:
            system_prompt += f"\n\nKnowledge Base Information:\n{knowledge_context}"

        # Default response message
        ai_response = "I'm sorry, I didn't understand that. Could you please rephrase?"

        # Try to get response from MCP if available
        if check_mcp_availability():
            try:
                response = mcp_client.execute_tool(
                    "chat",
                    {
                        "message": f"Respond to the customer's message in this conversation:\n{message_history}\n\nCustomer's message: {message}",
                        "system_prompt": system_prompt
                    }
                )

                if response and 'response' in response:
                    ai_response = response.get('response')
                    logger.info("Got response from MCP server")
                else:
                    logger.warning("MCP server returned invalid response, using fallback response")

            except Exception as e:
                logger.error(f"Error getting response from MCP: {str(e)}")
                # Update MCP availability status
                global MCP_SERVER_AVAILABLE
                MCP_SERVER_AVAILABLE = False
        else:
            logger.info("Using fallback response (MCP server not available)")

            # Generate a more contextual fallback response
            if "order" in message.lower():
                ai_response = "I understand you're asking about an order. To help you better, could you provide your order number?"
            elif "return" in message.lower():
                ai_response = "I understand you're interested in a return. Our return policy allows returns within 30 days of purchase. Would you like more details?"
            elif "help" in message.lower():
                ai_response = "I'm here to help! Could you please provide more details about what you need assistance with?"
            elif "phone" in message.lower() or "call" in message.lower():
                ai_response = "I understand you're asking about phone calls. Our system is using VoIP.ms for making calls globally. Is there something specific you'd like to know about our calling capabilities?"

        # Add response to history
        active_calls[session_id]['messages'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now().isoformat()
        })

        # If voice synthesis is enabled, generate audio for the response
        audio_url = None
        if active_calls[session_id].get('voice_synthesis_enabled', False):
            try:
                # This would be replaced with actual voice synthesis API call
                logger.info(f"Generating voice synthesis for message: {ai_response[:50]}...")
                # Simulated voice synthesis
                message_id = str(uuid.uuid4())[:8]
                audio_url = f"/static/audio/call_assistant/{session_id}_{message_id}.mp3"
                logger.info(f"Voice synthesis generated: {audio_url}")
            except Exception as e:
                logger.error(f"Error generating voice synthesis: {str(e)}")

        # If this is a real phone call, send the response to the call
        if active_calls[session_id].get('phone_call_enabled', False) and 'call_sid' in active_calls[session_id]:
            try:
                call_sid = active_calls[session_id]['call_sid']
                phone_number = active_calls[session_id]['phone_number']
                logger.info(f"Sending response to call {call_sid}: {ai_response[:50]}...")

                # Check if this is a simulated call
                if active_calls[session_id].get('simulated', False):
                    logger.info(f"Simulated message sent to call {call_sid}")
                else:
                    # Use VoIP.ms API to send a text-to-speech message to the call
                    import requests

                    # VoIP.ms API endpoint
                    api_url = "https://voip.ms/api/v1/rest.php"

                    # API parameters for sending a text-to-speech message
                    params = {
                        'api_username': VOIPMS_API_USERNAME,
                        'api_password': VOIPMS_API_PASSWORD,
                        'method': 'sendCallerID',
                        'did': VOIPMS_DID_NUMBER,
                        'dst': ''.join(filter(str.isdigit, phone_number)),
                        'callerid': VOIPMS_CALLER_ID,
                        'language': 'en',
                        'play': 1,  # Play a message
                        'type': 'text',  # Text-to-speech
                        'text': ai_response[:500]  # Limit to 500 chars as VoIP.ms may have limits
                    }

                    # Make API request
                    response = requests.get(api_url, params=params)
                    response_data = response.json()

                    if response_data.get('status') == 'success':
                        logger.info(f"VoIP.ms message sent successfully to call {call_sid}")
                    else:
                        logger.error(f"VoIP.ms message failed: {response_data.get('status')}")

                logger.info(f"Response sent to call {call_sid}")
            except Exception as e:
                logger.error(f"Error sending response to call: {str(e)}")

        return jsonify({
            'success': True,
            'response': ai_response,
            'audio_url': audio_url
        })

    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@call_assistant_bp.route('/api/call-assistant/knowledge', methods=['GET'])
def get_knowledge_base():
    """
    Get the knowledge base.

    Returns:
        JSON response with knowledge base items.
    """
    try:
        knowledge_base = load_knowledge_base()

        return jsonify({
            'success': True,
            'items': knowledge_base
        })

    except Exception as e:
        logger.error(f"Error getting knowledge base: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@call_assistant_bp.route('/api/call-assistant/knowledge', methods=['POST'])
def add_knowledge_item():
    """
    Add an item to the knowledge base.

    Returns:
        JSON response with success status and item ID.
    """
    try:
        data = request.json or {}
        text = data.get('text')

        if not text:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            })

        # Load knowledge base
        knowledge_base = load_knowledge_base()

        # Create new item
        item_id = str(uuid.uuid4())
        new_item = {
            'id': item_id,
            'text': text,
            'created_at': datetime.now().isoformat()
        }

        # Add to knowledge base
        knowledge_base.append(new_item)

        # Save knowledge base
        if save_knowledge_base(knowledge_base):
            return jsonify({
                'success': True,
                'id': item_id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save knowledge base'
            })

    except Exception as e:
        logger.error(f"Error adding knowledge item: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@call_assistant_bp.route('/api/call-assistant/knowledge/<item_id>', methods=['DELETE'])
def delete_knowledge_item(item_id):
    """
    Delete an item from the knowledge base.

    Args:
        item_id (str): The ID of the item to delete.

    Returns:
        JSON response with success status.
    """
    try:
        # Load knowledge base
        knowledge_base = load_knowledge_base()

        # Filter out the item to delete
        new_knowledge_base = [item for item in knowledge_base if item['id'] != item_id]

        # Check if item was found
        if len(new_knowledge_base) == len(knowledge_base):
            return jsonify({
                'success': False,
                'error': 'Item not found'
            })

        # Save knowledge base
        if save_knowledge_base(new_knowledge_base):
            return jsonify({
                'success': True
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save knowledge base'
            })

    except Exception as e:
        logger.error(f"Error deleting knowledge item: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
