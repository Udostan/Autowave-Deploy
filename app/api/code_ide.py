"""
Code Wave API

This module provides API endpoints for code generation and execution.
"""

import logging
import json
import re
from flask import Blueprint, request, jsonify, Response, stream_with_context
from app.api.gemini import GeminiAPI

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
code_ide_bp = Blueprint('code_ide', __name__)

# Initialize Gemini API
try:
    gemini_api = GeminiAPI()
    GEMINI_AVAILABLE = True
except Exception as e:
    logger.warning(f"Failed to initialize Gemini API: {e}")
    gemini_api = None
    GEMINI_AVAILABLE = False

class CodeSectionParser:
    """
    Intelligent code parser that identifies and extracts specific sections
    of HTML, CSS, and JavaScript code for targeted editing.
    """

    def __init__(self):
        self.html_element_pattern = r'<(\w+)([^>]*)>(.*?)</\1>'
        self.css_rule_pattern = r'([^{]+)\s*\{([^}]+)\}'
        self.js_function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*\}'

    def identify_sections(self, code):
        """
        Identify all editable sections in the code.

        Args:
            code (str): The complete HTML/CSS/JS code

        Returns:
            dict: Dictionary of identified sections with metadata
        """
        sections = {
            'html_elements': self._extract_html_elements(code),
            'css_rules': self._extract_css_rules(code),
            'js_functions': self._extract_js_functions(code),
            'inline_styles': self._extract_inline_styles(code),
            'text_content': self._extract_text_content(code)
        }

        return sections

    def _extract_html_elements(self, code):
        """Extract HTML elements with their positions."""
        elements = []
        pattern = r'<(\w+)([^>]*?)>(.*?)</\1>'

        for match in re.finditer(pattern, code, re.DOTALL | re.IGNORECASE):
            tag_name = match.group(1)
            attributes = match.group(2).strip()
            content = match.group(3)
            start_pos = match.start()
            end_pos = match.end()

            # Skip script and style tags for now
            if tag_name.lower() not in ['script', 'style']:
                elements.append({
                    'type': 'html_element',
                    'tag': tag_name,
                    'attributes': attributes,
                    'content': content,
                    'full_match': match.group(0),
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'editable_aspects': ['content', 'attributes', 'styling']
                })

        return elements

    def _extract_css_rules(self, code):
        """Extract CSS rules from style tags and inline styles."""
        rules = []

        # Extract from <style> tags
        style_pattern = r'<style[^>]*>(.*?)</style>'
        for style_match in re.finditer(style_pattern, code, re.DOTALL | re.IGNORECASE):
            css_content = style_match.group(1)
            style_start = style_match.start()

            # Extract individual CSS rules
            rule_pattern = r'([^{]+)\s*\{([^}]+)\}'
            for rule_match in re.finditer(rule_pattern, css_content):
                selector = rule_match.group(1).strip()
                properties = rule_match.group(2).strip()

                rules.append({
                    'type': 'css_rule',
                    'selector': selector,
                    'properties': properties,
                    'full_match': rule_match.group(0),
                    'start_pos': style_start + rule_match.start(),
                    'end_pos': style_start + rule_match.end(),
                    'editable_aspects': ['properties', 'selector']
                })

        return rules

    def _extract_js_functions(self, code):
        """Extract JavaScript functions."""
        functions = []

        # Extract from <script> tags
        script_pattern = r'<script[^>]*>(.*?)</script>'
        for script_match in re.finditer(script_pattern, code, re.DOTALL | re.IGNORECASE):
            js_content = script_match.group(1)
            script_start = script_match.start()

            # Extract function declarations
            func_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*\}'
            for func_match in re.finditer(func_pattern, js_content):
                func_name = func_match.group(1)

                functions.append({
                    'type': 'js_function',
                    'name': func_name,
                    'full_match': func_match.group(0),
                    'start_pos': script_start + func_match.start(),
                    'end_pos': script_start + func_match.end(),
                    'editable_aspects': ['logic', 'parameters']
                })

        return functions

    def _extract_inline_styles(self, code):
        """Extract inline style attributes."""
        styles = []
        style_pattern = r'style\s*=\s*["\']([^"\']+)["\']'

        for match in re.finditer(style_pattern, code, re.IGNORECASE):
            styles.append({
                'type': 'inline_style',
                'properties': match.group(1),
                'full_match': match.group(0),
                'start_pos': match.start(),
                'end_pos': match.end(),
                'editable_aspects': ['properties']
            })

        return styles

    def _extract_text_content(self, code):
        """Extract text content from HTML elements."""
        content = []
        # Simple pattern to find text between tags (excluding script/style)
        text_pattern = r'>([^<]+)<'

        for match in re.finditer(text_pattern, code):
            text = match.group(1).strip()
            if text and not text.isspace():
                content.append({
                    'type': 'text_content',
                    'text': text,
                    'start_pos': match.start(1),
                    'end_pos': match.end(1),
                    'editable_aspects': ['text']
                })

        return content

    def find_target_section(self, code, user_prompt):
        """
        Analyze user prompt to determine which section they want to edit.

        Args:
            code (str): The complete code
            user_prompt (str): User's editing request

        Returns:
            dict: Best matching section for the edit request
        """
        sections = self.identify_sections(code)
        prompt_lower = user_prompt.lower()

        # Keywords for different types of edits
        color_keywords = ['color', 'background', 'blue', 'red', 'green', 'yellow', 'purple', 'orange']
        text_keywords = ['text', 'title', 'heading', 'content', 'word', 'change text']
        layout_keywords = ['layout', 'position', 'margin', 'padding', 'width', 'height', 'size']
        animation_keywords = ['animation', 'animate', 'transition', 'hover', 'effect']

        # Score sections based on relevance to prompt
        scored_sections = []

        for section_type, section_list in sections.items():
            for section in section_list:
                score = 0

                # Score based on keywords in prompt
                if any(keyword in prompt_lower for keyword in color_keywords):
                    if section['type'] in ['css_rule', 'inline_style']:
                        score += 10

                if any(keyword in prompt_lower for keyword in text_keywords):
                    if section['type'] == 'text_content':
                        score += 10
                    elif section['type'] == 'html_element':
                        score += 5

                if any(keyword in prompt_lower for keyword in layout_keywords):
                    if section['type'] in ['css_rule', 'inline_style']:
                        score += 8

                if any(keyword in prompt_lower for keyword in animation_keywords):
                    if section['type'] == 'css_rule':
                        score += 10

                # Add context-based scoring
                if section['type'] == 'html_element':
                    if 'button' in prompt_lower and section['tag'].lower() == 'button':
                        score += 15
                    elif 'heading' in prompt_lower and section['tag'].lower() in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        score += 15

                if score > 0:
                    section['relevance_score'] = score
                    scored_sections.append(section)

        # Return the highest scoring section
        if scored_sections:
            return max(scored_sections, key=lambda x: x['relevance_score'])

        # Fallback: return the first CSS rule if no specific match
        if sections['css_rules']:
            return sections['css_rules'][0]

        return None

