"""
Chat tools for the MCP server.
This module provides tools for chat functionality using various LLM providers.
"""

import os
import json
import logging
import requests
import time
from typing import Dict, List, Any, Optional
import random

# Import OpenRouter API client
from app.api.openrouter import OpenRouterAPI

logger = logging.getLogger(__name__)

class ChatTools:
    """
    Tools for chat functionality using various LLM providers.
    """

    def __init__(self):
        """Initialize the chat tools with API keys from environment variables."""
        self.logger = logging.getLogger(__name__)

        # Load API keys from environment variables
        self.gemini_api_key_1 = os.environ.get("GEMINI_API_KEY", "")  # Primary key
        self.gemini_api_key_2 = os.environ.get("GEMINI_API_KEY_BACKUP1", "")  # Backup key 1
        self.gemini_api_key_3 = os.environ.get("GEMINI_API_KEY_BACKUP2", "")  # Backup key 2
        self.groq_api_key = os.environ.get("GROQ_API_KEY", "")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")

        # Initialize OpenRouter API client
        self.openrouter_api = OpenRouterAPI()
        if self.openrouter_api.is_available():
            self.logger.info("OpenRouter API is available as a fallback")
        else:
            self.logger.warning("OpenRouter API is not available (no API key provided)")

        # Track API key usage and errors
        self.api_key_status = {
            "gemini_1": {"working": True, "last_error": None, "error_count": 0},
            "gemini_2": {"working": True, "last_error": None, "error_count": 0},
            "gemini_3": {"working": True, "last_error": None, "error_count": 0},
            "groq": {"working": True, "last_error": None, "error_count": 0},
            "openai": {"working": True, "last_error": None, "error_count": 0},
            "openrouter": {"working": self.openrouter_api.is_available(), "last_error": None, "error_count": 0}
        }

        # Check if we have at least one API key
        if not any([self.gemini_api_key_1, self.gemini_api_key_2, self.gemini_api_key_3,
                   self.groq_api_key, self.openai_api_key, self.openrouter_api.api_key]):
            self.logger.warning("No API keys found for chat. Using fallback methods.")

    def chat(self, message: str, system_prompt: str = None, history: List[Dict[str, str]] = None) -> str:
        """
        Generate a chat response using available LLM providers.

        Args:
            message: The user's message
            system_prompt: Optional system prompt to guide the model's behavior
            history: Optional chat history for context

        Returns:
            The generated response
        """
        # Default system prompt if none provided
        if not system_prompt:
            system_prompt = "You are a helpful AI assistant. Respond to the following message in a friendly and informative way."

        # Default empty history if none provided
        if history is None:
            history = []

        # Check if this is a commercial/sensitive question that should always use LLM
        commercial_keywords = [
            'business', 'company', 'startup', 'investment', 'finance', 'market',
            'strategy', 'product', 'service', 'customer', 'client', 'revenue',
            'profit', 'sales', 'marketing', 'advertising', 'brand', 'competitor',
            'industry', 'sector', 'economy', 'stock', 'share', 'investor',
            'enterprise', 'commercial', 'corporate', 'organization', 'management'
        ]

        is_commercial_question = any(keyword in message.lower() for keyword in commercial_keywords)

        # For non-commercial questions, we can still check for pattern matches
        # but we'll only use them as a fallback if all API calls fail
        pattern_response = None
        if not is_commercial_question:
            pattern_response = self._check_pattern_match(message)
            # We'll store this for later use as fallback, but won't use it immediately
            if pattern_response:
                self.logger.info("Found pattern match, but will try API providers first")

        # Try different providers in order of preference
        # Prioritize Groq as it's faster and more reliable
        # Add OpenRouter as a fallback option
        providers = [
            self._chat_with_groq,
            self._chat_with_gemini_1,
            self._chat_with_gemini_2,
            self._chat_with_gemini_3,
            self._chat_with_openai,
            self._chat_with_openrouter  # Add OpenRouter as the last fallback
        ]

        # Try each provider until we get a successful response
        for provider in providers:
            if not self._is_provider_working(provider.__name__):
                self.logger.info(f"Skipping {provider.__name__} as it's marked as not working")
                continue

            try:
                response = provider(message, system_prompt, history)
                if response and not self._is_error_response(response):
                    return response
            except Exception as e:
                self.logger.error(f"Error with {provider.__name__}: {str(e)}")
                self._mark_provider_error(provider.__name__, str(e))

        # If all providers fail, use the pattern response if we have one
        if pattern_response:
            self.logger.info("All API providers failed, using pattern-based response as fallback")
            return pattern_response

        # If we don't have a pattern response, use the general fallback
        return self._chat_fallback(message)

    def _check_pattern_match(self, message: str) -> str:
        """
        Check if the message matches any of our predefined patterns for common questions.
        Returns the response if there's a match, None otherwise.
        """
        # Clean and normalize the message
        message_lower = message.lower().strip()
        # Remove punctuation and extra spaces
        import re
        message_clean = re.sub(r'[^\w\s]', '', message_lower)
        message_clean = re.sub(r'\s+', ' ', message_clean).strip()

        # Dictionary of patterns and responses for better organization and easier expansion
        pattern_responses = {
            # Capital cities
            "france": {
                "patterns": ["capital of france", "france capital", "capital city of france",
                            "what is the capital of france", "whats the capital of france",
                            "tell me the capital of france", "frances capital city"],
                "response": "The capital of France is Paris. It's one of the most visited cities in the world and known for landmarks like the Eiffel Tower, the Louvre Museum, and Notre-Dame Cathedral."
            },
            "germany": {
                "patterns": ["capital of germany", "germany capital", "capital city of germany",
                            "what is the capital of germany", "whats the capital of germany",
                            "tell me the capital of germany", "germanys capital city"],
                "response": "The capital of Germany is Berlin. It's the largest city in Germany and has a rich history, known for landmarks like the Brandenburg Gate and the Berlin Wall."
            },
            "italy": {
                "patterns": ["capital of italy", "italy capital", "capital city of italy",
                            "what is the capital of italy", "whats the capital of italy",
                            "tell me the capital of italy", "italys capital city"],
                "response": "The capital of Italy is Rome. Often called the 'Eternal City', Rome is known for its ancient ruins like the Colosseum and Roman Forum, as well as Vatican City."
            },
            "japan": {
                "patterns": ["capital of japan", "japan capital", "capital city of japan",
                            "what is the capital of japan", "whats the capital of japan",
                            "tell me the capital of japan", "japans capital city"],
                "response": "The capital of Japan is Tokyo. It's one of the world's most populous metropolitan areas and a blend of traditional and ultramodern culture."
            },
            "usa": {
                "patterns": ["capital of usa", "usa capital", "capital city of usa",
                            "what is the capital of usa", "whats the capital of usa",
                            "capital of united states", "united states capital",
                            "capital of america", "american capital", "us capital",
                            "capital of us", "capital of the united states",
                            "capital of the us", "capital of the usa"],
                "response": "The capital of the United States is Washington, D.C. (District of Columbia). It's home to iconic landmarks like the White House, the Capitol Building, and the Lincoln Memorial."
            },
            "uk": {
                "patterns": ["capital of uk", "uk capital", "capital city of uk",
                            "what is the capital of uk", "whats the capital of uk",
                            "capital of united kingdom", "united kingdom capital",
                            "capital of england", "england capital", "british capital",
                            "capital of britain", "capital of great britain"],
                "response": "The capital of the United Kingdom is London. It's a global city known for its history, culture, and landmarks like Big Ben, the Tower of London, and Buckingham Palace."
            },

            # Geography questions
            "longest_river": {
                "patterns": ["longest river", "longest river in the world", "what is the longest river",
                            "whats the longest river", "which river is the longest",
                            "which is the longest river", "tell me the longest river"],
                "response": "The Nile River in Africa is generally considered the longest river in the world, with a length of about 6,650 kilometers (4,130 miles). The Amazon River in South America is the second longest but has the largest drainage basin and carries the greatest volume of water."
            },
            "largest_desert": {
                "patterns": ["largest desert", "largest desert in the world", "what is the largest desert",
                            "whats the largest desert", "which desert is the largest",
                            "which is the largest desert", "tell me the largest desert",
                            "biggest desert", "biggest desert in the world"],
                "response": "The largest desert in the world is the Antarctic Desert, covering the continent of Antarctica with 14 million square kilometers. If considering only hot deserts, the Sahara Desert in North Africa is the largest, covering about 9.2 million square kilometers across several countries."
            },
            "tallest_mountain": {
                "patterns": ["tallest mountain", "tallest mountain in the world", "what is the tallest mountain",
                            "whats the tallest mountain", "which mountain is the tallest",
                            "which is the tallest mountain", "tell me the tallest mountain",
                            "highest mountain", "highest mountain in the world", "highest peak"],
                "response": "Mount Everest is the tallest mountain above sea level, with a height of 8,848.86 meters (29,031.7 feet). It's located in the Mahalangur Himal sub-range of the Himalayas on the border between Nepal and Tibet."
            },

            # History questions
            "computer_history": {
                "patterns": ["history of computers", "computer history", "tell me about the history of computers",
                            "how did computers evolve", "evolution of computers", "when were computers invented",
                            "first computer", "history of computing", "computer timeline"],
                "response": "The history of computers spans centuries, from mechanical calculating devices to modern digital computers. Key milestones include:\n\n1. Early mechanical calculators (1600s-1800s): Pascal's calculator, Leibniz's Stepped Reckoner, and Babbage's Difference Engine\n2. First programmable computer: Charles Babbage's Analytical Engine (1830s), with Ada Lovelace writing the first algorithm\n3. Early electronic computers (1940s): ENIAC, EDVAC, and the Manchester Baby\n4. Transistor-based computers (1950s-1960s): IBM mainframes and minicomputers\n5. Personal computers (1970s-1980s): Apple II, IBM PC, and Macintosh\n6. Internet era (1990s-2000s): World Wide Web, laptops, and mobile computing\n7. Modern era (2010s-present): Cloud computing, AI, quantum computing, and ubiquitous mobile devices\n\nThis evolution represents a shift from room-sized machines accessible to few to powerful devices that fit in our pockets and are used by billions worldwide."
            },
            "quantum_computing": {
                "patterns": ["quantum computing", "what is quantum computing", "explain quantum computing",
                            "how does quantum computing work", "quantum computers", "quantum computation",
                            "quantum computer explanation", "quantum computing simple terms",
                            "quantum computing explained", "explain quantum computing in simple terms"],
                "response": "Quantum computing in simple terms:\n\nTraditional computers use bits (0s and 1s) to process information. Quantum computers use quantum bits or 'qubits' that can exist in multiple states simultaneously thanks to two quantum properties:\n\n1. Superposition: Qubits can be in both 0 and 1 states at the same time\n2. Entanglement: Qubits can be connected so that the state of one instantly affects others\n\nThese properties allow quantum computers to process vast amounts of possibilities simultaneously, making them potentially much faster than classical computers for certain problems like:\n\n- Breaking encryption\n- Simulating molecules for drug discovery\n- Optimizing complex systems like traffic flow\n- Solving certain mathematical problems\n\nQuantum computers aren't better for all tasks, but they could revolutionize fields requiring massive computational power. They're still in early development, with researchers working to increase qubit counts and reduce error rates."
            },

            # Programming languages
            "python_vs_javascript": {
                "patterns": ["python vs javascript", "difference between python and javascript",
                            "compare python and javascript", "python and javascript differences",
                            "how does python compare to javascript", "javascript vs python",
                            "main differences between python and javascript",
                            "what are the differences between python and javascript",
                            "python javascript comparison"],
                "response": "Here are the main differences between Python and JavaScript:\n\n1. **Purpose and Environment**:\n   - Python: General-purpose language used for backend development, data science, AI, automation, and scientific computing\n   - JavaScript: Originally designed for web browsers, now also used for server-side development (Node.js), mobile apps, and desktop applications\n\n2. **Syntax**:\n   - Python: Uses indentation for code blocks, emphasizes readability with clean syntax\n   - JavaScript: Uses curly braces for code blocks, semicolons to end statements\n\n3. **Typing**:\n   - Python: Dynamically typed but strongly typed (types are enforced)\n   - JavaScript: Dynamically typed and loosely typed (allows implicit type conversion)\n\n4. **Concurrency**:\n   - Python: Uses the Global Interpreter Lock (GIL), which can limit true parallelism\n   - JavaScript: Event-driven, non-blocking I/O model with asynchronous programming via Promises and async/await\n\n5. **Libraries and Frameworks**:\n   - Python: Rich ecosystem for data science (NumPy, Pandas), web (Django, Flask), and AI (TensorFlow, PyTorch)\n   - JavaScript: Dominant in frontend frameworks (React, Angular, Vue) and has Node.js for backend\n\n6. **Object-Oriented Programming**:\n   - Python: Class-based OOP with inheritance\n   - JavaScript: Prototype-based OOP, though ES6 added class syntax\n\n7. **Learning Curve**:\n   - Python: Generally considered easier for beginners due to readable syntax\n   - JavaScript: More complex with asynchronous concepts and browser quirks\n\nBoth languages are extremely popular and versatile, with Python excelling in data-heavy applications and JavaScript dominating web development."
            },

            # Machine Learning
            "learn_machine_learning": {
                "patterns": ["learn machine learning", "how to learn machine learning",
                            "best way to learn machine learning", "machine learning learning path",
                            "start with machine learning", "begin machine learning",
                            "machine learning for beginners", "machine learning resources",
                            "how to get started with machine learning", "machine learning roadmap"],
                "response": "# The Best Way to Learn Machine Learning\n\nLearning machine learning effectively requires a structured approach combining theory, practice, and project work. Here's a comprehensive roadmap:\n\n## 1. Build a Strong Foundation\n\n- **Mathematics**: Focus on linear algebra, calculus, probability, and statistics\n- **Programming**: Learn Python and key libraries (NumPy, Pandas)\n- **Data Analysis**: Practice data cleaning, visualization, and exploratory analysis\n\n## 2. Structured Learning Resources\n\n- **Online Courses**:\n  - Andrew Ng's Machine Learning course on Coursera\n  - Fast.ai's Practical Deep Learning for Coders\n  - Stanford's CS229 Machine Learning (available on YouTube)\n  - DeepLearning.AI specializations\n\n- **Books**:\n  - \"Hands-On Machine Learning with Scikit-Learn and TensorFlow\" by Aurélien Géron\n  - \"Deep Learning\" by Ian Goodfellow, Yoshua Bengio, and Aaron Courville\n  - \"Pattern Recognition and Machine Learning\" by Christopher Bishop\n\n## 3. Practical Implementation\n\n- Master key libraries: scikit-learn, TensorFlow, PyTorch, Keras\n- Implement algorithms from scratch to understand their mechanics\n- Work through tutorials with provided datasets (MNIST, CIFAR-10, etc.)\n\n## 4. Project-Based Learning\n\n- Start with simple projects and gradually increase complexity\n- Participate in Kaggle competitions\n- Contribute to open-source ML projects\n- Build a portfolio of diverse projects\n\n## 5. Specialization\n\nOnce comfortable with the basics, specialize in areas like:\n- Computer Vision\n- Natural Language Processing\n- Reinforcement Learning\n- Time Series Analysis\n- Recommendation Systems\n\n## 6. Stay Updated\n\n- Follow research papers on arXiv\n- Join ML communities (Reddit r/MachineLearning, Discord servers)\n- Attend conferences or watch recordings (NeurIPS, ICML, CVPR)\n- Follow ML practitioners on social media\n\n## 7. Practical Tips\n\n- **Be patient**: ML has a steep learning curve\n- **Start small**: Build simple models before complex ones\n- **Learn by doing**: Theory alone isn't enough\n- **Collaborate**: Join ML communities and study groups\n- **Teach others**: Explaining concepts solidifies your understanding\n\nRemember that consistency is key. Regular practice and hands-on projects will help you progress much faster than passive learning."
            },

            # Geography
            "capital_of_france": {
                "patterns": ["capital of france", "what is the capital of france",
                            "france capital", "paris france", "capital city of france"],
                "response": "The capital of France is Paris. It's one of the most visited cities in the world and known for landmarks such as the Eiffel Tower, the Louvre Museum, Notre-Dame Cathedral, and the Arc de Triomphe. Paris is also renowned for its cuisine, fashion, art, and culture."
            },

            # Specific question about tallest building
            "tallest_building": {
                "patterns": ["tallest building in the world", "what is the tallest building",
                            "world's tallest building", "tallest skyscraper",
                            "height of burj khalifa", "tallest structure"],
                "response": "The tallest building in the world is the Burj Khalifa in Dubai, United Arab Emirates. It stands at a height of 828 meters (2,717 feet) and has 163 floors. It was completed in 2010 and has held the record for the world's tallest building since then. The building was designed by the architectural firm Skidmore, Owings & Merrill and is part of the Downtown Dubai development."
            },

            # City populations
            "tokyo_population": {
                "patterns": ["population of tokyo", "how many people live in tokyo",
                            "tokyo population", "what is the population of tokyo",
                            "how populated is tokyo", "tokyo residents"],
                "response": "Tokyo is the most populous city in Japan and one of the most populous urban areas in the world. The Tokyo metropolitan area, which includes the Tokyo Metropolis and surrounding prefectures, has a population of approximately 37 million people, making it the world's largest metropolitan area by population. The 23 special wards of Tokyo proper have a population of around 9.3 million. These numbers may vary slightly depending on the most recent census data."
            }
        }

        # Check for matches in our pattern dictionary
        for category, data in pattern_responses.items():
            for pattern in data["patterns"]:
                # Use fuzzy matching to allow for slight variations
                if pattern in message_clean or message_clean in pattern:
                    return data["response"]

                # Check for word similarity (if most words match)
                pattern_words = set(pattern.split())
                message_words = set(message_clean.split())
                common_words = pattern_words.intersection(message_words)

                # If more than 70% of the words match, consider it a match
                if len(common_words) >= 0.7 * len(pattern_words) and len(pattern_words) > 2:
                    return data["response"]

        # No match found
        return None

    def _is_provider_working(self, provider_name: str) -> bool:
        """Check if a provider is marked as working."""
        provider_key = provider_name.replace("_chat_with_", "")

        # Special case for Groq - we know we have a Groq API key
        if provider_key == "groq" and self.groq_api_key:
            return True

        return self.api_key_status.get(provider_key, {}).get("working", False)

    def _mark_provider_error(self, provider_name: str, error: str) -> None:
        """Mark a provider as having an error."""
        provider_key = provider_name.replace("_chat_with_", "")
        if provider_key in self.api_key_status:
            self.api_key_status[provider_key]["last_error"] = error
            self.api_key_status[provider_key]["error_count"] += 1

            # If we've had multiple errors, mark the provider as not working
            if self.api_key_status[provider_key]["error_count"] >= 3:
                self.api_key_status[provider_key]["working"] = False
                self.logger.warning(f"Marked {provider_key} as not working after multiple errors")

    def _is_error_response(self, response: str) -> bool:
        """Check if a response contains an error message."""
        error_phrases = [
            "exceeded your current quota",
            "API key not valid",
            "Error with",
            "API rate limit exceeded",
            "Invalid API key",
            "technical difficulties",
            "API request failed",
            "Gemini API key"
        ]

        # Special case for "not configured" - only an error for non-Groq responses
        if "not configured" in response and "Groq API key not configured" not in response:
            return True

        return any(phrase in response for phrase in error_phrases)

    def _chat_with_gemini_1(self, message: str, system_prompt: str, history: List[Dict[str, str]]) -> str:
        """Generate a chat response using Gemini API with the first API key."""
        if not self.gemini_api_key_1:
            return "Gemini API key 1 not configured."

        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
            headers = {
                "Content-Type": "application/json"
            }

            # Construct the prompt with system prompt and message
            prompt = f"{system_prompt}\n\nUser: {message}"

            # Add history if available
            if history:
                prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history]) + f"\n\nUser: {message}"

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }

            response = requests.post(
                f"{url}?key={self.gemini_api_key_1}",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    return "No response generated from Gemini API."
            else:
                error_message = f"Error with Gemini API 1: {response.status_code} - {response.text}"
                self.logger.error(error_message)
                return error_message

        except Exception as e:
            error_message = f"Error with Gemini API 1: {str(e)}"
            self.logger.error(error_message)
            return error_message

    def _chat_with_gemini_2(self, message: str, system_prompt: str, history: List[Dict[str, str]]) -> str:
        """Generate a chat response using Gemini API with the second API key."""
        if not self.gemini_api_key_2:
            return "Gemini API key 2 not configured."

        # Implementation is the same as _chat_with_gemini_1 but with the second API key
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
            headers = {
                "Content-Type": "application/json"
            }

            # Construct the prompt with system prompt and message
            prompt = f"{system_prompt}\n\nUser: {message}"

            # Add history if available
            if history:
                prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history]) + f"\n\nUser: {message}"

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }

            response = requests.post(
                f"{url}?key={self.gemini_api_key_2}",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    return "No response generated from Gemini API."
            else:
                error_message = f"Error with Gemini API 2: {response.status_code} - {response.text}"
                self.logger.error(error_message)
                return error_message

        except Exception as e:
            error_message = f"Error with Gemini API 2: {str(e)}"
            self.logger.error(error_message)
            return error_message

    def _chat_with_gemini_3(self, message: str, system_prompt: str, history: List[Dict[str, str]]) -> str:
        """Generate a chat response using Gemini API with the third API key."""
        if not self.gemini_api_key_3:
            return "Gemini API key 3 not configured."

        # Implementation is the same as _chat_with_gemini_1 but with the third API key
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
            headers = {
                "Content-Type": "application/json"
            }

            # Construct the prompt with system prompt and message
            prompt = f"{system_prompt}\n\nUser: {message}"

            # Add history if available
            if history:
                prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history]) + f"\n\nUser: {message}"

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }

            response = requests.post(
                f"{url}?key={self.gemini_api_key_3}",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    return "No response generated from Gemini API."
            else:
                error_message = f"Error with Gemini API 3: {response.status_code} - {response.text}"
                self.logger.error(error_message)
                return error_message

        except Exception as e:
            error_message = f"Error with Gemini API 3: {str(e)}"
            self.logger.error(error_message)
            return error_message

    def _chat_with_groq(self, message: str, system_prompt: str, history: List[Dict[str, str]]) -> str:
        """Generate a chat response using Groq API."""
        if not self.groq_api_key:
            self.logger.warning("Groq API key not configured. Skipping Groq API.")
            # Mark Groq as not working to avoid future attempts
            self.api_key_status["groq"]["working"] = False
            self.api_key_status["groq"]["last_error"] = "API key not configured"
            self.api_key_status["groq"]["error_count"] = 3  # Ensure it's marked as not working
            return "Groq API key not configured."

        # Log that we're using Groq API
        self.logger.info(f"Using Groq API with key: {self.groq_api_key[:5]}...{self.groq_api_key[-5:] if len(self.groq_api_key) > 10 else ''}")

        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }

            # Prepare messages in the OpenAI format
            messages = []

            # Add system message
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Add conversation history
            for entry in history:
                if "user" in entry:
                    messages.append({"role": "user", "content": entry["user"]})
                if "assistant" in entry:
                    messages.append({"role": "assistant", "content": entry["assistant"]})

            # Add the current message
            messages.append({"role": "user", "content": message})

            payload = {
                "model": "llama3-70b-8192",  # Using Llama 3 70B model for better quality
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }

            response = requests.post(
                url,
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "No response generated from Groq API."
            else:
                error_message = f"Error with Groq API: {response.status_code} - {response.text}"
                self.logger.error(error_message)

                # If we get an authentication error, mark Groq as not working
                if response.status_code == 401:
                    self.logger.warning("Invalid Groq API key. Marking Groq as not working.")
                    self.api_key_status["groq"]["working"] = False
                    self.api_key_status["groq"]["last_error"] = error_message
                    self.api_key_status["groq"]["error_count"] = 3  # Ensure it's marked as not working

                return error_message

        except Exception as e:
            error_message = f"Error with Groq API: {str(e)}"
            self.logger.error(error_message)
            return error_message

    def _chat_with_openai(self, message: str, system_prompt: str, history: List[Dict[str, str]]) -> str:
        """Generate a chat response using OpenAI API."""
        if not self.openai_api_key:
            return "OpenAI API key not configured."

        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }

            # Prepare messages in the OpenAI format
            messages = []

            # Add system message
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Add history
            if history:
                for msg in history:
                    messages.append({"role": msg["role"], "content": msg["content"]})

            # Add the current message
            messages.append({"role": "user", "content": message})

            payload = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }

            response = requests.post(
                url,
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and data["choices"]:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "No response generated from OpenAI API."
            else:
                error_message = f"Error with OpenAI API: {response.status_code} - {response.text}"
                self.logger.error(error_message)
                return error_message

        except Exception as e:
            error_message = f"Error with OpenAI API: {str(e)}"
            self.logger.error(error_message)
            return error_message

    def _chat_with_openrouter(self, message: str, system_prompt: str, history: List[Dict[str, str]]) -> str:
        """Generate a chat response using OpenRouter API."""
        if not self.openrouter_api.is_available():
            self.logger.warning("OpenRouter API not configured. Skipping OpenRouter API.")
            # Mark OpenRouter as not working to avoid future attempts
            self.api_key_status["openrouter"]["working"] = False
            self.api_key_status["openrouter"]["last_error"] = "API key not configured"
            self.api_key_status["openrouter"]["error_count"] = 3  # Ensure it's marked as not working
            return "OpenRouter API key not configured."

        # Log that we're using OpenRouter API
        self.logger.info(f"Using OpenRouter API with DeepSeek model")

        try:
            # Prepare messages in the OpenRouter format
            formatted_messages = []

            # Add system message
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})

            # Add history
            if history:
                for msg in history:
                    if "role" in msg and "content" in msg:
                        formatted_messages.append({"role": msg["role"], "content": msg["content"]})
                    elif "user" in msg:
                        formatted_messages.append({"role": "user", "content": msg["user"]})
                    elif "assistant" in msg:
                        formatted_messages.append({"role": "assistant", "content": msg["assistant"]})

            # Add the current message
            formatted_messages.append({"role": "user", "content": message})

            # Call the OpenRouter API
            response = self.openrouter_api.chat(
                messages=formatted_messages,
                temperature=0.7,
                max_tokens=1024
            )

            # Check if the response contains an error message
            if "Error with OpenRouter API" in response:
                self.logger.error(response)
                self._mark_provider_error("_chat_with_openrouter", response)
                return response
            else:
                return response

        except Exception as e:
            error_message = f"Error with OpenRouter API: {str(e)}"
            self.logger.error(error_message)
            self._mark_provider_error("_chat_with_openrouter", str(e))
            return error_message

    def _chat_fallback(self, message: str) -> str:
        """
        Generate a fallback response when all API providers fail.
        Uses a pattern-based approach to provide contextually relevant responses.

        Args:
            message: The user's message

        Returns:
            A fallback response
        """
        # First check if we have a pattern match for common factual questions
        pattern_response = self._check_pattern_match(message)
        if pattern_response:
            return pattern_response

        # Try to use the local LLM if available
        try:
            from app.api.local_llm import generate_response as local_llm_generate
            return local_llm_generate(message)
        except Exception as e:
            self.logger.error(f"Error using local LLM in fallback: {e}")
            # Continue with pattern-based fallback if local LLM fails

        # Define patterns and responses for conversational queries
        patterns = [
            # Greetings
            (r'\b(hi|hello|hey|greetings)\b', [
                "Hello! I'm currently operating in fallback mode due to API limitations, but I'm still here to chat.",
                "Hi there! While my full capabilities are limited right now, I'm happy to engage in basic conversation.",
                "Greetings! I'm running on a simplified system at the moment, but I'll do my best to assist you."
            ]),

            # Questions about the assistant
            (r'\b(who are you|what are you|tell me about yourself)\b', [
                "I'm an AI assistant designed to help with various tasks. I'm currently running in fallback mode due to API limitations.",
                "I'm your virtual assistant, though I'm currently operating with limited functionality due to API constraints.",
                "I'm an AI chatbot created to assist users. Right now, I'm using a local response system while our API connections are being updated."
            ]),

            # Time-related questions
            (r'\b(what time is it|what is the time|current time)\b', [
                f"The current time is {time.strftime('%H:%M')}. Note that I'm currently operating in fallback mode.",
                f"It's {time.strftime('%H:%M')} right now. I'm running with limited capabilities at the moment.",
                f"The time is {time.strftime('%H:%M')}. I should mention I'm in fallback mode with reduced functionality."
            ]),

            # Date-related questions
            (r'\b(what day is it|what is the date|current date)\b', [
                f"Today is {time.strftime('%A, %B %d, %Y')}. I'm currently in fallback mode with limited capabilities.",
                f"It's {time.strftime('%A, %B %d, %Y')}. Note that I'm operating with reduced functionality right now.",
                f"The date is {time.strftime('%B %d, %Y')}. I'm currently using a local response system due to API limitations."
            ]),

            # Weather questions
            (r'\b(weather|temperature|forecast)\b', [
                "I'd like to provide weather information, but I'm currently operating in fallback mode and can't access real-time weather data.",
                "While I normally could check the weather for you, I'm currently running with limited capabilities and can't access that information.",
                "I'm sorry, but I can't access weather data right now as I'm operating in fallback mode due to API limitations."
            ]),

            # Capital questions (general, not specific ones which are handled by _check_pattern_match)
            (r'\b(capital of|what is the capital)\b', [
                "I can answer some basic capital city questions. For example, Paris is the capital of France, Berlin is the capital of Germany, and Washington, D.C. is the capital of the United States.",
                "While I'm in fallback mode, I can still provide some basic geography information. Many capital cities are well-known, like Tokyo (Japan), Rome (Italy), and London (UK).",
                "Even in fallback mode, I can answer some geography questions. Capital cities are important centers of government and culture around the world."
            ]),

            # General knowledge questions
            (r'\b(what is|who is|where is|when is|why is|how does|explain)\b', [
                "That's an interesting question. While I'm in fallback mode, I can't provide the detailed answer this deserves. Please try again when our API services are back online.",
                "I'd love to answer that question properly, but I'm currently operating with limited knowledge access. Please try again later for a more comprehensive response.",
                "Great question! I'm currently using a local response system, so I can't provide the detailed information you're looking for. Please check back when our API services are restored."
            ]),

            # Thank you
            (r'\b(thank you|thanks)\b', [
                "You're welcome! I'm happy to help, even with my limited capabilities at the moment.",
                "My pleasure! While I'm in fallback mode right now, I'm still glad to be of assistance.",
                "You're welcome! I'm operating with reduced functionality, but I'm still here to help as best I can."
            ]),

            # Goodbye
            (r'\b(goodbye|bye|see you|farewell)\b', [
                "Goodbye! Feel free to return when our API services are fully restored for better assistance.",
                "Farewell! I hope to be back at full capacity soon to better assist you next time.",
                "See you later! Hopefully, I'll be operating with full capabilities when you return."
            ])
        ]

        import re

        # Check each pattern for a match
        for pattern, responses in patterns:
            if re.search(pattern, message.lower()):
                return random.choice(responses)

        # Default fallback responses if no pattern matches
        default_responses = [
            "I understand you're trying to communicate with me, but I'm currently operating in fallback mode due to API limitations. I can only provide basic responses right now.",
            "While I'd like to give you a more helpful response, I'm currently running with reduced capabilities. Please try again when our API services are restored.",
            "I appreciate your message. I'm currently using a local response system due to API constraints, which limits my ability to provide detailed answers.",
            "I'm currently in offline mode with limited functionality. For more comprehensive assistance, please try again when our API services are back online.",
            "Thanks for your message. I'm operating in fallback mode right now, which means I can only provide simple responses. Please check back later when full services are restored."
        ]

        return random.choice(default_responses)
