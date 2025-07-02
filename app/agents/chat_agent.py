from .base_agent import BaseAgent
from app.api.chat import do_chat

class ChatAgent(BaseAgent):
    """Agent specialized for chat functionality.

    This agent handles chat messages and returns conversational responses.
    """

    def perform_chat(self, message):
        """Process a chat message and generate a response.

        Args:
            message (str): The user's chat message

        Returns:
            dict: A dictionary containing the chat response
        """
        if not message or not isinstance(message, str):
            return {"response": "Invalid message"}

        # Process the message and get a response
        return do_chat(message)
