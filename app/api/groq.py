import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GroqAPI:
    """
    A class for interacting with the Groq API.
    """

    def __init__(self, api_key=None):
        """
        Initialize the Groq API client.

        Args:
            api_key (str, optional): The Groq API key. If not provided, it will be loaded from the environment.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-70b-8192"  # Default model

    def generate_text(self, prompt, max_tokens=4096, temperature=0.7, model=None):
        """
        Generate text using the Groq API.

        Args:
            prompt (str): The prompt to generate text from.
            max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 4096.
            temperature (float, optional): The temperature for text generation. Defaults to 0.7.
            model (str, optional): The model to use. If not provided, the default model will be used.

        Returns:
            str: The generated text.

        Raises:
            Exception: If there is an error generating text.
        """
        if not self.api_key:
            raise Exception("Groq API key not found. Please set the GROQ_API_KEY environment variable.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Use the specified model or fall back to the default model
        model_to_use = model if model else self.model

        data = {
            "model": model_to_use,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data), timeout=60)
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"Unexpected response format: {result}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Groq API: {str(e)}")

    def is_available(self):
        """
        Check if the Groq API is available.

        Returns:
            bool: True if the API is available, False otherwise.
        """
        return self.api_key is not None
