import google.generativeai as genai
import os
import time
import logging
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gemini_api')

# List available models to debug
def list_available_models():
    try:
        models = genai.list_models()
        return [model.name for model in models]
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return []

class GeminiKeyManager:
    """Manages multiple Gemini API keys with rotation and error handling."""
    def __init__(self):
        # Get primary API key
        primary_key = os.environ.get('GEMINI_API_KEY')
        if not primary_key:
            raise ValueError("Primary Gemini API key is required")

        # Get backup API keys
        backup_key1 = os.environ.get('GEMINI_API_KEY_BACKUP1')
        backup_key2 = os.environ.get('GEMINI_API_KEY_BACKUP2')

        # Create list of available keys (filter out None values)
        self.api_keys = [k for k in [primary_key, backup_key1, backup_key2] if k]

        logger.info(f"Initialized with {len(self.api_keys)} API keys")

        self.current_key_index = 0
        self.usage_counts = {key: 0 for key in self.api_keys}
        self.error_counts = {key: 0 for key in self.api_keys}
        self.quota_exceeded = {key: False for key in self.api_keys}
        self.last_rotation_time = time.time()

    def get_current_key(self):
        """Get the currently active API key."""
        return self.api_keys[self.current_key_index]

    def rotate_key(self, reason="manual"):
        """Rotate to the next available API key."""
        old_key = self.get_current_key()
        old_index = self.current_key_index

        # Find the next non-quota-exceeded key
        for _ in range(len(self.api_keys)):
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            if not self.quota_exceeded[self.get_current_key()]:
                break

        new_key = self.get_current_key()
        self.last_rotation_time = time.time()

        # Log the rotation
        if old_key != new_key:
            logger.info(f"Rotated API key from index {old_index} to {self.current_key_index} due to {reason}")

        return new_key

    def mark_usage(self, key):
        """Mark a successful usage of the given key."""
        if key in self.api_keys:
            self.usage_counts[key] += 1

    def mark_error(self, key, error):
        """Mark an error for the given key and determine if it's a quota error."""
        if key in self.api_keys:
            self.error_counts[key] += 1

            # Check if this is a quota exceeded error
            error_str = str(error).lower()
            if "quota" in error_str or "rate limit" in error_str or "429" in error_str:
                logger.warning(f"Quota exceeded for API key {key[:5]}...")
                self.quota_exceeded[key] = True
                return self.rotate_key(reason="quota_exceeded")

        return key

    def reset_quota_status(self, key=None):
        """Reset the quota exceeded status for a key or all keys."""
        if key is None:
            # Reset all keys
            for k in self.api_keys:
                self.quota_exceeded[k] = False
        elif key in self.api_keys:
            self.quota_exceeded[key] = False