@code_ide_bp.route('/api/code/generate', methods=['POST'])
def generate_code():
    """
    Generate code based on the provided prompt.

    Returns:
        Response: JSON response with the generated code.
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        content_types = data.get('contentTypes', [])

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'No prompt provided'
            })

        logger.info(f"Generating code for prompt: {prompt}")

        # System prompt for code generation
        system_prompt = """
        You are an expert web developer specializing in HTML, CSS (with Tailwind CSS), and JavaScript.
        Your task is to generate clean, well-structured, and functional code based on the user's request.

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

        # Generate code using Gemini API
        # Combine system prompt and user prompt
        content_type_str = ""
        if content_types:
            content_type_str = f"\n\nDetected content types: {', '.join(content_types)}"

        full_prompt = f"{system_prompt}\n\nCreate the following web component or application: {prompt}{content_type_str}"

        if GEMINI_AVAILABLE and gemini_api:
            response = gemini_api.generate_text(
                prompt=full_prompt,
                temperature=0.2
            )
        else:
            logger.warning("Gemini API not available, using fallback response")
            response = "// Gemini API not available - please configure API key"

        # Check if response is valid
        if response is None:
            logger.error("Gemini API returned None response")
            return jsonify({
                'success': False,
                'error': 'API returned empty response'
            })

        # Extract code from response
        code = response.strip()

        # If the response contains markdown code blocks, extract the code
        if "```html" in code:
            code = code.split("```html")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        logger.info("Code generation successful")

        return jsonify({
            'success': True,
            'code': code
        })
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@code_ide_bp.route('/api/code/generate-stream', methods=['POST'])
def generate_code_stream():
    """
    Generate code based on the provided prompt with streaming response.

    Returns:
        Response: Streaming response with the generated code.
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        content_types = data.get('contentTypes', [])

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'No prompt provided'
            })

        logger.info(f"Generating code with streaming for prompt: {prompt}")

        # System prompt for code generation
        system_prompt = """
        You are an expert web developer specializing in HTML, CSS (with Tailwind CSS), and JavaScript.
        Your task is to generate clean, well-structured, and functional code based on the user's request.

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

        # Combine system prompt and user prompt
        content_type_str = ""
        if content_types:
            content_type_str = f"\n\nDetected content types: {', '.join(content_types)}"

        full_prompt = f"{system_prompt}\n\nCreate the following web component or application: {prompt}{content_type_str}"

        def generate():
            # Send initial event to start the stream
            yield 'data: {"event": "start"}\n\n'

            # Use the Gemini API with streaming
            try:
                # Initialize code buffer
                code_buffer = ""

                # Generate code using Gemini API with streaming
                if GEMINI_AVAILABLE and gemini_api:
                    for chunk in gemini_api.generate_text_stream(prompt=full_prompt, temperature=0.2):
                        code_buffer += chunk
                        # Send the chunk as an event
                        yield f'data: {{"event": "chunk", "chunk": {json.dumps(chunk)}}}\n\n'
                else:
                    # Fallback when Gemini API not available
                    fallback_response = "// Gemini API not available - please configure API key"
                    code_buffer = fallback_response
                    yield f'data: {{"event": "chunk", "chunk": {json.dumps(fallback_response)}}}\n\n'

                # Extract code from response if needed
                if code_buffer:
                    code = code_buffer.strip()
                else:
                    code = "// No code generated"
            except Exception as e:
                logger.error(f"Error in streaming generation: {str(e)}")
                yield f'data: {{"event": "error", "error": {json.dumps(str(e))}}}\n\n'
                code = f"// Error generating code: {str(e)}"

            # If the response contains markdown code blocks, extract the code
            if "```html" in code:
                code = code.split("```html")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()

            # Send the complete code as the final event
            yield f'data: {{"event": "complete", "code": {json.dumps(code)}}}\n\n'

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )
    except Exception as e:
        logger.error(f"Error generating streaming code: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@code_ide_bp.route('/api/code/execute', methods=['POST'])
def execute_code():
    """
    Execute the provided code and return the result.

    Returns:
        Response: JSON response with the execution result.
    """
    try:
        data = request.get_json()
        code = data.get('code', '')

        if not code:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            })

        logger.info("Executing code")

        # For now, we just return the code as is since it will be executed in the browser
        # In the future, we could add server-side execution for other languages

        return jsonify({
            'success': True,
            'result': code
        })
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@code_ide_bp.route('/api/code/edit-section', methods=['POST'])
def edit_code_section():
    """
    Edit a specific section of code based on user prompt.

    This endpoint uses the Targeted Code Section Editor to modify
    only the relevant parts of the code without affecting the rest.

    Expected JSON payload:
    {
        "prompt": "user editing request",
        "current_code": "complete current code",
        "target_section": "optional specific section to edit"
    }
    """
    try:
        data = request.get_json()
        user_prompt = data.get('prompt', '').strip()
        current_code = data.get('current_code', '')
        target_section = data.get('target_section')

        if not user_prompt:
            return jsonify({
                'success': False,
                'error': 'No editing prompt provided'
            })

        if not current_code:
            return jsonify({
                'success': False,
                'error': 'No current code provided'
            })

        logger.info(f"Processing targeted edit request: {user_prompt[:100]}...")

        # Initialize the code parser
        parser = CodeSectionParser()

        # Find the target section to edit
        if target_section:
            # Use provided target section
            target = target_section
        else:
            # Automatically detect target section
            target = parser.find_target_section(current_code, user_prompt)

        if not target:
            return jsonify({
                'success': False,
                'error': 'Could not identify target section for editing'
            })

        # Create specialized system prompt for targeted editing
        section_content = target.get('full_match', target.get('text', 'N/A'))
        section_type = target.get('type', 'unknown')

        system_prompt = f"""
        You are an expert web developer specializing in precise, high-quality code modifications.

        TASK: Modify the specific code section below based on the user's request.

        SECTION TO EDIT:
        Type: {section_type}
        Original Content:
        ```
        {section_content}
        ```

        USER REQUEST: {user_prompt}

        EDITING RULES:
        1. Create high-quality, modern, visually appealing code
        2. Use best practices for HTML, CSS, and JavaScript
        3. Ensure the modification is syntactically correct and functional
        4. Maintain compatibility with the existing code structure
        5. For CSS: Use modern properties, gradients, shadows, and animations when appropriate
        6. For HTML: Use semantic elements and proper structure
        7. For JavaScript: Use modern ES6+ syntax and best practices
        8. Make the code visually rich and professional

        SPECIFIC GUIDELINES BY SECTION TYPE:
        - CSS Rules: Use modern CSS features like flexbox, grid, gradients, shadows, transitions
        - HTML Elements: Ensure proper semantic structure and accessibility
        - Text Content: Make content engaging and well-formatted
        - Inline Styles: Convert to modern CSS properties with visual enhancements

        QUALITY STANDARDS:
        - Use rich color palettes and gradients
        - Add subtle animations and transitions
        - Implement modern design patterns
        - Ensure responsive design principles
        - Add visual depth with shadows and effects

        RESPONSE FORMAT:
        You must respond with ONLY a valid JSON object in this exact format:
        {{
            "success": true,
            "modified_section": "the complete modified code section with high-quality improvements",
            "change_description": "detailed description of what was changed and improved",
            "section_type": "{section_type}",
            "start_pos": {target.get('start_pos', 0)},
            "end_pos": {target.get('end_pos', 0)}
        }}

        Do not include any explanations, markdown formatting, or additional text.
        Start your response with {{ and end with }}.
        """

        # Generate the targeted modification with fallback
        response = gemini_api.generate_text(
            prompt=system_prompt,
            temperature=0.1  # Low temperature for precise edits
        )

        # If Gemini fails, try Groq as fallback
        if response is None:
            logger.warning("Gemini API failed for targeted edit, trying Groq fallback")
            try:
                from app.utils.groq_api import groq_api
                response = groq_api.generate_text(
                    prompt=system_prompt,
                    temperature=0.1
                )
                if response:
                    logger.info("Successfully used Groq fallback for targeted edit")
                else:
                    logger.error("Groq fallback also returned None response")
            except Exception as e:
                logger.error(f"Groq fallback failed: {str(e)}")

        if response is None:
            logger.error("Both Gemini and Groq APIs returned None response for targeted edit")
            return jsonify({
                'success': False,
                'error': 'API returned empty response'
            })

        # Parse the JSON response
        try:
            # Clean the response to extract JSON
            cleaned_response = response.strip()

            # Look for JSON content between { and }
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}')

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_content = cleaned_response[start_idx:end_idx + 1]
                edit_result = json.loads(json_content)

                # Validate the response structure
                if not isinstance(edit_result.get('modified_section'), str):
                    raise ValueError("Invalid modified_section in response")

                # Apply the edit to the original code
                logger.info(f"Applying edit to section: {target.get('type')} at position {target.get('start_pos')}-{target.get('end_pos')}")
                logger.info(f"Original code length: {len(current_code)}")
                logger.info(f"Modified section: {edit_result['modified_section'][:100]}...")

                modified_code = apply_section_edit(
                    current_code,
                    target,
                    edit_result['modified_section']
                )

                logger.info(f"Modified code length: {len(modified_code)}")
                logger.info(f"Code changed: {modified_code != current_code}")
                logger.info("Targeted code edit completed successfully")

                return jsonify({
                    'success': True,
                    'modified_code': modified_code,
                    'original_section': target.get('full_match', target.get('text', '')),
                    'modified_section': edit_result['modified_section'],
                    'change_description': edit_result.get('change_description', 'Code section modified'),
                    'section_type': edit_result.get('section_type', target.get('type')),
                    'edit_position': {
                        'start': target.get('start_pos', 0),
                        'end': target.get('end_pos', 0)
                    }
                })

            else:
                raise ValueError("No valid JSON found in response")

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse edit response: {str(e)}")

            # Fallback: try to extract the modification directly
            fallback_result = handle_edit_fallback(current_code, target, user_prompt, response)
            if fallback_result:
                return jsonify(fallback_result)

            return jsonify({
                'success': False,
                'error': f'Failed to parse edit response: {str(e)}'
            })

    except Exception as e:
        logger.error(f"Error in targeted code editing: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

def apply_section_edit(original_code, target_section, modified_section):
    """
    Apply the modified section to the original code with proper formatting.

    Args:
        original_code (str): The complete original code
        target_section (dict): The target section metadata
        modified_section (str): The new content for the section

    Returns:
        str: The code with the section replaced and properly formatted
    """
    logger.info(f"apply_section_edit called")
    logger.info(f"Target section type: {target_section.get('type')}")
    logger.info(f"Start pos: {target_section.get('start_pos')}, End pos: {target_section.get('end_pos')}")
    logger.info(f"Original code length: {len(original_code)}")
    logger.info(f"Modified section length: {len(modified_section)}")

    start_pos = target_section.get('start_pos', 0)
    end_pos = target_section.get('end_pos', len(original_code))

    # Log the original section being replaced
    original_section = original_code[start_pos:end_pos]
    logger.info(f"Original section being replaced: {original_section[:100]}...")
    logger.info(f"New section to insert: {modified_section[:100]}...")

    # Clean and format the modified section
    cleaned_modified_section = modified_section.strip()

    # For CSS rules, ensure proper indentation and formatting
    if target_section.get('type') == 'css_rule':
        logger.info("Applying CSS rule formatting...")
        # Add proper indentation for CSS rules
        lines = cleaned_modified_section.split('\n')
        indented_lines = []
        for line in lines:
            if line.strip():
                # Add 8 spaces for proper CSS indentation within <style> tags
                indented_lines.append('        ' + line.strip())
            else:
                indented_lines.append('')
        cleaned_modified_section = '\n'.join(indented_lines)
        logger.info(f"Formatted CSS section: {cleaned_modified_section[:100]}...")

    # Replace the section in the original code
    logger.info("Assembling modified code...")
    modified_code = (
        original_code[:start_pos] +
        cleaned_modified_section +
        original_code[end_pos:]
    )

    logger.info(f"Modified code assembled. Length: {len(modified_code)}")
    logger.info(f"Code actually changed: {modified_code != original_code}")

    # Validate the resulting code structure
    if not is_valid_html_structure(modified_code):
        logger.warning("Generated code may have structural issues")
        # Try to fix common issues
        modified_code = fix_html_structure(modified_code)
        logger.info("Applied HTML structure fixes")

    logger.info("apply_section_edit completed successfully")
    return modified_code

def is_valid_html_structure(code):
    """
    Basic validation to check if the HTML structure is intact.

    Args:
        code (str): The HTML code to validate

    Returns:
        bool: True if structure appears valid
    """
    # Check for basic HTML structure
    has_html_tag = '<html' in code.lower()
    has_head_tag = '<head' in code.lower()
    has_body_tag = '<body' in code.lower()

    # Check for balanced style tags
    style_open_count = code.lower().count('<style')
    style_close_count = code.lower().count('</style>')

    return (has_html_tag and has_head_tag and has_body_tag and
            style_open_count == style_close_count)

def fix_html_structure(code):
    """
    Attempt to fix common HTML structure issues.

    Args:
        code (str): The potentially malformed HTML code

    Returns:
        str: Fixed HTML code
    """
    # This is a basic fix - could be enhanced further
    fixed_code = code

    # Ensure DOCTYPE is present
    if not fixed_code.strip().lower().startswith('<!doctype'):
        fixed_code = '<!DOCTYPE html>\n' + fixed_code

    # Basic structure validation and fixes could be added here

    return fixed_code

def handle_edit_fallback(original_code, target_section, user_prompt, ai_response):
    """
    Fallback handler when JSON parsing fails.

    Args:
        original_code (str): The complete original code
        target_section (dict): The target section metadata
        user_prompt (str): User's editing request
        ai_response (str): Raw AI response

    Returns:
        dict: Fallback edit result or None
    """
    try:
        # Simple fallback: use the AI response as the modified section
        # This is a basic implementation - could be enhanced

        original_section = target_section.get('full_match', target_section.get('text', ''))

        # If the response looks like code, use it
        if '<' in ai_response or '{' in ai_response or ai_response.strip().startswith(('function', 'var', 'const', 'let')):
            modified_code = apply_section_edit(original_code, target_section, ai_response.strip())

            return {
                'success': True,
                'modified_code': modified_code,
                'original_section': original_section,
                'modified_section': ai_response.strip(),
                'change_description': f'Applied edit based on: {user_prompt}',
                'section_type': target_section.get('type', 'unknown'),
                'edit_position': {
                    'start': target_section.get('start_pos', 0),
                    'end': target_section.get('end_pos', 0)
                },
                'fallback_used': True
            }

    except Exception as e:
        logger.error(f"Fallback edit handler failed: {str(e)}")

    return None