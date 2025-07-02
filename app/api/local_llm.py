"""
Local LLM implementation for offline chat functionality.
This module provides a simple pattern-based response system that can be used
when API-based LLMs are unavailable.
"""

import re
import random
import logging
import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('local_llm')

class LocalLLM:
    """A simple pattern-based local LLM implementation for offline chat functionality."""
    
    def __init__(self):
        """Initialize the local LLM with response patterns."""
        self.patterns = [
            # Greetings
            (r'\b(hi|hello|hey|greetings)\b', self._respond_to_greeting),
            
            # Questions about the assistant
            (r'\b(who are you|what are you|tell me about yourself)\b', self._respond_about_self),
            
            # Time-related questions
            (r'\b(what time is it|what is the time|current time)\b', self._respond_with_time),
            (r'\b(what day is it|what is the date|current date)\b', self._respond_with_date),
            
            # Weather questions (simulated)
            (r'\b(weather|temperature|forecast)\b', self._respond_about_weather),
            
            # Simple calculations
            (r'calculate\s+(\d+)\s*([\+\-\*\/])\s*(\d+)', self._respond_to_calculation),
            
            # General knowledge statements
            (r'\b(tell me about|what is|who is|explain)\b', self._respond_to_knowledge_query),
            
            # Help request
            (r'\b(help|assist|support)\b', self._respond_to_help),
            
            # Thank you
            (r'\b(thank you|thanks)\b', self._respond_to_thanks),
            
            # Goodbye
            (r'\b(goodbye|bye|see you|farewell)\b', self._respond_to_goodbye),
        ]
        
        # Fallback responses when no pattern matches
        self.fallback_responses = [
            "I'm not sure I understand. Could you rephrase that?",
            "That's an interesting question. I'm currently in offline mode, so my responses are limited.",
            "I'd like to help with that, but I'm currently operating with limited functionality.",
            "I understand you're asking something, but I'm currently in a simplified mode due to API limitations.",
            "I appreciate your question. While I'm in offline mode, I can still try to assist with basic queries."
        ]
    
    def generate_response(self, message):
        """Generate a response based on the input message using pattern matching.
        
        Args:
            message (str): The user's message
            
        Returns:
            str: The generated response
        """
        # Check each pattern for a match
        for pattern, response_func in self.patterns:
            match = re.search(pattern, message.lower())
            if match:
                return response_func(message, match)
        
        # If no pattern matches, use a fallback response
        return random.choice(self.fallback_responses)
    
    def _respond_to_greeting(self, message, match):
        """Respond to a greeting."""
        greetings = [
            "Hello! How can I assist you today?",
            "Hi there! What can I help you with?",
            "Greetings! How may I be of service?",
            "Hello! I'm your AI assistant. What would you like to know?"
        ]
        return random.choice(greetings)
    
    def _respond_about_self(self, message, match):
        """Respond to questions about the assistant."""
        responses = [
            "I'm an AI assistant designed to help with various tasks. I'm currently running in offline mode.",
            "I'm your virtual assistant, here to help answer questions and provide information, though I'm currently operating with limited functionality.",
            "I'm an AI chatbot created to assist users. Right now, I'm using a local response system while our API connections are being updated."
        ]
        return random.choice(responses)
    
    def _respond_with_time(self, message, match):
        """Respond with the current time."""
        current_time = datetime.datetime.now().strftime("%H:%M")
        return f"The current time is {current_time}."
    
    def _respond_with_date(self, message, match):
        """Respond with the current date."""
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}."
    
    def _respond_about_weather(self, message, match):
        """Respond to weather-related questions with a simulated response."""
        weather_conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "clear", "stormy", "windy", "foggy"]
        temperatures = range(50, 85)
        
        condition = random.choice(weather_conditions)
        temperature = random.choice(temperatures)
        
        return f"I don't have access to real-time weather data in offline mode, but I can provide a simulated response: It's currently {condition} with a temperature of {temperature}°F."
    
    def _respond_to_calculation(self, message, match):
        """Respond to simple calculation requests."""
        try:
            num1 = int(match.group(1))
            operator = match.group(2)
            num2 = int(match.group(3))
            
            result = None
            if operator == '+':
                result = num1 + num2
            elif operator == '-':
                result = num1 - num2
            elif operator == '*':
                result = num1 * num2
            elif operator == '/':
                if num2 == 0:
                    return "I can't divide by zero."
                result = num1 / num2
            
            return f"The result of {num1} {operator} {num2} is {result}."
        except Exception as e:
            return "I had trouble with that calculation. Could you rephrase it?"
    
    def _respond_to_knowledge_query(self, message, match):
        """Respond to general knowledge queries."""
        responses = [
            "That's an interesting topic. While I'm in offline mode, I can't provide detailed information, but I'd be happy to discuss it when our API services are back online.",
            "I'd love to help with that question, but I'm currently operating with limited knowledge access. Please try again later for a more detailed response.",
            "Great question! I'm currently using a local response system, so I can't provide the comprehensive answer this topic deserves."
        ]
        return random.choice(responses)
    
    def _respond_to_help(self, message, match):
        """Respond to requests for help."""
        return "I can help with basic questions and provide simple information while in offline mode. For more complex assistance, please try again later when our API services are available."
    
    def _respond_to_thanks(self, message, match):
        """Respond to expressions of gratitude."""
        responses = [
            "You're welcome! Is there anything else I can help with?",
            "Happy to help! Let me know if you need anything else.",
            "My pleasure! Feel free to ask if you have other questions."
        ]
        return random.choice(responses)
    
    def _respond_to_goodbye(self, message, match):
        """Respond to goodbyes."""
        responses = [
            "Goodbye! Have a great day!",
            "Farewell! Feel free to return if you have more questions.",
            "See you later! I'll be here if you need assistance."
        ]
        return random.choice(responses)

# Create a singleton instance
local_llm = LocalLLM()

def generate_response(message):
    """Generate a response using the local LLM.
    
    Args:
        message (str): The user's message
        
    Returns:
        str: The generated response
    """
    # Add a small delay to simulate processing time
    time.sleep(0.5)
    return local_llm.generate_response(message)
