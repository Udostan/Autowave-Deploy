"""
Test script to run the Flask application.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Load environment variables
load_dotenv()

from app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)
