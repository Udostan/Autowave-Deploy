# Agen911 - Super Agent Web Assistant

Agen911 is a Flask-based web application that uses Google's Gemini API to provide a powerful AI assistant that can browse the web, fill out forms, generate code, and execute Python applications in a web environment.

## Features

### Super Agent Capabilities

The Super Agent can:

1. **Browse the Web**: Navigate to websites and extract content
2. **JavaScript Support**: Render JavaScript-heavy websites using requests-html
3. **Form Submission**: Fill out and submit forms on websites
4. **Link Following**: Navigate through links on webpages
5. **Code Generation**: Generate code snippets in various programming languages
6. **Code Execution**: Execute Python code in a web environment, including GUI applications like Pygame
7. **Caching**: Cache responses to improve performance and reduce API calls
8. **Multiple API Keys**: Use multiple Gemini API keys with automatic rotation
9. **Groq API Fallback**: Use Groq API as a fallback when Gemini API is unavailable

### Specialized Handlers

The Super Agent includes specialized handlers for:

- Financial information and stock prices
- Travel planning and recommendations
- Recipe and food-related queries
- Product reviews and comparisons
- General web searches

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your API keys in the `.env` file:
   - Add your Gemini API key(s)
   - Optionally add a Groq API key for fallback

### Additional Setup for Code Execution

For the code execution functionality, additional dependencies are required:

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install xvfb imagemagick

# Python packages
pip install pygame pyvirtualdisplay xvfbwrapper opencv-python flask-socketio
```

See the [Deployment Guide](deployment_guide.md) for detailed instructions on setting up the application for production.

## Configuration

### API Keys

- `GEMINI_API_KEY`: Your primary Gemini API key
- `GEMINI_API_KEY_BACKUP1`, `GEMINI_API_KEY_BACKUP2`, etc.: Backup Gemini API keys
- `GROQ_API_KEY`: Your Groq API key for fallback (optional)

### Cache Settings

The Super Agent uses caching to improve performance:

- Cache expiry: 1 hour by default
- Cache location: `agen911/cache/` directory

## Usage

1. Start the Flask server: `flask run`
2. Access the web interface at `http://localhost:5000`
3. Enter your query in the input field
4. The Super Agent will process your request and provide a response

## Recent Improvements

1. **JavaScript Support**: Added support for JavaScript-rendered websites using requests-html
2. **Caching System**: Implemented a robust caching system for web requests and API responses
3. **Groq API Integration**: Added Groq API as a fallback when Gemini API is unavailable
4. **Error Handling**: Improved error handling with graceful fallbacks
5. **Performance Optimization**: Optimized web browsing for older systems
6. **Code Execution**: Added ability to execute Python code in a web environment, including GUI applications
7. **Virtual Display**: Implemented headless execution of GUI applications using Xvfb

## License

This project is licensed under the MIT License - see the LICENSE file for details.
