import os
import requests
import json
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('openrouter_api')

class OpenRouterAPI:
    """
    A class for interacting with the OpenRouter API.
    """
    
    def __init__(self, api_key=None, default_model="deepseek-ai/deepseek-coder-v2"):
        """
        Initialize the OpenRouter API client.
        
        Args:
            api_key (str, optional): The OpenRouter API key. If not provided, it will be loaded from the environment.
            default_model (str, optional): The default model to use. Defaults to "deepseek-ai/deepseek-coder-v2".
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = default_model
        
        if not self.api_key:
            logger.warning("No OpenRouter API key found. OpenRouter fallback will not be available.")
        else:
            logger.info(f"OpenRouter API initialized with default model: {self.default_model}")
    
    def chat(self, messages: List[Dict[str, str]], 
             system_prompt: Optional[str] = None,
             temperature: float = 0.7,
             max_tokens: int = 1024,
             model: Optional[str] = None) -> str:
        """
        Generate a chat response using the OpenRouter API.
        
        Args:
            messages (List[Dict[str, str]]): The chat messages.
            system_prompt (Optional[str]): The system prompt to use. Default is None.
            temperature (float): The temperature for text generation. Default is 0.7.
            max_tokens (int): The maximum number of tokens to generate. Default is 1024.
            model (Optional[str]): The model to use. If not provided, the default model will be used.
            
        Returns:
            str: The generated response.
        """
        if not self.api_key:
            return "OpenRouter API key not configured."
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://autowave.ai",  # Optional for rankings
            "X-Title": "AutoWave Prime Agent"  # Optional for rankings
        }
        
        # Prepare the messages
        formatted_messages = []
        
        # Add system message if provided
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        
        # Add the conversation messages
        for message in messages:
            if isinstance(message, dict) and "role" in message and "content" in message:
                formatted_messages.append(message)
            elif isinstance(message, dict) and "user" in message:
                formatted_messages.append({"role": "user", "content": message["user"]})
            elif isinstance(message, dict) and "assistant" in message:
                formatted_messages.append({"role": "assistant", "content": message["assistant"]})
        
        # If no messages were added, add the last message as user message
        if not formatted_messages and messages:
            if isinstance(messages[-1], str):
                formatted_messages.append({"role": "user", "content": messages[-1]})
        
        data = {
            "model": model or self.default_model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            logger.info(f"Sending request to OpenRouter API with model: {model or self.default_model}")
            response = requests.post(
                self.api_url, 
                headers=headers, 
                data=json.dumps(data),
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                error_message = f"Unexpected response format from OpenRouter: {result}"
                logger.error(error_message)
                return f"Error with OpenRouter API: {error_message}"
                
        except requests.exceptions.RequestException as e:
            error_message = f"Error calling OpenRouter API: {str(e)}"
            logger.error(error_message)
            return error_message
    
    def is_available(self) -> bool:
        """
        Check if the OpenRouter API is available.
        
        Returns:
            bool: True if the API is available, False otherwise.
        """
        return self.api_key is not None
