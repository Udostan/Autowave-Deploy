"""
Agentic Code API - Smart Code Assistant with Conversational AI
Provides Augment-like capabilities for iterative code generation and modification
"""

from flask import Blueprint, request, jsonify
import json
import time
import re
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv
from app.services.file_processor import file_processor
from app.decorators.paywall import require_credits, trial_limit, require_subscription
from app.services.activity_logger import log_agentic_code_activity

# Load environment variables
load_dotenv()

# Create blueprint
agentic_code_bp = Blueprint('agentic_code', __name__)

# Import LLM clients
try:
    import google.generativeai as genai

    # Configure Gemini
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)

    # Configure Groq (with error handling)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    groq_client = None
    if GROQ_API_KEY:
        try:
            from groq import Groq
            groq_client = Groq(api_key=GROQ_API_KEY)
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {e}")
            groq_client = None

except ImportError as e:
    print(f"Warning: Could not import LLM libraries: {e}")
    genai = None
    groq_client = None

# Session storage (in production, use Redis or database)
sessions = {}

class AgenticCodeAssistant:
    """
    AI Code Assistant with Augment-like capabilities
    """

    def __init__(self):
        self.model_name = "gemini-1.5-flash"
        self.groq_model = "llama-3.1-70b-versatile"

    def analyze_request(self, message: str, current_code: str = "", files: list = None) -> Dict[str, Any]:
        """
        Analyze user request and determine the approach (like Augment's planning phase)
        """
        try:
            # Process uploaded files if any
            processed_message = message
            if files:
                processed_message = self._process_uploaded_files(message, files)

            # Use Gemini for analysis
            if genai and GEMINI_API_KEY:
                return self._analyze_with_gemini(processed_message, current_code)
            elif groq_client:
                return self._analyze_with_groq(processed_message, current_code)
            else:
                return self._fallback_analysis(processed_message, current_code)
        except Exception as e:
            print(f"Error in analysis: {e}")
            return self._fallback_analysis(message, current_code)

    def _process_uploaded_files(self, message: str, files: list) -> str:
        """Process uploaded files and enhance the message with file content"""
        if not files:
            return message

        enhanced_message = message + "\n\n--- UPLOADED FILES ---\n"

        for file_data in files:
            file_name = file_data.get('name', 'unknown')
            file_type = file_data.get('type', '')
            content = file_data.get('content', '')
            content_type = file_data.get('contentType', '')

            enhanced_message += f"\n📁 File: {file_name}\n"

            if content_type == 'image':
                # For images, describe what we can see
                enhanced_message += f"Type: Image ({file_type})\n"
                enhanced_message += "Content: [Image file uploaded - please analyze the image and use it as reference for the code generation]\n"
                if content:
                    enhanced_message += f"Image data: {content[:100]}...\n"
            elif content_type == 'text' and content:
                # For text files, include the content
                enhanced_message += f"Type: Text file ({file_type})\n"
                enhanced_message += f"Content:\n```\n{content}\n```\n"
            else:
                enhanced_message += f"Type: {file_type}\n"
                enhanced_message += "Content: [File uploaded for reference]\n"

        enhanced_message += "\n--- END OF FILES ---\n\n"
        enhanced_message += "Please analyze the uploaded files and use them as reference or input for generating the requested code. "
        enhanced_message += "If images are provided, describe what you see and incorporate relevant elements into the design. "
        enhanced_message += "If code files are provided, use them as a starting point or reference for the new code."

        return enhanced_message

    def _analyze_with_gemini(self, message: str, current_code: str) -> Dict[str, Any]:
        """Analyze request using Gemini with enhanced language support"""
        model = genai.GenerativeModel(self.model_name)

        if not current_code.strip():
            # Detect language from user request
            detected_language = self._detect_language_from_request(message)

            # Initial code generation using enhanced approach
            system_prompt = self._get_enhanced_system_prompt(detected_language)

            if detected_language == "python":
                full_prompt = f"{system_prompt}\n\nCreate the following Python application or script: {message}"
            else:
                full_prompt = f"{system_prompt}\n\nCreate the following web component or application: {message}"

            response = model.generate_content(full_prompt)
            code = response.text.strip()

            # Extract code from response if needed
            if f"```{detected_language}" in code:
                code = code.split(f"```{detected_language}")[1].split("```")[0].strip()
            elif "```html" in code:
                code = code.split("```html")[1].split("```")[0].strip()
            elif "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()

            if detected_language == "python":
                return {
                    "plan": f"Generate professional Python application for: {message}",
                    "steps": [
                        "Analyzing your request and determining project type",
                        "Designing application structure and logic",
                        "Implementing with Python best practices",
                        "Adding error handling and user interaction features"
                    ],
                    "code": code,
                    "explanation": f"I've created a professional Python application based on your request: '{message}'. The code follows Python best practices with proper error handling and functionality.",
                    "language": "python"
                }
            else:
                return {
                    "plan": f"Generate professional webpage for: {message}",
                    "steps": [
                        "Analyzing your request and determining content type",
                        "Designing layout with modern UI patterns",
                        "Implementing with HTML, Tailwind CSS, and JavaScript",
                        "Adding interactive features and optimizations"
                    ],
                    "code": code,
                    "explanation": f"I've created a professional webpage based on your request: '{message}'. The code uses modern HTML, Tailwind CSS, and JavaScript with responsive design and rich visual elements.",
                    "language": "html"
                }
        else:
            # Code modification
            prompt = f"""
You are an expert AI coding assistant similar to Augment. Analyze this user request and provide a structured response.

Current Code:
```
{current_code}
```

User Request: {message}

Provide a JSON response with:
1. "plan" - Brief description of what you'll do
2. "steps" - Array of 3-4 implementation steps
3. "code" - The complete updated code
4. "explanation" - Friendly explanation of changes made
5. "language" - Detected programming language

Focus on:
- Clear, step-by-step approach
- Professional code quality
- Helpful explanations
- Iterative improvements

Return only valid JSON.
"""

            response = model.generate_content(prompt)
            return self._parse_llm_response(response.text)

    def _detect_language_from_request(self, message: str) -> str:
        """Detect programming language from user request"""
        message_lower = message.lower()

        # Python keywords and indicators - prioritize Flask and web frameworks
        python_indicators = [
            'flask', 'django', 'fastapi', 'python web', 'python app', 'web application',
            'api', 'backend', 'server', 'python', 'py', 'script', 'data analysis',
            'machine learning', 'ml', 'ai', 'pandas', 'numpy', 'matplotlib',
            'automation', 'scraping', 'tkinter', 'gui', 'desktop app',
            'algorithm', 'data processing', 'csv', 'json', 'api client',
            'command line', 'cli', 'terminal', 'file processing', 'contact form',
            'form submission', 'json file', 'save submissions'
        ]

        # Web development indicators (default)
        web_indicators = [
            'website', 'webpage', 'web app', 'landing page', 'portfolio',
            'dashboard', 'blog', 'ecommerce', 'shop', 'store', 'html',
            'css', 'javascript', 'js', 'frontend', 'ui', 'ux', 'responsive',
            'bootstrap', 'tailwind', 'react', 'vue', 'angular'
        ]

        # Count matches for each language
        python_score = sum(1 for indicator in python_indicators if indicator in message_lower)
        web_score = sum(1 for indicator in web_indicators if indicator in message_lower)

        # If Python indicators are stronger, return Python
        if python_score > web_score and python_score > 0:
            return "python"

        # Default to HTML/web development
        return "html"

    def _analyze_with_groq(self, message: str, current_code: str) -> Dict[str, Any]:
        """Analyze request using Groq with enhanced language support"""
        if not current_code.strip():
            # Detect language from user request
            detected_language = self._detect_language_from_request(message)

            # Initial code generation using enhanced approach
            system_prompt = self._get_enhanced_system_prompt(detected_language)

            if detected_language == "python":
                full_prompt = f"{system_prompt}\n\nCreate the following Python application or script: {message}"
            else:
                full_prompt = f"{system_prompt}\n\nCreate the following web component or application: {message}"

            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": full_prompt}],
                model=self.groq_model,
                temperature=0.2,
                max_tokens=4000
            )

            code = response.choices[0].message.content.strip()

            # Extract code from response if needed
            if f"```{detected_language}" in code:
                code = code.split(f"```{detected_language}")[1].split("```")[0].strip()
            elif "```html" in code:
                code = code.split("```html")[1].split("```")[0].strip()
            elif "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()

            if detected_language == "python":
                return {
                    "plan": f"Generate professional Python application for: {message}",
                    "steps": [
                        "Analyzing your request and determining project type",
                        "Designing application structure and logic",
                        "Implementing with Python best practices",
                        "Adding error handling and user interaction features"
                    ],
                    "code": code,
                    "explanation": f"I've created a professional Python application based on your request: '{message}'. The code follows Python best practices with proper error handling and functionality.",
                    "language": "python"
                }
            else:
                return {
                    "plan": f"Generate professional webpage for: {message}",
                    "steps": [
                        "Analyzing your request and determining content type",
                        "Designing layout with modern UI patterns",
                        "Implementing with HTML, Tailwind CSS, and JavaScript",
                        "Adding interactive features and optimizations"
                    ],
                    "code": code,
                    "explanation": f"I've created a professional webpage based on your request: '{message}'. The code uses modern HTML, Tailwind CSS, and JavaScript with responsive design and rich visual elements.",
                    "language": "html"
                }
        else:
            # Code modification
            prompt = f"""
You are an expert AI coding assistant similar to Augment. Analyze this user request and provide a structured response.

Current Code:
```
{current_code}
```

User Request: {message}

Provide a JSON response with:
1. "plan" - Brief description of what you'll do
2. "steps" - Array of 3-4 implementation steps
3. "code" - The complete updated code
4. "explanation" - Friendly explanation of changes made
5. "language" - Detected programming language

Focus on:
- Clear, step-by-step approach
- Professional code quality
- Helpful explanations
- Iterative improvements

Return only valid JSON.
"""

            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.groq_model,
                temperature=0.7,
                max_tokens=4000
            )

            return self._parse_llm_response(response.choices[0].message.content)

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response and extract JSON"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # If no JSON found, create structured response
                return self._create_structured_response(response_text)
        except json.JSONDecodeError:
            return self._create_structured_response(response_text)

    def _create_structured_response(self, text: str) -> Dict[str, Any]:
        """Create structured response from unstructured text"""
        return {
            "plan": "Process user request and generate appropriate code",
            "steps": [
                "Analyzing requirements",
                "Generating code structure",
                "Implementing functionality",
                "Optimizing and finalizing"
            ],
            "code": self._generate_fallback_code(text),
            "explanation": f"I've processed your request: {text[:100]}...",
            "language": "html"
        }

    def _fallback_analysis(self, message: str, current_code: str) -> Dict[str, Any]:
        """Fallback analysis when no LLM is available"""
        if not current_code.strip():
            # Detect language from user request
            detected_language = self._detect_language_from_request(message)

            # Initial code generation using enhanced style
            code = self._generate_initial_code_enhanced_style(message, detected_language)

            if detected_language == "python":
                explanation = f"I've created a Python application based on your request: '{message}'"
                return {
                    "plan": f"Generate professional Python application for: {message}",
                    "steps": [
                        "Analyzing your request and determining project type",
                        "Designing application structure and logic",
                        "Implementing with Python best practices",
                        "Adding error handling and user interaction features"
                    ],
                    "code": code,
                    "explanation": explanation,
                    "language": "python"
                }
            else:
                explanation = f"I've created a webpage based on your request: '{message}'"
                return {
                    "plan": f"Generate professional webpage for: {message}",
                    "steps": [
                        "Analyzing your request and determining content type",
                        "Designing layout with modern UI patterns",
                        "Implementing with HTML, Tailwind CSS, and JavaScript",
                        "Adding interactive features and optimizations"
                    ],
                    "code": code,
                    "explanation": explanation,
                    "language": "html"
                }
        else:
            # Code modification
            code = self._modify_existing_code(message, current_code)
            explanation = f"I've modified the existing code based on your request: '{message}'"

            return {
                "plan": f"Modify code for: {message}",
                "steps": [
                    "Analyzing your request",
                    "Planning the implementation",
                    "Writing the code",
                    "Finalizing and optimizing"
                ],
                "code": code,
                "explanation": explanation,
                "language": self._detect_language(code)
            }

    def _generate_initial_code_codewave_style(self, message: str) -> str:
        """Generate initial code using Code Wave's LLM approach"""
        try:
            # Import the Gemini API from Code Wave
            from app.api.gemini import GeminiAPI
            gemini_api = GeminiAPI()

            # Use Code Wave's comprehensive system prompt
            system_prompt = self._get_codewave_system_prompt()

            # Generate code using the same approach as Code Wave
            full_prompt = f"{system_prompt}\n\nCreate the following web component or application: {message}"
            response = gemini_api.generate_text(
                prompt=full_prompt,
                temperature=0.2
            )

            if response:
                # Extract code from response
                code = response.strip()

                # If the response contains markdown code blocks, extract the code
                if "```html" in code:
                    code = code.split("```html")[1].split("```")[0].strip()
                elif "```" in code:
                    code = code.split("```")[1].split("```")[0].strip()

                return code
            else:
                # Fallback to template if LLM fails
                return self._generate_initial_code_template(message)

        except Exception as e:
            print(f"Error generating code with LLM: {e}")
            # Fallback to template if LLM fails
            return self._generate_initial_code_template(message)

    def _generate_initial_code_enhanced_style(self, message: str, language: str) -> str:
        """Generate initial code using enhanced approach with language support"""
        try:
            # Try to use LLM first
            from app.api.gemini import GeminiAPI
            gemini_api = GeminiAPI()

            # Use enhanced system prompt
            system_prompt = self._get_enhanced_system_prompt(language)

            # Generate code using the enhanced approach
            if language == "python":
                full_prompt = f"{system_prompt}\n\nCreate the following Python application or script: {message}"
            else:
                full_prompt = f"{system_prompt}\n\nCreate the following web component or application: {message}"

            response = gemini_api.generate_text(
                prompt=full_prompt,
                temperature=0.2
            )

            if response:
                # Extract code from response
                code = response.strip()

                # If the response contains markdown code blocks, extract the code
                if f"```{language}" in code:
                    code = code.split(f"```{language}")[1].split("```")[0].strip()
                elif "```html" in code:
                    code = code.split("```html")[1].split("```")[0].strip()
                elif "```python" in code:
                    code = code.split("```python")[1].split("```")[0].strip()
                elif "```" in code:
                    code = code.split("```")[1].split("```")[0].strip()

                return code
            else:
                # Fallback to template if LLM fails
                return self._generate_initial_code_template(message)

        except Exception as e:
            print(f"Error generating code with enhanced LLM: {e}")
            # Fallback to template if LLM fails
            return self._generate_initial_code_template(message)

    def _get_enhanced_system_prompt(self, language: str = "html") -> str:
        """Get the enhanced system prompt for multiple languages"""
        if language.lower() == "python":
            return self._get_python_system_prompt()
        else:
            return self._get_web_system_prompt()

    def _get_python_system_prompt(self) -> str:
        """Get the comprehensive system prompt for Python development"""
        return """
        You are an expert Python developer specializing in clean, functional, and well-documented Python code.
        Your task is to generate professional Python applications, scripts, and tools based on the user's request.

        Guidelines:
        1. Use modern Python best practices and PEP 8 standards
        2. Write clean, readable, and well-commented code
        3. Include proper error handling and input validation
        4. Use type hints where appropriate
        5. Create modular, reusable functions and classes
        6. Include docstrings for all functions and classes
        7. Use appropriate Python libraries and frameworks
        8. Ensure code is complete, error-free, and ready to run
        9. Include example usage and test cases when appropriate
        10. Follow security best practices

        PYTHON PROJECT TYPES:
        1. SCRIPTS: Data processing, automation, utilities, file operations
        2. WEB APPS: Flask/Django applications, APIs, web scrapers
        3. DATA ANALYSIS: Pandas, NumPy, Matplotlib, data visualization
        4. MACHINE LEARNING: Scikit-learn, TensorFlow, PyTorch models
        5. GUI APPLICATIONS: Tkinter, PyQt, desktop applications
        6. GAMES: Pygame, simple games and interactive applications
        7. AUTOMATION: Selenium, web automation, task scheduling
        8. APIS: FastAPI, Flask REST APIs, microservices

        STRUCTURE GUIDELINES:
        1. Always include proper imports at the top
        2. Define constants and configuration variables
        3. Create helper functions for reusable logic
        4. Use main() function for script entry point
        5. Include if __name__ == "__main__": guard
        6. Add comprehensive error handling
        7. Include logging where appropriate
        8. Use virtual environments and requirements.txt for dependencies

        FUNCTIONALITY REQUIREMENTS:
        1. Make applications fully functional and interactive
        2. Include proper user input handling and validation
        3. Implement complete business logic
        4. Add file I/O operations when needed
        5. Include data persistence (files, databases) when appropriate
        6. Add configuration options and command-line arguments
        7. Implement proper testing and debugging features

        FLASK APPLICATION REQUIREMENTS (CRITICAL):
        1. For Flask web applications, ALWAYS use port 5002 to avoid conflicts
        2. Use app.run(debug=True, port=5002, host="127.0.0.1") for Flask apps
        3. Never use port 5000 or 5001 as they may be in use
        4. Include proper error handling for port conflicts
        5. Set FLASK_DEBUG=True instead of deprecated FLASK_ENV

        Your response should ONLY include the complete Python code without any explanations or markdown formatting.
        Just provide the raw Python file that is ready to run.
        """

    def _get_web_system_prompt(self) -> str:
        """Get the comprehensive system prompt for web development"""
        return """
        You are an expert web developer specializing in HTML, CSS (with Tailwind CSS), and JavaScript.
        Your task is to generate clean, well-structured, and FULLY FUNCTIONAL code based on the user's request.

        Guidelines:
        1. Use modern best practices and standards
        2. Prioritize responsive design using Tailwind CSS classes directly in HTML elements (not @apply directives)
        3. Write clean, well-commented code
        4. Include all necessary HTML, CSS, and JavaScript in a single file
        5. Make sure the code is complete, error-free, and ready to run
        6. Use semantic HTML elements
        7. Ensure the code is accessible
        8. Optimize for performance
        9. Include the Tailwind CSS CDN in the head section: <script src="https://cdn.tailwindcss.com"></script>
        10. Use regular CSS for custom styles, not @apply directives
        11. Double-check your JavaScript code for syntax errors and missing brackets

        CRITICAL FUNCTIONALITY REQUIREMENTS - MUST BE FULLY WORKING:
        1. ALL INTERACTIVE ELEMENTS MUST BE FULLY FUNCTIONAL - NO EXCEPTIONS
        2. Buttons must have proper click event handlers that actually do something
        3. Forms must have complete validation and submission handling with feedback
        4. Navigation links must work correctly and scroll/navigate properly
        5. Modals and popups must open/close properly with proper event handling
        6. Tabs must switch content correctly with proper state management
        7. Search functionality must actually search and filter data in real-time
        8. Calculators must perform real calculations with proper math operations
        9. Games must be playable with complete game logic and state management
        10. APIs must be called and data displayed correctly with error handling
        11. Local storage must be used for data persistence when needed
        12. Error handling must be implemented for all user interactions
        13. CRUD operations must be fully implemented (Create, Read, Update, Delete)
        14. Data must persist between page reloads using localStorage
        15. All user inputs must be validated with proper error messages
        16. Loading states must be shown during operations
        17. Success/error notifications must be displayed to users
        18. All features mentioned in the user request must actually work

        JAVASCRIPT IMPLEMENTATION REQUIREMENTS:
        1. Use modern ES6+ JavaScript syntax
        2. Implement proper event listeners for all interactive elements
        3. Add input validation and error handling
        4. Use async/await for API calls
        5. Implement proper state management
        6. Add loading states and user feedback
        7. Include proper error messages and success notifications
        8. Use localStorage or sessionStorage for data persistence
        9. Implement proper form handling and validation
        10. Add keyboard navigation support
        11. Include proper accessibility features
        12. Test all functionality before finalizing code

        CONTENT TYPE DETECTION (VERY IMPORTANT):
        1. ANALYZE THE USER'S PROMPT CAREFULLY to determine what type of content they want:
           - WEBSITE: Landing pages, portfolios, company sites, blogs, e-commerce
           - APPLICATION: Weather apps, calculators, tools, dashboards, games
           - DIAGRAM: Flowcharts, mind maps, org charts, process diagrams, network diagrams
           - PRESENTATION: Slides, pitch decks, visual presentations, infographics
           - VISUALIZATION: Data charts, graphs, interactive visualizations
        2. For each content type, use the appropriate libraries and techniques as described below

        DESIGN GUIDELINES (VERY IMPORTANT):
        1. NAVIGATION AND STRUCTURE:
           - For WEBSITES: ALWAYS separate navigation bar from header section (nav should be its own distinct element)
           - Navigation should be <nav> element, header should be <header> element with hero content
           - Use proper semantic structure: <nav>, <header>, <main>, <section>, <footer>
           - For APPLICATIONS: Use appropriate UI patterns like sidebars, tab bars, or minimal navigation
           - For DIAGRAMS & PRESENTATIONS: Include minimal navigation with clear controls for interaction

        2. SECTION SPACING AND LAYOUT:
           - Create proper section spacing with adequate margins/padding (use py-16 or py-20 for main sections)
           - Ensure sections are well-separated visually with proper spacing (min py-8 between elements)
           - Use proper container classes (max-w-7xl mx-auto px-4) for content width
           - Add mb-8 or mb-12 for element spacing within sections

        3. FOOTER REQUIREMENTS:
           - ALWAYS include a consistent, appropriately-sized footer (max height 200px)
           - Use py-8 or py-12 for footer padding (never more than py-16)
           - Footer should be compact but informative (links, contact, copyright)
           - Footer should have dark background with light text for contrast

        4. TAB FUNCTIONALITY:
           - For multi-tab websites: create functional tabs that show/hide different content sections
           - Use JavaScript to implement proper tab switching functionality
           - Each tab should reveal different content areas, not just styling changes
           - Add active states and smooth transitions between tabs

        5. COLOR PALETTE AND BACKGROUNDS:
           - ALWAYS use a dark theme by default for applications (dark backgrounds with light text)
           - Use a cohesive color palette throughout the design (4-6 complementary colors)
           - Every section should have a rich background color, gradient, or pattern
           - Avoid plain white backgrounds - use subtle gradients or dark themes instead
           - Create visually appealing designs with rich colors and gradients that work well together
           - For gradients, use at least 3 colors from the same palette to create depth

        6. VISUAL ELEMENTS (CRITICAL FOR RICH APPEARANCE):
           - Add depth with layered elements, shadows, and 3D effects
           - Use glass morphism effects (frosted glass) for cards and containers
           - Incorporate subtle animations for hover states and transitions
           - Add micro-interactions (e.g., button hover effects, loading animations)
           - Use rounded corners (at least 0.5rem) for containers and buttons
           - Include icons from Font Awesome or Material Icons for visual enhancement
           - Add subtle patterns or textures to backgrounds when appropriate
           - Use border highlights with glowing effects for active elements
           - Implement card-based designs with elevation shadows
           - Make sure text has sufficient contrast with background colors
           - Use proper spacing between elements (min 1rem) for better readability

        7. APPLICATION STRUCTURE GUIDELINES (CRITICAL FOR RICH APPLICATIONS):
           - Create a proper layout with header, main content area, and footer
           - Use a sidebar or navigation panel for applications with multiple sections
           - Implement proper state management using JavaScript objects or Alpine.js
           - Add loading states and transitions between application states
           - Include proper error handling and user feedback mechanisms
           - Use card-based layouts for content organization
           - Implement responsive designs that work on mobile and desktop
           - Add subtle animations for user interactions (button clicks, form submissions)
           - Include proper form validation with visual feedback
           - Use modals/dialogs for confirmations and additional information

        8. SPECIALIZED CONTENT GUIDELINES:
           - For DIAGRAMS: Use libraries like Mermaid.js, D3.js, or Chart.js to create interactive diagrams
           - For PRESENTATIONS: Create slide-like sections with navigation controls and transitions
           - For VISUALIZATIONS: Use appropriate chart types and interactive elements

        COLOR PALETTE SUGGESTIONS (USE THESE FOR RICH DESIGNS):
        - Dark Mode UI: #121212 (background), #1e1e1e (surface), #bb86fc (primary), #03dac6 (secondary), #cf6679 (error)
        - Cyberpunk: #000000 (background), #ff2a6d (primary), #05d9e8 (secondary), #d1f7ff (text), #7700a6 (accent)
        - Gradient Dark: #0f0c29 (start), #302b63 (middle), #24243e (end), #f8f8f8 (text), #ff7b00 (accent)
        - Neon Glow: #10002b (background), #240046 (surface), #3c096c (container), #5a189a (primary), #7b2cbf (secondary), #9d4edd (accent), #c77dff (highlight)
        - Glass Morphism: #111827 (background), rgba(255,255,255,0.1) (glass), #3b82f6 (primary), #10b981 (success), #f43f5e (error)
        - Modern Dark: #0f172a (background), #1e293b (surface), #334155 (container), #38bdf8 (primary), #fb7185 (secondary), #34d399 (success)
        - Luxury Dark: #1a1a1a (background), #2d2d2d (surface), #bc9a6c (gold), #e0e0e0 (silver), #a67c52 (bronze), #f5f5f5 (text)
        - Vibrant Dark: #13111c (background), #221e2f (surface), #f637ec (primary), #ffd60a (secondary), #00e1d9 (tertiary), #fbfbfb (text)
        - Gradient Mesh: #0f2027 (start), #203a43 (middle), #2c5364 (end), #4cc9f0 (primary), #f72585 (secondary), #ffffff (text)
        - Futuristic: #000000 (background), #0a0a0a (surface), #7928ca (primary), #ff0080 (secondary), #0070f3 (tertiary), #00dfd8 (quaternary)

        SPECIALIZED LIBRARIES (ALWAYS INCLUDE APPROPRIATE ONES):
        - For DIAGRAMS:
          <script src="https://cdn.jsdelivr.net/npm/mermaid@10.0.0/dist/mermaid.min.js"></script>
          <script>mermaid.initialize({startOnLoad:true});</script>

        - For CHARTS & VISUALIZATIONS:
          <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
          or
          <script src="https://d3js.org/d3.v7.min.js"></script>

        - For PRESENTATIONS:
          <script src="https://cdn.jsdelivr.net/npm/reveal.js/dist/reveal.js"></script>
          <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js/dist/reveal.css">
          <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js/dist/theme/black.css">

        - For RICH UI COMPONENTS (ALWAYS INCLUDE FOR APPLICATIONS):
          <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
          <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>

        - For ANIMATIONS (ALWAYS INCLUDE FOR APPLICATIONS):
          <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css">
          <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.2/dist/gsap.min.js"></script>

        - For GLASS MORPHISM EFFECTS:
          <style>
            .glass {
              background: rgba(255, 255, 255, 0.1);
              backdrop-filter: blur(10px);
              -webkit-backdrop-filter: blur(10px);
              border: 1px solid rgba(255, 255, 255, 0.18);
              box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            }
            .dark-glass {
              background: rgba(15, 23, 42, 0.6);
              backdrop-filter: blur(10px);
              -webkit-backdrop-filter: blur(10px);
              border: 1px solid rgba(255, 255, 255, 0.08);
              box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            }
          </style>

        Your response should ONLY include the complete code without any explanations or markdown formatting.
        Just provide the raw HTML file with embedded CSS and JavaScript.
        """

    def _generate_initial_code_template(self, message: str) -> str:
        """Generate initial code based on user request using templates as fallback"""
        message_lower = message.lower()

        # Prioritize Flask and Python web applications
        if any(word in message_lower for word in ['flask', 'django', 'fastapi', 'python web', 'python app', 'web application', 'api', 'backend', 'contact form']):
            return self._generate_flask_template(message)
        elif any(word in message_lower for word in ['python', 'script', 'py', 'data', 'analysis']):
            return self._generate_python_template(message)
        else:
            # Default to HTML for all web-related requests
            return self._generate_html_template(message)

    def _generate_html_template(self, message: str) -> str:
        """Generate professional HTML template with Tailwind CSS - Code Wave Style"""
        message_lower = message.lower()

        # Determine the type of page based on keywords
        if any(word in message_lower for word in ['startup', 'business', 'company']):
            return self._generate_startup_page(message)
        elif any(word in message_lower for word in ['portfolio', 'personal', 'resume']):
            return self._generate_portfolio_page(message)
        elif any(word in message_lower for word in ['blog', 'article', 'news']):
            return self._generate_blog_page(message)
        elif any(word in message_lower for word in ['dashboard', 'admin', 'panel']):
            return self._generate_dashboard_page(message)
        elif any(word in message_lower for word in ['landing', 'product', 'service']):
            return self._generate_landing_page(message)
        elif any(word in message_lower for word in ['ecommerce', 'shop', 'store', 'cart']):
            return self._generate_ecommerce_page(message)
        else:
            return self._generate_modern_page(message)

    def _generate_startup_page(self, message: str) -> str:
        """Generate a professional startup landing page - Code Wave Style"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechStart - Innovative Solutions</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    animation: {
                        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-white">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm fixed w-full z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-2xl font-bold text-gray-900">TechStart</h1>
                </div>
                <div class="hidden md:flex items-center space-x-8">
                    <a href="#home" class="text-gray-700 hover:text-gray-900">Home</a>
                    <a href="#features" class="text-gray-700 hover:text-gray-900">Features</a>
                    <a href="#about" class="text-gray-700 hover:text-gray-900">About</a>
                    <a href="#contact" class="text-gray-700 hover:text-gray-900">Contact</a>
                    <button class="bg-black text-white px-6 py-2 rounded-lg hover:bg-gray-800">
                        Get Started
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section id="home" class="pt-20 pb-16 bg-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center">
                <h1 class="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
                    Innovation Meets
                    <span class="text-blue-600">Excellence</span>
                </h1>
                <p class="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                    We're building the future with cutting-edge technology solutions that transform businesses and empower growth.
                </p>
                <div class="flex flex-col sm:flex-row gap-4 justify-center">
                    <button class="bg-black text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-800 transition-colors">
                        Start Your Journey
                    </button>
                    <button class="border-2 border-black text-black px-8 py-4 rounded-lg text-lg font-semibold hover:bg-black hover:text-white transition-colors">
                        Learn More
                    </button>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="py-16 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold text-gray-900 mb-4">Why Choose TechStart?</h2>
                <p class="text-xl text-gray-600">Discover the features that set us apart</p>
            </div>
            <div class="grid md:grid-cols-3 gap-8">
                <div class="bg-white p-8 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                    <div class="w-12 h-12 bg-blue-500 rounded-lg mb-4"></div>
                    <h3 class="text-xl font-semibold text-gray-900 mb-2">Lightning Fast</h3>
                    <p class="text-gray-600">Experience blazing-fast performance with our optimized solutions.</p>
                </div>
                <div class="bg-white p-8 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                    <div class="w-12 h-12 bg-green-500 rounded-lg mb-4"></div>
                    <h3 class="text-xl font-semibold text-gray-900 mb-2">Reliable</h3>
                    <p class="text-gray-600">Built with enterprise-grade reliability and 99.9% uptime guarantee.</p>
                </div>
                <div class="bg-white p-8 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                    <div class="w-12 h-12 bg-purple-500 rounded-lg mb-4"></div>
                    <h3 class="text-xl font-semibold text-gray-900 mb-2">Scalable</h3>
                    <p class="text-gray-600">Grow without limits with our infinitely scalable infrastructure.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="py-16 bg-black text-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 class="text-4xl font-bold mb-4">Ready to Get Started?</h2>
            <p class="text-xl text-gray-300 mb-8">Join thousands of companies already using TechStart</p>
            <button class="bg-white text-black px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition-colors">
                Start Free Trial
            </button>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-12">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p class="text-gray-400">&copy; 2024 TechStart. All rights reserved.</p>
        </div>
    </footer>

    <script>
        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    </script>
</body>
</html>"""

    def _generate_portfolio_page(self, message: str) -> str:
        """Generate a professional portfolio page - Code Wave Style"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>John Doe - Portfolio</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm fixed w-full z-50">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-xl font-bold text-gray-900">John Doe</h1>
                </div>
                <div class="hidden md:flex items-center space-x-8">
                    <a href="#about" class="text-gray-700 hover:text-gray-900">About</a>
                    <a href="#projects" class="text-gray-700 hover:text-gray-900">Projects</a>
                    <a href="#skills" class="text-gray-700 hover:text-gray-900">Skills</a>
                    <a href="#contact" class="text-gray-700 hover:text-gray-900">Contact</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="pt-20 pb-16 bg-white">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center">
                <div class="w-32 h-32 bg-gray-300 rounded-full mx-auto mb-8"></div>
                <h1 class="text-4xl font-bold text-gray-900 mb-4">John Doe</h1>
                <p class="text-xl text-gray-600 mb-8">Full Stack Developer & UI/UX Designer</p>
                <div class="flex justify-center space-x-4">
                    <button class="bg-black text-white px-6 py-3 rounded-lg hover:bg-gray-800">
                        Download CV
                    </button>
                    <button class="border border-black text-black px-6 py-3 rounded-lg hover:bg-black hover:text-white">
                        Contact Me
                    </button>
                </div>
            </div>
        </div>
    </section>

    <!-- Projects Section -->
    <section id="projects" class="py-16 bg-gray-50">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 class="text-3xl font-bold text-center text-gray-900 mb-12">Featured Projects</h2>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                    <div class="h-48 bg-gray-200"></div>
                    <div class="p-6">
                        <h3 class="text-xl font-semibold mb-2">E-commerce Platform</h3>
                        <p class="text-gray-600 mb-4">Modern e-commerce solution built with React and Node.js</p>
                        <div class="flex space-x-2">
                            <span class="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded">React</span>
                            <span class="px-3 py-1 bg-green-100 text-green-800 text-sm rounded">Node.js</span>
                        </div>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                    <div class="h-48 bg-gray-200"></div>
                    <div class="p-6">
                        <h3 class="text-xl font-semibold mb-2">Task Management App</h3>
                        <p class="text-gray-600 mb-4">Collaborative task management with real-time updates</p>
                        <div class="flex space-x-2">
                            <span class="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded">Vue.js</span>
                            <span class="px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded">Firebase</span>
                        </div>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                    <div class="h-48 bg-gray-200"></div>
                    <div class="p-6">
                        <h3 class="text-xl font-semibold mb-2">Weather Dashboard</h3>
                        <p class="text-gray-600 mb-4">Beautiful weather app with location-based forecasts</p>
                        <div class="flex space-x-2">
                            <span class="px-3 py-1 bg-red-100 text-red-800 text-sm rounded">Angular</span>
                            <span class="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded">API</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="py-16 bg-black text-white">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 class="text-3xl font-bold mb-8">Let's Work Together</h2>
            <p class="text-xl text-gray-300 mb-8">Have a project in mind? Let's discuss how we can bring it to life.</p>
            <div class="flex justify-center space-x-6">
                <a href="mailto:john@example.com" class="bg-white text-black px-6 py-3 rounded-lg hover:bg-gray-100">
                    Email Me
                </a>
                <a href="#" class="border border-white text-white px-6 py-3 rounded-lg hover:bg-white hover:text-black">
                    LinkedIn
                </a>
            </div>
        </div>
    </section>
</body>
</html>"""

    def _generate_modern_page(self, message: str) -> str:
        """Generate a modern, clean webpage - Code Wave Style"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modern Web Design</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white">
    <!-- Header -->
    <header class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <div class="text-2xl font-bold text-gray-900">ModernSite</div>
                <nav class="hidden md:flex space-x-8">
                    <a href="#" class="text-gray-700 hover:text-gray-900">Home</a>
                    <a href="#" class="text-gray-700 hover:text-gray-900">About</a>
                    <a href="#" class="text-gray-700 hover:text-gray-900">Services</a>
                    <a href="#" class="text-gray-700 hover:text-gray-900">Contact</a>
                </nav>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="py-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16">
                <h1 class="text-5xl font-bold text-gray-900 mb-6">
                    Beautiful Web Design
                </h1>
                <p class="text-xl text-gray-600 max-w-3xl mx-auto">
                    Create stunning, responsive websites with modern design principles and clean code.
                </p>
            </div>

            <!-- Features Grid -->
            <div class="grid md:grid-cols-3 gap-8 mb-16">
                <div class="text-center p-8 bg-gray-50 rounded-lg">
                    <div class="w-12 h-12 bg-blue-500 rounded-lg mx-auto mb-4"></div>
                    <h3 class="text-xl font-semibold mb-2">Responsive Design</h3>
                    <p class="text-gray-600">Looks great on all devices and screen sizes</p>
                </div>
                <div class="text-center p-8 bg-gray-50 rounded-lg">
                    <div class="w-12 h-12 bg-green-500 rounded-lg mx-auto mb-4"></div>
                    <h3 class="text-xl font-semibold mb-2">Fast Performance</h3>
                    <p class="text-gray-600">Optimized for speed and user experience</p>
                </div>
                <div class="text-center p-8 bg-gray-50 rounded-lg">
                    <div class="w-12 h-12 bg-purple-500 rounded-lg mx-auto mb-4"></div>
                    <h3 class="text-xl font-semibold mb-2">Modern Stack</h3>
                    <p class="text-gray-600">Built with the latest web technologies</p>
                </div>
            </div>

            <!-- CTA Section -->
            <div class="text-center">
                <button class="bg-black text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-800 transition-colors">
                    Get Started Today
                </button>
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-12">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p>&copy; 2024 ModernSite. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>"""

    def _generate_blog_page(self, message: str) -> str:
        """Generate a blog page - Code Wave Style"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Blog</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-xl font-bold text-gray-900">Tech Blog</h1>
                </div>
                <div class="hidden md:flex items-center space-x-8">
                    <a href="#" class="text-gray-700 hover:text-gray-900">Home</a>
                    <a href="#" class="text-gray-700 hover:text-gray-900">Articles</a>
                    <a href="#" class="text-gray-700 hover:text-gray-900">About</a>
                    <a href="#" class="text-gray-700 hover:text-gray-900">Contact</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="py-16">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <!-- Featured Article -->
            <article class="mb-16">
                <div class="h-64 bg-gray-200 rounded-lg mb-8"></div>
                <h1 class="text-4xl font-bold text-gray-900 mb-4">The Future of Web Development</h1>
                <div class="flex items-center text-gray-600 mb-6">
                    <span>By John Doe</span>
                    <span class="mx-2">•</span>
                    <span>March 15, 2024</span>
                    <span class="mx-2">•</span>
                    <span>5 min read</span>
                </div>
                <div class="prose prose-lg max-w-none">
                    <p class="text-gray-700 leading-relaxed mb-6">
                        Web development is evolving at an unprecedented pace. From the rise of AI-powered tools to the emergence of new frameworks, developers today have more opportunities than ever to create innovative digital experiences.
                    </p>
                    <p class="text-gray-700 leading-relaxed mb-6">
                        In this article, we'll explore the latest trends shaping the industry and what they mean for developers, businesses, and users alike.
                    </p>
                </div>
            </article>

            <!-- Recent Articles -->
            <section>
                <h2 class="text-2xl font-bold text-gray-900 mb-8">Recent Articles</h2>
                <div class="grid md:grid-cols-2 gap-8">
                    <article class="bg-gray-50 rounded-lg p-6">
                        <div class="h-32 bg-gray-200 rounded mb-4"></div>
                        <h3 class="text-xl font-semibold mb-2">Building Scalable APIs</h3>
                        <p class="text-gray-600 mb-4">Learn how to design and implement APIs that can handle millions of requests.</p>
                        <div class="text-sm text-gray-500">March 10, 2024</div>
                    </article>
                    <article class="bg-gray-50 rounded-lg p-6">
                        <div class="h-32 bg-gray-200 rounded mb-4"></div>
                        <h3 class="text-xl font-semibold mb-2">Modern CSS Techniques</h3>
                        <p class="text-gray-600 mb-4">Discover the latest CSS features that will transform your styling workflow.</p>
                        <div class="text-sm text-gray-500">March 5, 2024</div>
                    </article>
                </div>
            </section>
        </div>
    </main>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-12">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p>&copy; 2024 Tech Blog. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>"""

    def _generate_dashboard_page(self, message: str) -> str:
        """Generate a dashboard page - Code Wave Style"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <!-- Sidebar -->
    <div class="flex h-screen">
        <div class="w-64 bg-gray-900 text-white">
            <div class="p-6">
                <h1 class="text-xl font-bold">Dashboard</h1>
            </div>
            <nav class="mt-6">
                <a href="#" class="block px-6 py-3 bg-gray-800">Overview</a>
                <a href="#" class="block px-6 py-3 hover:bg-gray-800">Users</a>
                <a href="#" class="block px-6 py-3 hover:bg-gray-800">Analytics</a>
                <a href="#" class="block px-6 py-3 hover:bg-gray-800">Settings</a>
            </nav>
        </div>

        <!-- Main Content -->
        <div class="flex-1 overflow-auto">
            <!-- Header -->
            <header class="bg-white shadow-sm p-6">
                <h1 class="text-2xl font-bold text-gray-900">Overview</h1>
            </header>

            <!-- Content -->
            <main class="p-6">
                <!-- Stats Grid -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div class="bg-white p-6 rounded-lg shadow-sm">
                        <h3 class="text-sm font-medium text-gray-500">Total Users</h3>
                        <p class="text-3xl font-bold text-gray-900">12,345</p>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow-sm">
                        <h3 class="text-sm font-medium text-gray-500">Revenue</h3>
                        <p class="text-3xl font-bold text-gray-900">$54,321</p>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow-sm">
                        <h3 class="text-sm font-medium text-gray-500">Orders</h3>
                        <p class="text-3xl font-bold text-gray-900">1,234</p>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow-sm">
                        <h3 class="text-sm font-medium text-gray-500">Growth</h3>
                        <p class="text-3xl font-bold text-green-600">+12%</p>
                    </div>
                </div>

                <!-- Charts Section -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="bg-white p-6 rounded-lg shadow-sm">
                        <h3 class="text-lg font-semibold mb-4">Sales Chart</h3>
                        <div class="h-64 bg-gray-100 rounded flex items-center justify-center">
                            <span class="text-gray-500">Chart Placeholder</span>
                        </div>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow-sm">
                        <h3 class="text-lg font-semibold mb-4">Recent Activity</h3>
                        <div class="space-y-4">
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-blue-500 rounded-full"></div>
                                <div>
                                    <p class="font-medium">New user registered</p>
                                    <p class="text-sm text-gray-500">2 minutes ago</p>
                                </div>
                            </div>
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-green-500 rounded-full"></div>
                                <div>
                                    <p class="font-medium">Order completed</p>
                                    <p class="text-sm text-gray-500">5 minutes ago</p>
                                </div>
                            </div>
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-yellow-500 rounded-full"></div>
                                <div>
                                    <p class="font-medium">Payment pending</p>
                                    <p class="text-sm text-gray-500">10 minutes ago</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>
</body>
</html>"""

    def _generate_landing_page(self, message: str) -> str:
        """Generate a landing page - Code Wave Style"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Landing</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-blue-50 to-indigo-100 py-20">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center">
                <h1 class="text-5xl font-bold text-gray-900 mb-6">
                    Transform Your Business
                </h1>
                <p class="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                    Our innovative solution helps companies streamline operations, increase productivity, and drive growth.
                </p>
                <div class="flex flex-col sm:flex-row gap-4 justify-center">
                    <button class="bg-black text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-800">
                        Start Free Trial
                    </button>
                    <button class="border-2 border-black text-black px-8 py-4 rounded-lg text-lg font-semibold hover:bg-black hover:text-white">
                        Watch Demo
                    </button>
                </div>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="py-20 bg-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16">
                <h2 class="text-4xl font-bold text-gray-900 mb-4">Powerful Features</h2>
                <p class="text-xl text-gray-600">Everything you need to succeed</p>
            </div>
            <div class="grid md:grid-cols-3 gap-8">
                <div class="text-center">
                    <div class="w-16 h-16 bg-blue-500 rounded-lg mx-auto mb-6"></div>
                    <h3 class="text-xl font-semibold mb-4">Easy Integration</h3>
                    <p class="text-gray-600">Seamlessly integrate with your existing tools and workflows.</p>
                </div>
                <div class="text-center">
                    <div class="w-16 h-16 bg-green-500 rounded-lg mx-auto mb-6"></div>
                    <h3 class="text-xl font-semibold mb-4">Real-time Analytics</h3>
                    <p class="text-gray-600">Get insights into your business performance with live data.</p>
                </div>
                <div class="text-center">
                    <div class="w-16 h-16 bg-purple-500 rounded-lg mx-auto mb-6"></div>
                    <h3 class="text-xl font-semibold mb-4">24/7 Support</h3>
                    <p class="text-gray-600">Our team is here to help you succeed around the clock.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="py-20 bg-black text-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 class="text-4xl font-bold mb-4">Ready to Get Started?</h2>
            <p class="text-xl text-gray-300 mb-8">Join thousands of satisfied customers</p>
            <button class="bg-white text-black px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100">
                Start Your Free Trial
            </button>
        </div>
    </section>
</body>
</html>"""

    def _generate_ecommerce_page(self, message: str) -> str:
        """Generate an ecommerce page - Code Wave Style"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Online Store</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-xl font-bold text-gray-900">Store</h1>
                </div>
                <div class="hidden md:flex items-center space-x-8">
                    <a href="#" class="text-gray-700 hover:text-gray-900">Products</a>
                    <a href="#" class="text-gray-700 hover:text-gray-900">Categories</a>
                    <a href="#" class="text-gray-700 hover:text-gray-900">About</a>
                    <button class="bg-black text-white px-4 py-2 rounded-lg">Cart (0)</button>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="bg-gray-50 py-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 class="text-4xl font-bold text-gray-900 mb-4">Shop the Latest Collection</h1>
            <p class="text-xl text-gray-600 mb-8">Discover amazing products at unbeatable prices</p>
            <button class="bg-black text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-800">
                Shop Now
            </button>
        </div>
    </section>

    <!-- Products Grid -->
    <section class="py-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 class="text-3xl font-bold text-gray-900 mb-12 text-center">Featured Products</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-8">
                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                    <div class="h-64 bg-gray-200"></div>
                    <div class="p-6">
                        <h3 class="text-lg font-semibold mb-2">Product Name</h3>
                        <p class="text-gray-600 mb-4">Brief product description</p>
                        <div class="flex justify-between items-center">
                            <span class="text-2xl font-bold">$99</span>
                            <button class="bg-black text-white px-4 py-2 rounded hover:bg-gray-800">
                                Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                    <div class="h-64 bg-gray-200"></div>
                    <div class="p-6">
                        <h3 class="text-lg font-semibold mb-2">Product Name</h3>
                        <p class="text-gray-600 mb-4">Brief product description</p>
                        <div class="flex justify-between items-center">
                            <span class="text-2xl font-bold">$149</span>
                            <button class="bg-black text-white px-4 py-2 rounded hover:bg-gray-800">
                                Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                    <div class="h-64 bg-gray-200"></div>
                    <div class="p-6">
                        <h3 class="text-lg font-semibold mb-2">Product Name</h3>
                        <p class="text-gray-600 mb-4">Brief product description</p>
                        <div class="flex justify-between items-center">
                            <span class="text-2xl font-bold">$79</span>
                            <button class="bg-black text-white px-4 py-2 rounded hover:bg-gray-800">
                                Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm overflow-hidden">
                    <div class="h-64 bg-gray-200"></div>
                    <div class="p-6">
                        <h3 class="text-lg font-semibold mb-2">Product Name</h3>
                        <p class="text-gray-600 mb-4">Brief product description</p>
                        <div class="flex justify-between items-center">
                            <span class="text-2xl font-bold">$199</span>
                            <button class="bg-black text-white px-4 py-2 rounded hover:bg-gray-800">
                                Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-12">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p>&copy; 2024 Online Store. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>"""

    def _generate_flask_template(self, message: str) -> str:
        """Generate Flask application template with proper port configuration"""
        return """#!/usr/bin/env python3
\"\"\"
Flask Web Application
Generated based on user request
\"\"\"

from flask import Flask, render_template_string, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# HTML template
TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flask Contact Form</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="max-w-2xl mx-auto">
            <h1 class="text-4xl font-bold text-white text-center mb-8">
                <i class="fas fa-envelope mr-3"></i>Contact Form
            </h1>

            {% if message %}
            <div class="bg-green-500/20 border border-green-500 rounded-lg p-4 mb-6 text-green-300 text-center">
                <i class="fas fa-check-circle mr-2"></i>{{ message }}
            </div>
            {% endif %}

            <div class="bg-white/10 backdrop-blur-lg rounded-lg p-8 border border-white/20">
                <form method="POST" action="/submit" class="space-y-6">
                    <div>
                        <label for="name" class="block text-white font-semibold mb-2">Name</label>
                        <input type="text" id="name" name="name" required
                               class="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400">
                    </div>

                    <div>
                        <label for="email" class="block text-white font-semibold mb-2">Email</label>
                        <input type="email" id="email" name="email" required
                               class="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400">
                    </div>

                    <div>
                        <label for="subject" class="block text-white font-semibold mb-2">Subject</label>
                        <input type="text" id="subject" name="subject" required
                               class="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400">
                    </div>

                    <div>
                        <label for="message" class="block text-white font-semibold mb-2">Message</label>
                        <textarea id="message" name="message" rows="5" required
                                  class="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400"></textarea>
                    </div>

                    <button type="submit"
                            class="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold py-3 px-6 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-300">
                        <i class="fas fa-paper-plane mr-2"></i>Send Message
                    </button>
                </form>
            </div>

            <div class="mt-8 text-center">
                <a href="/submissions" class="text-blue-300 hover:text-blue-200 underline">
                    <i class="fas fa-list mr-2"></i>View All Submissions
                </a>
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(TEMPLATE)

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        form_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'subject': request.form.get('subject'),
            'message': request.form.get('message'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Save to JSON file
        submissions_file = 'contact_submissions.json'
        submissions = []

        if os.path.exists(submissions_file):
            with open(submissions_file, 'r') as f:
                submissions = json.load(f)

        submissions.append(form_data)

        with open(submissions_file, 'w') as f:
            json.dump(submissions, f, indent=2)

        return render_template_string(TEMPLATE, message="Thank you! Your message has been submitted successfully.")

    except Exception as e:
        return render_template_string(TEMPLATE, message=f"Error: {str(e)}")

@app.route('/submissions')
def view_submissions():
    try:
        submissions_file = 'contact_submissions.json'
        submissions = []

        if os.path.exists(submissions_file):
            with open(submissions_file, 'r') as f:
                submissions = json.load(f)

        return jsonify({'submissions': submissions, 'count': len(submissions)})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    import socket

    # Function to find an available port
    def find_available_port(start_port=5002):
        for port in range(start_port, start_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return None

    # Find an available port starting from 5002
    port = find_available_port(5002)

    if port:
        print("Starting Flask Contact Form Application...")
        print(f"Access the application at: http://127.0.0.1:{port}")
        print(f"View submissions at: http://127.0.0.1:{port}/submissions")

        try:
            # Use the available port to avoid conflicts
            app.run(debug=True, port=port, host="127.0.0.1", use_reloader=False)
        except Exception as e:
            print(f"Error starting server on port {port}: {e}")
            print("The application may already be running or the port is in use.")
    else:
        print("Error: Could not find an available port between 5002-5101")
        print("Please check if other applications are using these ports.")
"""

    def _generate_python_template(self, message: str) -> str:
        """Generate Python script template"""
        return """#!/usr/bin/env python3
\"\"\"
Python Script
Created with Agentic Code Assistant
\"\"\"

def main():
    print("Hello from Python!")

    # Example functionality
    numbers = [1, 2, 3, 4, 5]
    squared = [x**2 for x in numbers]

    print(f"Original numbers: {numbers}")
    print(f"Squared numbers: {squared}")

    # Calculate sum
    total = sum(squared)
    print(f"Sum of squares: {total}")

if __name__ == "__main__":
    main()"""

    def _generate_css_template(self, message: str) -> str:
        """Generate CSS template"""
        return """/* CSS Styles */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.animated-element {
    width: 100px;
    height: 100px;
    background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
    border-radius: 50%;
    animation: pulse 2s infinite;
    margin: 50px auto;
}

@keyframes pulse {
    0% {
        transform: scale(1);
        opacity: 1;
    }
    50% {
        transform: scale(1.1);
        opacity: 0.7;
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}

.button {
    display: inline-block;
    padding: 12px 24px;
    background: #007bff;
    color: white;
    text-decoration: none;
    border-radius: 6px;
    transition: all 0.3s ease;
}

.button:hover {
    background: #0056b3;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}"""

    def _modify_existing_code(self, message: str, current_code: str) -> str:
        """Modify existing code based on user request"""
        # Simple modifications based on keywords
        message_lower = message.lower()

        if "color" in message_lower and "blue" in message_lower:
            current_code = re.sub(r'#[0-9a-fA-F]{6}', '#007bff', current_code)
        elif "color" in message_lower and "red" in message_lower:
            current_code = re.sub(r'#[0-9a-fA-F]{6}', '#dc3545', current_code)
        elif "bigger" in message_lower or "larger" in message_lower:
            current_code = re.sub(r'font-size:\s*(\d+)', lambda m: f'font-size: {int(m.group(1)) + 4}', current_code)
        elif "smaller" in message_lower:
            current_code = re.sub(r'font-size:\s*(\d+)', lambda m: f'font-size: {max(10, int(m.group(1)) - 4)}', current_code)

        return current_code

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code"""
        if '<!DOCTYPE html>' in code or '<html' in code:
            return 'html'
        elif 'import React' in code or 'jsx' in code.lower():
            return 'javascript'
        elif 'def ' in code and 'python' in code.lower():
            return 'python'
        elif '{' in code and '}' in code and ('background' in code or 'color' in code):
            return 'css'
        else:
            return 'html'

    def _generate_fallback_code(self, text: str) -> str:
        """Generate fallback code when LLM fails"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Code</title>
