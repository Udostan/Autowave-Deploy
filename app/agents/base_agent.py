import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BaseAgent:
    """Base class for all AI agents in the system.

    This class provides common functionality for all agent types.
    Specific agent implementations should inherit from this class.
    """

    def __init__(self, api_key=None):
        """Initialize the agent with an optional API key.

        Args:
            api_key (str, optional): The API key to use. If not provided,
                                     will try to get it from environment variables.
        """
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            print("Warning: No API key provided. Some features may not work.")

    def process(self, data):
        """Process the input data.

        This is a generic method that should be overridden by subclasses.

        Args:
            data: The input data to process

        Returns:
            The processed data
        """
        return data
