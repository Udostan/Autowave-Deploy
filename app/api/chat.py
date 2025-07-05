from .gemini import GeminiAPI
import random
import logging
import os
import time
import requests
from flask import Blueprint, request, jsonify
from .local_llm import generate_response as local_llm_generate
from app.utils.mcp_client import MCPClient
from app.services.file_processor import file_processor
from app.services.activity_logger import log_chat_activity

# Create blueprint
chat_bp = Blueprint('chat', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('chat_api')

# Initialize MCP client with the correct port and retry logic
MCP_SERVER_PORT = 5011
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Create MCP client with retry capability
mcp_client = MCPClient(base_url=f"http://localhost:{MCP_SERVER_PORT}")
logger.info(f"Initialized MCP client for chat API with base URL: http://localhost:{MCP_SERVER_PORT}")

# Check if the MCP server is running
def check_mcp_server():
    try:
        response = requests.get(f"http://localhost:{MCP_SERVER_PORT}/api/mcp/tools", timeout=5)
        if response.status_code == 200:
            logger.info("MCP server is running and responding")
            return True
        else:
            logger.error(f"MCP server returned status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to MCP server: {e}")
        return False

# Try to connect to the MCP server
mcp_server_available = check_mcp_server()
if not mcp_server_available:
    logger.warning("MCP server is not available. Chat functionality will use fallback methods.")

# Check if we should use the local LLM by default
USE_LOCAL_LLM = os.environ.get('USE_LOCAL_LLM', 'false').lower() == 'true'
# Check if we should use the MCP server by default
USE_MCP_SERVER = os.environ.get('USE_MCP_SERVER', 'true').lower() == 'true'
logger.info(f"Local LLM default mode: {'ENABLED' if USE_LOCAL_LLM else 'DISABLED'}")
logger.info(f"MCP Server default mode: {'ENABLED' if USE_MCP_SERVER else 'DISABLED'}")

# Predefined responses for different types of questions (used as backup if local_llm fails)
FALLBACK_RESPONSES = {
    "greeting": [
        "Hello! I'm your AI assistant. How can I help you today?",
        "Hi there! I'm here to assist you. What can I do for you?",
        "Greetings! How may I assist you today?",
        "Welcome! I'm your virtual assistant. How can I be of service?"
    ],
    "question": [
        "That's an interesting question. I'd love to help you with that, but I'm currently in offline mode due to API limitations.",
        "Great question! I'm currently operating in fallback mode due to API quota limits, but I'd be happy to try again later.",
        "I appreciate your curiosity! I'm currently using a local response system while our API connections are being updated."
    ],
    "general": [
        "I understand what you're asking. While I'm currently operating in fallback mode, I'd be happy to assist you once our API services are back online.",
        "Thanks for your message. I'm currently using a local response system due to API limitations. Please try again later for a more detailed response.",
        "I appreciate your patience. Our API services are currently at capacity, but I'm here to acknowledge your request."
    ]
}

def categorize_message(message):
    """Categorize the message to determine the appropriate fallback response."""
    message = message.lower()

    # Check for greetings
    if any(word in message for word in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
        return "greeting"

    # Check for questions
    if any(word in message for word in ["what", "how", "why", "when", "where", "who", "which", "?"]):
        return "question"

    # Default category
    return "general"

def get_fallback_response(message):
    """Get a fallback response based on the message category."""
    try:
        # First try to use the local LLM
        return local_llm_generate(message)
    except Exception as e:
        logger.error(f"Error using local LLM: {e}")
        # Fall back to the category-based responses if local LLM fails
        category = categorize_message(message)
        responses = FALLBACK_RESPONSES.get(category, FALLBACK_RESPONSES["general"])
        return random.choice(responses)

def do_chat(message):
    """Process a chat message using the MCP server or fallback methods.

    Args:
        message (str): The user's chat message (may include file content)

    Returns:
        dict: A dictionary containing the chat response
    """
    # Define the system prompt
    system_prompt = "You are a helpful AI assistant. Respond to the following message in a friendly and informative way."

    # Log the incoming message
    logger.info(f"=== CHAT API CALLED WITH MESSAGE: {message} ===")

    # Handle URL-encoded characters
    import urllib.parse
    decoded_message = urllib.parse.unquote(message)
    logger.info(f"=== DECODED MESSAGE: {decoded_message} ===")

    # Check if the message contains file content and process it
    enhanced_message = decoded_message
    file_context = ""

    if "--- File:" in decoded_message or "--- Image:" in decoded_message:
        logger.info("File content detected in message, processing files...")
        try:
            # Extract the original user message (before file content)
            parts = decoded_message.split('\n\n--- File:')
            if len(parts) > 1:
                original_message = parts[0]
                file_content = '\n\n--- File:' + '\n\n--- File:'.join(parts[1:])
            else:
                parts = decoded_message.split('\n\n--- Image:')
                if len(parts) > 1:
                    original_message = parts[0]
                    file_content = '\n\n--- Image:' + '\n\n--- Image:'.join(parts[1:])
                else:
                    original_message = decoded_message
                    file_content = ""

            if file_content:
                # Use the file processor to enhance the message
                enhanced_message = file_processor.enhance_prompt_with_files(original_message, file_content)
                file_context = f" (with {file_content.count('--- File:') + file_content.count('--- Image:')} uploaded file(s))"
                logger.info(f"Enhanced message with file analysis: {len(enhanced_message)} characters")
        except Exception as e:
            logger.error(f"Error processing files: {str(e)}")
            # Continue with original message if file processing fails
            enhanced_message = decoded_message

    # Update the system prompt to include file processing capabilities
    if file_context:
        system_prompt = f"You are a helpful AI assistant with file analysis capabilities. The user has uploaded files{file_context}. Analyze the uploaded files and respond to their request in a friendly and informative way, using the file content to provide accurate and relevant assistance."

    # Check if this is a commercial/sensitive question that should always use LLM
    # This helps ensure commercial questions always get fresh, accurate responses
    commercial_keywords = [
        'business', 'company', 'startup', 'investment', 'finance', 'market',
        'strategy', 'product', 'service', 'customer', 'client', 'revenue',
        'profit', 'sales', 'marketing', 'advertising', 'brand', 'competitor',
        'industry', 'sector', 'economy', 'stock', 'share', 'investor',
        'enterprise', 'commercial', 'corporate', 'organization', 'management'
    ]

    is_commercial_question = any(keyword in enhanced_message.lower() for keyword in commercial_keywords)

    # For non-commercial questions, we can still use pattern matching for very common factual questions
    # but only as a last resort fallback
    pattern_response = None
    if not is_commercial_question:
        try:
            from app.mcp.tools.chat_tools import ChatTools
            chat_tools = ChatTools()
            pattern_response = chat_tools._check_pattern_match(decoded_message)
            # We'll store this for later use as fallback, but won't use it immediately
        except Exception as e:
            logger.warning(f"Error using pattern matching: {e}")

    # If MCP server is available, try to use it with retries
    if mcp_server_available:
        for retry in range(MAX_RETRIES):
            try:
                logger.info(f"Using MCP server for message (attempt {retry+1}/{MAX_RETRIES}): {decoded_message}")
                logger.info(f"MCP server URL: {mcp_client.base_url}")

                # Call the MCP chat tool
                response = mcp_client.execute_tool(
                    "chat",
                    {
                        "message": enhanced_message,
                        "system_prompt": system_prompt
                    }
                )

                # Add detailed logging
                logger.info(f"Full MCP response: {response}")

                # Check if we got a successful response
                if response and response.get("status") == "success" and "result" in response:
                    # Check if the response indicates offline mode or limited functionality
                    if "offline mode" in str(response["result"]) or "limited functionality" in str(response["result"]) or "limited response" in str(response["result"]):
                        logger.warning("MCP server is in offline mode or has limited functionality, bypassing to direct API calls")
                        break  # Exit the retry loop to try direct API calls

                    # Check if this is a commercial/business question
                    commercial_keywords = [
                        'business', 'company', 'startup', 'investment', 'finance', 'market',
                        'strategy', 'product', 'service', 'customer', 'client', 'revenue',
                        'profit', 'sales', 'marketing', 'advertising', 'brand', 'competitor',
                        'industry', 'sector', 'economy', 'stock', 'share', 'investor',
                        'enterprise', 'commercial', 'corporate', 'organization', 'management'
                    ]

                    is_commercial_question = any(keyword in decoded_message.lower() for keyword in commercial_keywords)

                    # For commercial questions, prefer direct API calls over MCP server
                    if is_commercial_question:
                        logger.info("Commercial question detected, bypassing MCP server to use direct API calls")
                        break  # Exit the retry loop to try direct API calls

                    logger.info("Successfully got response from MCP server")
                    logger.info(f"=== RETURNING MCP RESPONSE (success): {str(response['result'])[:100]}... ===")
                    return {"response": response["result"]}
                elif response and "result" in response:
                    # Check if the response indicates offline mode or limited functionality
                    if "offline mode" in str(response["result"]) or "limited functionality" in str(response["result"]) or "limited response" in str(response["result"]):
                        logger.warning("MCP server is in offline mode or has limited functionality, bypassing to direct API calls")
                        break  # Exit the retry loop to try direct API calls

                    # Check if this is a commercial/business question
                    commercial_keywords = [
                        'business', 'company', 'startup', 'investment', 'finance', 'market',
                        'strategy', 'product', 'service', 'customer', 'client', 'revenue',
                        'profit', 'sales', 'marketing', 'advertising', 'brand', 'competitor',
                        'industry', 'sector', 'economy', 'stock', 'share', 'investor',
                        'enterprise', 'commercial', 'corporate', 'organization', 'management'
                    ]

                    is_commercial_question = any(keyword in decoded_message.lower() for keyword in commercial_keywords)

                    # For commercial questions, prefer direct API calls over MCP server
                    if is_commercial_question:
                        logger.info("Commercial question detected, bypassing MCP server to use direct API calls")
                        break  # Exit the retry loop to try direct API calls

                    # Some MCP responses might not have a status field but still have a result
                    logger.info("Got response from MCP server without status field")
                    logger.info(f"=== RETURNING MCP RESPONSE (no status): {str(response['result'])[:100]}... ===")
                    return {"response": response["result"]}
                else:
                    logger.warning(f"MCP server error: {response.get('error', 'Unknown error')}")

                    # If this is not the last retry, wait and try again
                    if retry < MAX_RETRIES - 1:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                    else:
                        # On the last retry, fall back to local LLM
                        logger.info("All MCP server retries failed, falling back to local LLM")
                        break
            except Exception as e:
                logger.error(f"Error using MCP server (attempt {retry+1}/{MAX_RETRIES}): {e}")

                # If this is not the last retry, wait and try again
                if retry < MAX_RETRIES - 1:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    # On the last retry, fall back to local LLM
                    logger.info("All MCP server retries failed, falling back to local LLM")
                    break

    # Check if this is a commercial/business question
    commercial_keywords = [
        'business', 'company', 'startup', 'investment', 'finance', 'market',
        'strategy', 'product', 'service', 'customer', 'client', 'revenue',
        'profit', 'sales', 'marketing', 'advertising', 'brand', 'competitor',
        'industry', 'sector', 'economy', 'stock', 'share', 'investor',
        'enterprise', 'commercial', 'corporate', 'organization', 'management'
    ]

    is_commercial_question = any(keyword in decoded_message.lower() for keyword in commercial_keywords)

    # For all questions, try to use Groq API directly first, but prioritize commercial questions
    try:
        # Choose the appropriate model based on the question type
        # Use Llama 3 8B for general questions (most cost-effective)
        # Use Llama 3 70B for commercial/business questions (better quality for business topics)
        model_name = "llama3-70b-8192" if is_commercial_question else "llama3-8b-8192"

        if is_commercial_question:
            logger.info(f"Commercial question detected, using Groq API with {model_name} model for message: {decoded_message}")
        else:
            logger.info(f"Using Groq API with {model_name} model for general question: {decoded_message}")

        from app.api.groq import GroqAPI
        groq_api = GroqAPI()
        groq_response = groq_api.generate_text(f"{system_prompt}\n\nUser: {enhanced_message}", model=model_name)

        if groq_response and not "Error" in groq_response:
            logger.info(f"Successfully got response from Groq API using {model_name} model")
            logger.info(f"=== RETURNING GROQ RESPONSE: {groq_response[:100]}... ===")
            return {"response": groq_response}
    except Exception as e:
        logger.error(f"Error using Groq API directly: {e}")

    # If Groq API failed, fall back to local LLM
    try:
        logger.info(f"Groq API failed, falling back to local LLM for message: {decoded_message}")
        local_response = local_llm_generate(enhanced_message)
        if local_response:
            logger.info("Successfully got response from local LLM")
            logger.info(f"=== RETURNING LOCAL LLM RESPONSE: {local_response[:100]}... ===")
            return {"response": local_response}
    except Exception as e:
        logger.error(f"Error using local LLM: {e}")

    # If Groq API failed or it's not a commercial question, try Gemini API
    try:
        logger.info(f"Using Gemini API directly for message: {decoded_message}")
        api = GeminiAPI()
        prompt = f"{system_prompt}\n\nUser: {enhanced_message}"
        gemini_response = api.chat(prompt)

        if gemini_response and not "Error" in gemini_response:
            logger.info("Successfully got response from Gemini API")
            logger.info(f"=== RETURNING GEMINI RESPONSE: {gemini_response[:100]}... ===")
            return {"response": gemini_response}
    except Exception as e:
        logger.error(f"Error using Gemini API directly: {e}")

    # If we have a pattern response and all API methods failed, use it as a last resort
    if pattern_response:
        logger.info("Using pattern-based response as fallback after all API methods failed")
        logger.info(f"=== RETURNING PATTERN RESPONSE AS FALLBACK: {pattern_response[:100]}... ===")
        return {"response": pattern_response}

    # If all methods fail, return a friendly error message
    error_msg = "I'm currently experiencing technical difficulties connecting to my knowledge sources. Please try again in a few moments."
    logger.info(f"=== RETURNING FRIENDLY ERROR MESSAGE ===")
    return {"response": error_msg}

def _fallback_to_gemini(message, system_prompt):
    """Fallback to Gemini API if MCP server and local LLM are unavailable."""
    try:
        logger.info(f"Using Gemini API for message: {message}")
        api = GeminiAPI()
        prompt = f"{system_prompt}\n\nUser: {message}"

        # Try to get a response from the API
        response = api.chat(prompt)

        # Check if the response contains an error message
        if "Error with Groq API" in response or "exceeded your current quota" in response or "technical difficulties" in response:
            logger.warning(f"API error detected, using fallback response for: {message}")
            fallback_response = get_fallback_response(message)
            return {"response": fallback_response}

        return {"response": response}
    except Exception as e:
        logger.error(f"Error in _fallback_to_gemini: {e}")
        fallback_response = get_fallback_response(message)
        return {"response": fallback_response}

@chat_bp.route('/api/chat/message', methods=['POST'])
def chat_message():
    """
    Process a chat message and return a response.

    Returns:
        Response: JSON response with the chat result.
    """
    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message:
            return jsonify({
                'success': False,
                'error': 'No message provided'
            })

        # Check and consume credits before processing
        from flask import session
        from ..services.credit_service import credit_service

        user_id = session.get('user_id', 'anonymous')

        # Determine credit cost based on message complexity
        if len(message) > 500 or any(keyword in message.lower() for keyword in ['analyze', 'research', 'detailed', 'comprehensive']):
            task_type = 'autowave_chat_advanced'
        else:
            task_type = 'autowave_chat_basic'

        # Consume credits
        credit_result = credit_service.consume_credits(user_id, task_type)

        if not credit_result['success']:
            return jsonify({
                'success': False,
                'error': credit_result['error'],
                'credits_needed': credit_result.get('credits_needed'),
                'credits_available': credit_result.get('credits_available')
            }), 402

        # Process the chat message
        result = do_chat(message)

        # Get updated credit status after consumption
        updated_credit_status = credit_service.get_user_credits(user_id)

        # Add credit consumption info to response
        result['credits_consumed'] = credit_result['credits_consumed']
        result['remaining_credits'] = updated_credit_status.get('remaining', 50)

        return jsonify({
            'success': True,
            'response': result.get('response', ''),
            'credits_consumed': credit_result['credits_consumed'],
            'remaining_credits': updated_credit_status.get('remaining', 50)
        })
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