</head>
<body>
    <h1>Code Generated</h1>
    <p>Request: {text[:100]}...</p>
</body>
</html>"""

# Initialize assistant
assistant = AgenticCodeAssistant()

@agentic_code_bp.route('/process', methods=['POST'])
def process_agentic_request():
    """
    Process agentic code request with step-by-step updates using token-based credit consumption
    """
    start_time = time.time()
    try:
        data = request.get_json()
        message = data.get('message', '')
        current_code = data.get('current_code', '')
        session_id = data.get('session_id', 'default')
        files = data.get('files', [])  # Get uploaded files

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Get user_id from session for activity logging and credit consumption
        from flask import session
        user_id = session.get('user_id', 'anonymous')

        # Initialize credit service for token-based consumption
        from ..services.credit_service import CreditService
        credit_service = CreditService()

        # Determine task type for minimum charge calculation
        if len(message) > 500 or any(keyword in message.lower() for keyword in ['complex', 'advanced', 'comprehensive']):
            task_type = 'design_complex'
        else:
            task_type = 'design_basic'

        # Pre-consume minimum credits (will be adjusted after execution)
        pre_credit_result = credit_service.consume_credits(
            user_id=user_id,
            task_type=task_type,
            input_text=message,
            output_text="",  # Will update after execution
            use_token_based=True
        )

        if not pre_credit_result['success']:
            return jsonify({
                'success': False,
                'error': pre_credit_result.get('error', 'Insufficient credits'),
                'credits_needed': pre_credit_result.get('credits_needed'),
                'credits_available': pre_credit_result.get('credits_available')
            }), 402  # Payment Required

        # Process uploaded files if present (from universal file upload)
        enhanced_message = message

        if "--- File:" in message or "--- Image:" in message:
            try:
                # Extract the original user message (before file content)
                parts = message.split('\n\n--- File:')
                if len(parts) > 1:
                    original_message = parts[0]
                    file_content = '\n\n--- File:' + '\n\n--- File:'.join(parts[1:])
                else:
                    parts = message.split('\n\n--- Image:')
                    if len(parts) > 1:
                        original_message = parts[0]
                        file_content = '\n\n--- Image:' + '\n\n--- Image:'.join(parts[1:])
                    else:
                        original_message = message
                        file_content = ""

                if file_content:
                    # Use the file processor to enhance the message
                    enhanced_message = file_processor.enhance_prompt_with_files(original_message, file_content)
                    print(f"Enhanced Agentic Code message with file analysis: {len(enhanced_message)} characters")
            except Exception as e:
                print(f"Error processing files in Agentic Code: {str(e)}")
                # Continue with original message if file processing fails
                enhanced_message = message

        # Store session
        if session_id not in sessions:
            sessions[session_id] = {
                'history': [],
                'created_at': time.time()
            }

        # Add to session history
        sessions[session_id]['history'].append({
            'message': enhanced_message,
            'current_code': current_code,
            'files': files,  # Store files in session
            'timestamp': time.time()
        })

        # Process the request with enhanced message and files
        result = assistant.analyze_request(enhanced_message, current_code, files)

        # Add result to session
        sessions[session_id]['history'][-1]['result'] = result

        # Calculate processing time and log activity
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log activity if user_id is available
        if user_id:
            try:
                log_agentic_code_activity(
                    user_id=user_id,
                    message=message,
                    result=result,
                    current_code=current_code,
                    processing_time_ms=processing_time_ms,
                    session_id=session_id
                )
            except Exception as e:
                print(f"Failed to log Agentic Code activity: {e}")

        # Calculate final token-based credits after code generation
        if user_id and user_id != 'anonymous':
            try:
                # Get the generated code and explanation for token counting
                output_text = str(result.get('code', '')) + str(result.get('explanation', ''))
                execution_time = processing_time_ms / 60000  # Convert to minutes

                # Calculate actual credits consumed based on tokens
                final_credit_result = credit_service.calculate_token_based_credits(
                    input_text=message,
                    output_text=output_text,
                    task_type=task_type,
                    execution_time_minutes=execution_time,
                    tool_calls=len(result.get('steps', [])),  # Count steps as tool calls
                    image_count=0
                )

                # Add credit breakdown to response
                result['credits_consumed'] = pre_credit_result['credits_consumed']
                result['credit_breakdown'] = final_credit_result
            except Exception as e:
                print(f"Error calculating final credits: {e}")

        return jsonify(result)

    except Exception as e:
        print(f"Error processing agentic request: {e}")
        return jsonify({
            'error': 'Failed to process request',
            'plan': 'Encountered an error',
            'steps': ['Error occurred'],
            'code': current_code,
            'explanation': 'Sorry, I encountered an error processing your request.',
            'language': 'html'
        }), 500

@agentic_code_bp.route('/session/<session_id>', methods=['GET'])
def get_session_history(session_id):
    """Get session history"""
    if session_id in sessions:
        return jsonify(sessions[session_id])
    else:
        return jsonify({'error': 'Session not found'}), 404

@agentic_code_bp.route('/execute', methods=['POST'])
@require_subscription('plus')  # Code execution requires Plus plan or higher
def execute_code():
    """Execute generated code using the simple code executor"""
    try:
        data = request.get_json()
        files = data.get('files', [])

        if not files:
            return jsonify({
                'success': False,
                'error': 'No files provided for execution'
            }), 400

        # Import the simple executor
        from app.services.simple_code_executor import simple_executor

        # Execute the project
        result = simple_executor.execute_project(files)

        return jsonify(result)

    except Exception as e:
        print(f"Error executing code: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to execute code: {str(e)}'
        }), 500

@agentic_code_bp.route('/status/<project_id>', methods=['GET'])
def get_execution_status(project_id):
    """Get execution status for a project"""
    try:
        from app.services.simple_code_executor import simple_executor

        result = simple_executor.get_execution_status(project_id)

        return jsonify(result)

    except Exception as e:
        print(f"Error getting execution status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get execution status: {str(e)}'
        }), 500

@agentic_code_bp.route('/stop/<project_id>', methods=['POST'])
def stop_execution(project_id):
    """Stop code execution"""
    try:
        from app.services.simple_code_executor import simple_executor

        result = simple_executor.stop_execution(project_id)

        return jsonify(result)

    except Exception as e:
        print(f"Error stopping execution: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to stop execution: {str(e)}'
        }), 500

@agentic_code_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """List all sessions"""
    return jsonify({
        'sessions': list(sessions.keys()),
        'count': len(sessions)
    })