class GeminiAPI:
    def __init__(self, api_key=None, model_name="gemini-1.5-pro"):
        """Initialize the Gemini API client with multiple API keys and Groq fallback."""
        # Store the model name
        self.model_name = model_name

        # If a specific API key is provided, use only that one
        if api_key:
            self.single_key_mode = True
            self.api_key = api_key
            genai.configure(api_key=self.api_key)
            self.key_manager = None
        else:
            # Otherwise use the key manager with multiple keys
            self.single_key_mode = False
            self.key_manager = GeminiKeyManager()
            self.api_key = self.key_manager.get_current_key()
            genai.configure(api_key=self.api_key)

        # Initialize Groq API for fallback
        self.groq_api = GroqAPI()
        # Check if Groq fallback is explicitly disabled
        disable_groq = os.environ.get("DISABLE_GROQ_FALLBACK", "false").lower() == "true"
        self.use_groq_fallback = bool(self.groq_api.api_key) and not disable_groq
        if self.use_groq_fallback:
            logger.info("Groq API fallback is enabled")
        elif disable_groq:
            logger.info("Groq API fallback is explicitly disabled via environment variable")
        else:
            logger.info("Groq API fallback is disabled (no API key)")

        # Log available models for debugging
        available_models = list_available_models()
        logger.info(f"Available models: {available_models}")

        # Try to use a model that's available

        try:
            # First try to use the specified model_name
            model_with_prefix = f'models/{self.model_name}'
            if model_with_prefix in available_models or self.model_name in available_models:
                # Use the model name without the 'models/' prefix
                clean_model_name = self.model_name.replace('models/', '')
                self.model = genai.GenerativeModel(clean_model_name)
                logger.info(f"Using specified model: {clean_model_name}")
            # If specified model is not available, try to find the best available model
            elif 'models/gemini-1.5-pro' in available_models:
                self.model = genai.GenerativeModel('gemini-1.5-pro')
                logger.info("Using gemini-1.5-pro model")
            elif 'models/gemini-1.5-flash' in available_models:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Using gemini-1.5-flash model")
            elif 'models/gemini-pro' in available_models:
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("Using gemini-pro model")
            elif any('gemini' in model_name for model_name in available_models):
                # Find any gemini model
                for model_name in available_models:
                    if 'gemini' in model_name and not model_name.endswith('vision'):
                        model_name_clean = model_name.replace('models/', '')
                        self.model = genai.GenerativeModel(model_name_clean)
                        logger.info(f"Using {model_name_clean} model")
                        break
            else:
                # No suitable model found
                raise Exception("No suitable Gemini model found")
        except Exception as e:
            logger.error(f"Error initializing Gemini model: {e}")
            # Check if Groq fallback is available
            if self.use_groq_fallback:
                logger.info("Will use Groq API as fallback for Gemini")
                self.model = None
            else:
                # Fallback to a simple mock implementation if Groq is not available
                self.model = None
                logger.warning("No model available, using mock implementation")

    def generate_text(self, prompt, temperature=0.7, max_tokens=4096, max_retries=3):
        """Generate text response using Gemini API with automatic key rotation on quota errors."""
        if self.model is None:
            # Try Groq API if available
            if self.use_groq_fallback:
                logger.info("Using Groq API as fallback for generate_text")
                return self.groq_api.generate_text(prompt, max_tokens=max_tokens, temperature=temperature)
            else:
                return "The Gemini API is currently unavailable. This is a mock response for demonstration purposes."

        # If in single key mode, just make a single attempt
        if self.single_key_mode:
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    }
                )
                return response.text
            except Exception as e:
                logger.error(f"Error generating text: {e}")
                # Try Groq API if available
                if self.use_groq_fallback:
                    logger.info("Using Groq API as fallback after Gemini error")
                    return self.groq_api.generate_text(prompt, max_tokens=max_tokens, temperature=temperature)
                return f"An error occurred: {str(e)}"

    def generate_text_stream(self, prompt, temperature=0.7, max_tokens=4096):
        """Generate streaming text response using Gemini API."""
        if self.model is None:
            # If model is not available, yield a mock response
            yield "The Gemini API is currently unavailable. This is a mock response for demonstration purposes."
            return

        # If in single key mode, just make a single attempt
        if self.single_key_mode:
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    },
                    stream=True  # Enable streaming
                )

                # Stream the response chunks
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
                    elif hasattr(chunk, 'parts') and chunk.parts:
                        for part in chunk.parts:
                            if hasattr(part, 'text') and part.text:
                                yield part.text
            except Exception as e:
                logger.error(f"Error generating streaming text: {e}")
                yield f"An error occurred: {str(e)}"
            return

        # With key manager, try multiple keys if needed
        retries = 0
        max_retries = 3
        last_error = None

        while retries < max_retries:
            current_key = self.key_manager.get_current_key()
            try:
                # Configure with the current key
                genai.configure(api_key=current_key)

                # Create a new model instance with the current key
                available_models = list_available_models()
                logger.info(f"Available models for key {current_key[:5]}...: {available_models}")

                # First try to use the specified model_name
                model_with_prefix = f'models/{self.model_name}'
                if model_with_prefix in available_models or self.model_name in available_models:
                    # Use the model name without the 'models/' prefix
                    clean_model_name = self.model_name.replace('models/', '')
                    model = genai.GenerativeModel(clean_model_name)
                    logger.info(f"Using specified model: {clean_model_name}")
                # If specified model is not available, try to find the best available model
                elif 'models/gemini-1.5-pro' in available_models:
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    logger.info("Using gemini-1.5-pro model")
                elif 'models/gemini-1.5-flash' in available_models:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    logger.info("Using gemini-1.5-flash model")
                elif 'models/gemini-pro' in available_models:
                    model = genai.GenerativeModel('gemini-pro')
                    logger.info("Using gemini-pro model")
                elif any('gemini' in model_name for model_name in available_models):
                    # Find any gemini model
                    for model_name in available_models:
                        if 'gemini' in model_name and not model_name.endswith('vision'):
                            model_name_clean = model_name.replace('models/', '')
                            model = genai.GenerativeModel(model_name_clean)
                            logger.info(f"Using {model_name_clean} model")
                            break
                else:
                    # No suitable model found
                    raise Exception(f"No suitable Gemini model found for key {current_key[:5]}...")

                # Generate the streaming response
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    },
                    stream=True  # Enable streaming
                )

                # Mark successful usage
                self.key_manager.mark_usage(current_key)

                # Stream the response chunks
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
                    elif hasattr(chunk, 'parts') and chunk.parts:
                        for part in chunk.parts:
                            if hasattr(part, 'text') and part.text:
                                yield part.text

                # If we get here, streaming completed successfully
                return

            except Exception as e:
                last_error = e
                logger.warning(f"Error with key {current_key[:5]}... during streaming: {e}")

                # Handle the error and potentially rotate keys
                self.key_manager.mark_error(current_key, e)

                # If all keys have quota exceeded, break early
                if all(self.key_manager.quota_exceeded.values()):
                    logger.error("All API keys have exceeded their quota")
                    break

                retries += 1

        # If we get here, all retries failed
        logger.error(f"All API keys failed after {retries} retries for streaming. Last error: {last_error}")

        # Try Groq API if available (note: Groq doesn't support streaming, so we'll return the full response)
        if self.use_groq_fallback:
            logger.info("Using Groq API as fallback after all Gemini keys failed for streaming")
            groq_response = self.groq_api.generate_text(prompt, max_tokens=max_tokens, temperature=temperature)
            # Return the Groq response as a single chunk
            yield groq_response
            return

        # If all else fails, yield an error message
        yield f"An error occurred: {str(last_error)}"

    def chat(self, messages, temperature=0.7, max_retries=3):
        """Generate a chat response using Gemini API with automatic key rotation on quota errors."""
        if self.model is None:
            # Try Groq API if available
            if self.use_groq_fallback:
                logger.info("Using Groq API as fallback for chat")
                return self.groq_api.chat(messages, temperature=temperature)
            else:
                return "The Gemini API is currently unavailable. This is a mock response for demonstration purposes."

        # If in single key mode, just make a single attempt
        if self.single_key_mode:
            try:
                chat = self.model.start_chat(history=[])
                response = chat.send_message(
                    messages,
                    generation_config={"temperature": temperature}
                )
                return response.text
            except Exception as e:
                logger.error(f"Error in chat: {e}")
                # Try Groq API if available
                if self.use_groq_fallback:
                    logger.info("Using Groq API as fallback after Gemini chat error")
                    return self.groq_api.chat(messages, temperature=temperature)
                return f"An error occurred: {str(e)}"

        # With key manager, try multiple keys if needed
        retries = 0
        last_error = None

        while retries < max_retries:
            current_key = self.key_manager.get_current_key()
            try:
                # Configure with the current key
                genai.configure(api_key=current_key)

                # Create a new model instance with the current key
                available_models = list_available_models()
                logger.info(f"Available models for key {current_key[:5]}...: {available_models}")

                # First try to use the specified model_name
                model_with_prefix = f'models/{self.model_name}'
                if model_with_prefix in available_models or self.model_name in available_models:
                    # Use the model name without the 'models/' prefix
                    clean_model_name = self.model_name.replace('models/', '')
                    model = genai.GenerativeModel(clean_model_name)
                    logger.info(f"Using specified model: {clean_model_name}")
                # If specified model is not available, try to find the best available model
                elif 'models/gemini-1.5-pro' in available_models:
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    logger.info("Using gemini-1.5-pro model")
                elif 'models/gemini-1.5-flash' in available_models:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    logger.info("Using gemini-1.5-flash model")
                elif 'models/gemini-pro' in available_models:
                    model = genai.GenerativeModel('gemini-pro')
                    logger.info("Using gemini-pro model")
                elif any('gemini' in model_name for model_name in available_models):
                    # Find any gemini model
                    for model_name in available_models:
                        if 'gemini' in model_name and not model_name.endswith('vision'):
                            model_name_clean = model_name.replace('models/', '')
                            model = genai.GenerativeModel(model_name_clean)
                            logger.info(f"Using {model_name_clean} model")
                            break
                else:
                    # No suitable model found
                    raise Exception(f"No suitable Gemini model found for key {current_key[:5]}...")

                # Start a chat and send the message
                chat = model.start_chat(history=[])
                response = chat.send_message(
                    messages,
                    generation_config={"temperature": temperature}
                )

                # Mark successful usage
                self.key_manager.mark_usage(current_key)
                return response.text

            except Exception as e:
                last_error = e
                logger.warning(f"Error with key {current_key[:5]}...: {e}")

                # Handle the error and potentially rotate keys
                self.key_manager.mark_error(current_key, e)

                # If all keys have quota exceeded, break early
                if all(self.key_manager.quota_exceeded.values()):
                    logger.error("All API keys have exceeded their quota")
                    break

                retries += 1

        # If we get here, all retries failed
        logger.error(f"All API keys failed after {retries} retries. Last error: {last_error}")

        # Try Groq API if available
        if self.use_groq_fallback:
            logger.info("Using Groq API as fallback after all Gemini keys failed for chat")
            return self.groq_api.chat(messages, temperature=temperature)

        return f"An error occurred: {str(last_error)}"

    def analyze_image_with_text(self, image_path, prompt, temperature=0.7, max_tokens=4096):
        """Analyze an image with text prompt using Gemini Vision API."""
        if not image_path or not os.path.exists(image_path):
            return "Image file not found or invalid path provided."

        try:
            import PIL.Image

            # Load the image
            image = PIL.Image.open(image_path)

            # If model is not available, try Groq fallback (though Groq doesn't support vision)
            if self.model is None:
                if self.use_groq_fallback:
                    logger.info("Groq API doesn't support vision, using text-only analysis")
                    return self.groq_api.generate_text(f"Analyze this image (image analysis not available): {prompt}")
                else:
                    return "Vision analysis is currently unavailable. Please try again later."

            # If in single key mode, just make a single attempt
            if self.single_key_mode:
                try:
                    response = self.model.generate_content(
                        [prompt, image],
                        generation_config={
                            "temperature": temperature,
                            "max_output_tokens": max_tokens,
                        }
                    )
                    return response.text
                except Exception as e:
                    logger.error(f"Error analyzing image: {e}")
                    if self.use_groq_fallback:
                        logger.info("Using Groq API as fallback (text-only)")
                        return self.groq_api.generate_text(f"Image analysis not available: {prompt}")
                    return f"An error occurred during image analysis: {str(e)}"

            # With key manager, try multiple keys if needed
            retries = 0
            max_retries = 3
            last_error = None

            while retries < max_retries:
                current_key = self.key_manager.get_current_key()
                try:
                    # Configure with the current key
                    genai.configure(api_key=current_key)

                    # Create a new model instance with the current key
                    available_models = list_available_models()

                    # Try to find a vision-capable model
                    vision_model = None
                    if 'models/gemini-1.5-pro' in available_models:
                        vision_model = genai.GenerativeModel('gemini-1.5-pro')
                        logger.info("Using gemini-1.5-pro for vision analysis")
                    elif 'models/gemini-1.5-flash' in available_models:
                        vision_model = genai.GenerativeModel('gemini-1.5-flash')
                        logger.info("Using gemini-1.5-flash for vision analysis")
                    elif 'models/gemini-pro-vision' in available_models:
                        vision_model = genai.GenerativeModel('gemini-pro-vision')
                        logger.info("Using gemini-pro-vision for vision analysis")
                    else:
                        # Try any available gemini model
                        for model_name in available_models:
                            if 'gemini' in model_name:
                                model_name_clean = model_name.replace('models/', '')
                                vision_model = genai.GenerativeModel(model_name_clean)
                                logger.info(f"Using {model_name_clean} for vision analysis")
                                break

                    if vision_model is None:
                        raise Exception(f"No suitable vision model found for key {current_key[:5]}...")

                    # Generate the response with image
                    response = vision_model.generate_content(
                        [prompt, image],
                        generation_config={
                            "temperature": temperature,
                            "max_output_tokens": max_tokens,
                        }
                    )

                    # Mark successful usage
                    self.key_manager.mark_usage(current_key)
                    return response.text

                except Exception as e:
                    last_error = e
                    logger.warning(f"Error with key {current_key[:5]}... during vision analysis: {e}")

                    # Handle the error and potentially rotate keys
                    self.key_manager.mark_error(current_key, e)

                    # If all keys have quota exceeded, break early
                    if all(self.key_manager.quota_exceeded.values()):
                        logger.error("All API keys have exceeded their quota")
                        break

                    retries += 1

            # If we get here, all retries failed
            logger.error(f"All API keys failed after {retries} retries for vision analysis. Last error: {last_error}")

            # Try Groq API if available (though it doesn't support vision)
            if self.use_groq_fallback:
                logger.info("Using Groq API as fallback after all Gemini keys failed (text-only)")
                return self.groq_api.generate_text(f"Image analysis not available: {prompt}")

            return f"An error occurred during image analysis: {str(last_error)}"

        except Exception as e:
            logger.error(f"Error loading or processing image: {e}")
            return f"Error processing image: {str(e)}"


class GroqAPI:
    """Class for interacting with the Groq API."""

    def __init__(self, api_key=None):
        """Initialize the Groq API client."""
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "llama3-70b-8192"  # Default model

        if not self.api_key:
            logger.warning("No Groq API key provided. Groq fallback will not be available.")

    def generate_text(self, prompt, max_tokens=1024, temperature=0.7):
        """Generate text using the Groq API."""
        if not self.api_key:
            return "Groq API key not configured. Please add GROQ_API_KEY to your .env file."

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Ensure prompt is a string
            if not isinstance(prompt, str):
                if hasattr(prompt, 'get'):
                    # If it's a dict-like object, try to extract content
                    prompt = prompt.get('content', str(prompt))
                else:
                    # Convert to string
                    prompt = str(prompt)

            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            # Extract the generated text
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "No response generated"

        except Exception as e:
            logger.error(f"Error with Groq API: {e}")
            return "I'm sorry, but I'm currently experiencing technical difficulties. Please try again later."

    def chat(self, messages, max_tokens=1024, temperature=0.7):
        """Generate a chat response using the Groq API."""
        if not self.api_key:
            return "Groq API key not configured. Please add GROQ_API_KEY to your .env file."

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Convert messages to the format expected by Groq
            formatted_messages = []

            # If messages is a string, convert it to a single message
            if isinstance(messages, str):
                formatted_messages = [{"role": "user", "content": messages}]
            else:
                # Process list of messages
                for message in messages:
                    if isinstance(message, str):
                        formatted_messages.append({"role": "user", "content": message})
                    else:
                        role = message.get("role", "user")
                        content = message.get("parts", message.get("content", ""))

                        if isinstance(content, list):
                            # Join multiple parts into a single string
                            content = " ".join([str(part) for part in content])

                        formatted_messages.append({"role": role, "content": content})

            data = {
                "model": self.model,
                "messages": formatted_messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            # Extract the generated text
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "No response generated"

        except Exception as e:
            logger.error(f"Error with Groq API chat: {e}")
            return "I'm sorry, but I'm currently experiencing technical difficulties. Please try again later."


def gemini_request(query):
    """Legacy function for backward compatibility."""
    try:
        api = GeminiAPI()  # This will now use multiple API keys
        result = api.generate_text(query)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error in legacy gemini_request: {e}")

        # Try Groq as a fallback
        try:
            groq_api = GroqAPI()
            if groq_api.api_key:  # Only try if API key is configured
                logger.info("Trying Groq API as fallback")
                result = groq_api.generate_text(query)
                return {"result": result}
        except Exception as groq_error:
            logger.error(f"Error with Groq fallback: {groq_error}")

        return {"result": f"Error: {str(e)}"}
