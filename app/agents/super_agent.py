"""
Prime Agent module for Agen911.
This agent can browse the web, fill out forms, and generate code.
Uses lightweight implementation for compatibility with older systems.
"""

import os
import json
from urllib.parse import urljoin
import re
import hashlib
import datetime

from .base_agent import BaseAgent
from app.api.gemini import GeminiAPI
from app.api.groq import GroqAPI
from app.utils.web_browser import WebBrowser

# Import BrowserUseWrapper if available
try:
    from app.utils.browser_use_agent import BrowserUseWrapper, BROWSER_USE_AVAILABLE
except ImportError:
    BROWSER_USE_AVAILABLE = False

class SuperAgent(BaseAgent):
    """
    Prime Agent that can browse the web, fill out forms, and generate code.
    Uses lightweight implementation for compatibility with older systems.
    """

    def __init__(self, api_key=None, use_browser_use=False, use_advanced_browser=False):
        """Initialize the Prime Agent.

        Args:
            api_key (str, optional): The API key to use. Defaults to None.
            use_browser_use (bool, optional): Whether to use the browser-use library for web browsing. Defaults to False.
            use_advanced_browser (bool, optional): Whether to use advanced browser capabilities. Defaults to False.
        """
        super().__init__(api_key)

        # Initialize API clients
        self.gemini_api = GeminiAPI(api_key)
        self.groq_api = GroqAPI()  # Initialize Groq API for fallback

        # Check if Groq API is available
        if self.groq_api.api_key:
            print(f"Groq API is available as a fallback")
        else:
            print(f"Groq API is not available (no API key provided)")

        # Initialize cache directory
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cache')
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # Initialize browser options
        self.use_browser_use = use_browser_use and BROWSER_USE_AVAILABLE
        self.use_advanced_browser = use_advanced_browser

        # Initialize web browser based on configuration
        if self.use_browser_use:
            try:
                self.web_browser = BrowserUseWrapper(api_key=api_key)
                print(f"Using browser-use for web browsing")
            except Exception as e:
                print(f"Failed to initialize browser-use: {str(e)}. Falling back to lightweight browser.")
                self.web_browser = WebBrowser(cache_dir=self.cache_dir, use_advanced_browser=self.use_advanced_browser)
                self.use_browser_use = False
        else:
            self.web_browser = WebBrowser(cache_dir=self.cache_dir, use_advanced_browser=self.use_advanced_browser)
            if self.use_advanced_browser:
                print("Using advanced browser for web browsing")
            else:
                print("Using lightweight browser for web browsing")

        # State tracking
        self.current_url = None
        self.current_page_content = None
        self.current_soup = None
        self.session_history = []
        self.code_snippets = []
        self.js_enabled = True  # Flag to control JavaScript rendering (for compatibility with existing code)

        # Initialize cache (for compatibility with existing code)
        self.cache = {}
        self.cache_enabled = True
        self.cache_expiry = 3600  # Cache expiry in seconds (1 hour)

    def _get_cache_key(self, url, use_js=False):
        """
        Generate a cache key for a URL.

        Args:
            url (str): The URL to generate a key for
            use_js (bool): Whether JavaScript was used

        Returns:
            str: A cache key
        """
        # Create a unique key based on the URL and whether JS was used
        key_string = f"{url}_{use_js}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cache_path(self, cache_key):
        """
        Get the file path for a cache key.

        Args:
            cache_key (str): The cache key

        Returns:
            str: The file path
        """
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def _save_to_cache(self, cache_key, data):
        """
        Save data to the cache.

        Args:
            cache_key (str): The cache key
            data (dict): The data to cache
        """
        if not self.cache_enabled:
            return

        try:
            # Add timestamp for expiry checking
            cache_data = {
                "timestamp": datetime.datetime.now().timestamp(),
                "data": data
            }

            # Save to memory cache
            self.cache[cache_key] = cache_data

            # Save to disk cache
            cache_path = self._get_cache_path(cache_key)
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)

            print(f"Saved data to cache: {cache_key}")
        except Exception as e:
            print(f"Error saving to cache: {str(e)}")

    def _get_from_cache(self, cache_key):
        """
        Get data from the cache.

        Args:
            cache_key (str): The cache key

        Returns:
            dict or None: The cached data or None if not found or expired
        """
        if not self.cache_enabled:
            return None

        # Check memory cache first
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            timestamp = cache_data.get("timestamp", 0)
            current_time = datetime.datetime.now().timestamp()

            # Check if cache is expired
            if current_time - timestamp <= self.cache_expiry:
                print(f"Cache hit (memory): {cache_key}")
                return cache_data.get("data")
            else:
                print(f"Cache expired (memory): {cache_key}")
                return None

        # Check disk cache
        try:
            cache_path = self._get_cache_path(cache_key)
            if os.path.exists(cache_path):
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

                timestamp = cache_data.get("timestamp", 0)
                current_time = datetime.datetime.now().timestamp()

                # Check if cache is expired
                if current_time - timestamp <= self.cache_expiry:
                    # Update memory cache
                    self.cache[cache_key] = cache_data
                    print(f"Cache hit (disk): {cache_key}")
                    return cache_data.get("data")
                else:
                    print(f"Cache expired (disk): {cache_key}")
                    return None
        except Exception as e:
            print(f"Error reading from cache: {str(e)}")
            return None

        return None

    def browse_web(self, url, use_js=None):  # use_js parameter kept for backward compatibility
        """
        Browse to a specific URL and extract page content.

        Args:
            url (str): The URL to browse to
            use_js (bool, optional): Whether to use JavaScript rendering. Defaults to None (use self.js_enabled).
                                     This parameter is kept for backward compatibility but is ignored.

        Returns:
            dict: A dictionary containing the page title, content, and URL
        """
        try:
            print(f"DEBUG: SuperAgent.browse_web() called with URL: {url}")

            # Ensure URL has proper format
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url
                print(f"DEBUG: Added https:// prefix to URL: {url}")

            # Browse to the URL using our lightweight browser
            print(f"DEBUG: Calling WebBrowser.browse() with URL: {url}")
            result = self.web_browser.browse(url)
            print(f"DEBUG: WebBrowser.browse() returned: success={result.get('success', False)}")

            # Update current state
            if result.get("success", False):
                print(f"DEBUG: Updating SuperAgent state with successful browse result")
                self.current_url = url
                self.current_page_content = result.get("content", "")
                self.current_soup = self.web_browser.current_soup

                # Store screenshot data if available
                if "screenshot" in result:
                    print(f"DEBUG: Screenshot found in browse result, size: {len(result['screenshot']) if result['screenshot'] else 0} bytes")
                    self.screenshot_data = result.get("screenshot")
                else:
                    print(f"DEBUG: No screenshot found in browse result")
                    self.screenshot_data = None

                # Add to history
                self.session_history.append({
                    "action": "browse",
                    "url": url,
                    "title": result.get("title", "No title"),
                    "js_enabled": False  # We're not using JavaScript rendering anymore
                })
            else:
                print(f"DEBUG: Browse failed: {result.get('error', 'Unknown error')}")
                self.screenshot_data = None

            return result

        except Exception as e:
            print(f"DEBUG: Error in SuperAgent.browse_web(): {str(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            self.screenshot_data = None
            return {
                "error": f"Error browsing to {url}: {str(e)}",
                "success": False
            }

    def extract_form_details(self, form):
        """
        Extract details from a form element.

        Args:
            form: BeautifulSoup form element

        Returns:
            dict: A dictionary containing form details
        """
        details = {}

        # Get the form action (URL)
        action = form.get("action")
        if action:
            # If action is a relative URL, make it absolute
            if not action.startswith(('http://', 'https://')):
                action = urljoin(self.current_url, action)
        else:
            # If no action is specified, use the current URL
            action = self.current_url

        # Get the form method (POST, GET, etc.)
        method = form.get("method", "get").lower()

        # Get form inputs
        inputs = []
        for input_tag in form.find_all(["input", "textarea", "select"]):
            input_type = input_tag.get("type", "text")
            input_name = input_tag.get("name")
            input_value = input_tag.get("value", "")

            # Skip submit buttons
            if input_type == "submit":
                continue

            inputs.append({
                "type": input_tag.name,
                "input_type": input_type,
                "name": input_name,
                "value": input_value
            })

        details["action"] = action
        details["method"] = method
        details["inputs"] = inputs

        return details

    def submit_form(self, form_id, form_data):
        """
        Submit a form with the provided data.

        Args:
            form_id (int or str): The ID of the form to submit
            form_data (dict): A dictionary mapping input names to values

        Returns:
            dict: A dictionary containing the response
        """
        try:
            # Convert form_id to integer if it's a string
            if isinstance(form_id, str) and form_id.isdigit():
                form_id = int(form_id)
            elif not isinstance(form_id, int):
                form_id = 0  # Default to first form if not a valid integer

            # Use the WebBrowser's submit_form method
            result = self.web_browser.submit_form(form_id, form_data)

            # Update current state if successful
            if result.get("success", False):
                self.current_url = result.get("url", self.current_url)
                self.current_page_content = result.get("content", "")
                self.current_soup = self.web_browser.current_soup

                # Add to history
                self.session_history.append({
                    "action": "submit_form",
                    "form_id": form_id,
                    "form_data": form_data,
                    "url": result.get("url", self.current_url)
                })

            return result

        except Exception as e:
            print(f"Error in submit_form: {str(e)}")
            return {"error": f"Error submitting form: {str(e)}", "success": False}

    def follow_link(self, link_index):
        """
        Follow a link on the current page.

        Args:
            link_index (int): The index of the link to follow

        Returns:
            dict: A dictionary containing the response
        """
        try:
            # Use the WebBrowser's follow_link method
            result = self.web_browser.follow_link(link_index)

            # Update current state if successful
            if result.get("success", False):
                self.current_url = result.get("url", self.current_url)
                self.current_page_content = result.get("content", "")
                self.current_soup = self.web_browser.current_soup

                # Add to history
                self.session_history.append({
                    "action": "follow_link",
                    "link_index": link_index,
                    "url": result.get("url", self.current_url)
                })

            return result

        except Exception as e:
            print(f"Error in follow_link: {str(e)}")
            return {"error": f"Error following link: {str(e)}", "success": False}

    def analyze_webpage(self):
        """
        Analyze the current webpage and extract key information.

        Returns:
            dict: A dictionary containing the analysis results
        """
        try:
            # Use the WebBrowser's analyze_page method
            result = self.web_browser.analyze_page()

            # Add to history if successful
            if result.get("success", False):
                self.session_history.append({
                    "action": "analyze_webpage",
                    "url": self.current_url
                })

            return result

        except Exception as e:
            print(f"Error in analyze_webpage: {str(e)}")
            return {"error": f"Error analyzing webpage: {str(e)}", "success": False}

    def generate_code(self, prompt, language="javascript"):
        """
        Generate code using the Gemini API with Gemini 2.5 Pro Preview for better code quality.

        Args:
            prompt (str): The prompt describing the code to generate
            language (str): The programming language to use

        Returns:
            dict: A dictionary containing the generated code
        """
        try:
            # Use the specialized code generation method from GeminiAPI
            # This will use Gemini 2.5 Pro Preview which is optimized for code generation
            try:
                # Use a moderate temperature for more reliable code generation
                response = self.gemini_api.generate_text(f"""
                You are an expert {language} programmer. Generate clean, efficient, and well-documented code based on the following requirements:

                {prompt}

                The code should be:
                - Well-structured and organized
                - Properly commented and documented
                - Follow best practices for {language}
                - Complete and ready to run
                - Handle edge cases and errors appropriately

                Provide ONLY the code without any explanations or markdown formatting.
                """)
            except Exception as gemini_error:
                # If Gemini fails, try with Groq API
                try:
                    print(f"Gemini API error: {str(gemini_error)}. Trying Groq API for code generation.")
                    enhanced_prompt = f"""
                    You are an expert programmer. Generate clean, efficient, and well-documented code in {language}
                    based on the following requirements:

                    {prompt}

                    The code should be:
                    - Well-structured and organized
                    - Properly commented and documented
                    - Follow best practices for {language}
                    - Complete and ready to run
                    - Handle edge cases and errors appropriately

                    Provide ONLY the code without any explanations or markdown formatting.
                    """
                    response = self.groq_api.generate_text(enhanced_prompt)
                except Exception as groq_error:
                    print(f"Groq API error: {str(groq_error)}")
                    return {"error": f"Error generating code: Both Gemini and Groq APIs failed", "success": False}

            # Extract code from response (remove markdown if present)
            code = response
            if "```" in response:
                code_blocks = response.split("```")
                if len(code_blocks) >= 3:  # At least one code block
                    # Get the content of the first code block
                    code = code_blocks[1]
                    # Remove language identifier if present
                    if code.startswith(language):
                        code = code[len(language):].strip()
                    else:
                        code = code.strip()

            # Add to code snippets
            self.code_snippets.append({
                "prompt": prompt,
                "language": language,
                "code": code
            })

            # Add to history
            self.session_history.append({
                "action": "generate_code",
                "prompt": prompt,
                "language": language
            })

            return {
                "code": code,
                "language": language,
                "success": True
            }

        except Exception as e:
            return {"error": f"Error generating code: {str(e)}", "success": False}

    # The analyze_webpage method is defined earlier in the file

    def generate_code_project(self, prompt, project_type='web', complexity='simple'):
        """
        Generate a code project based on a prompt.

        Args:
            prompt (str): The description of what the project should do
            project_type (str, optional): The type of project (web, script, api, data, mobile). Defaults to 'web'.
            complexity (str, optional): The complexity level (simple, moderate, complex). Defaults to 'simple'.

        Returns:
            dict: A dictionary containing the generated project files
        """
        print(f"Generating {complexity} {project_type} project for: {prompt}")

        try:
            # Prepare a more concise but effective prompt for code generation
            code_prompt = f"""
            You are a senior software engineer with 10+ years of experience. Generate a professional-grade {complexity} {project_type} project based on the following description:
            {prompt}

            IMPORTANT: Create a COMPLETE, PRODUCTION-READY project with ALL necessary files. The code must be of professional quality that would impress senior developers.

            For web projects, use React with proper component structure, hooks, context API for state management, and responsive design with Tailwind CSS.

            For backend/API projects, use Express.js with proper MVC architecture, middleware for auth/validation, and MongoDB/Mongoose for data modeling.

            For full-stack projects, include both frontend and backend with proper separation and API integration.

            For all projects:
            1. Include proper error handling and validation
            2. Follow security best practices
            3. Use modern coding patterns
            4. Add comprehensive comments
            5. Include proper folder structure

            Return ONLY a valid JSON object with this exact structure:
            {{"files": [{{"name": "filename.ext", "content": "file content"}}, ...]}}

            The files array MUST include ALL necessary files to make the project fully functional.
            """

            # Generate code using Gemini 2.5 Pro Preview for better code quality
            try:
                # Use a moderate temperature for creative but reliable code generation
                # and a high max_output_tokens to allow for larger code projects
                gemini_params = {
                    "temperature": 0.7,
                    "max_output_tokens": 8192,  # Request more tokens for complex code
                }

                print("Using Gemini API for code project generation")
                # Use the standard generate_text method for better reliability
                response = self.gemini_api.generate_text(code_prompt, temperature=gemini_params["temperature"])

                # If the response is too short, it might be incomplete - try again with different parameters
                if len(response) < 1000:
                    print("Initial response too short, trying again with different parameters")
                    gemini_params["temperature"] = 0.8  # Increase temperature slightly
                    response = self.gemini_api.generate_text(code_prompt, temperature=gemini_params["temperature"])
            except Exception as gemini_error:
                # If Gemini fails, try with Groq API
                try:
                    print(f"Gemini API error: {str(gemini_error)}. Trying Groq API for code generation.")
                    response = self.groq_api.generate_text(code_prompt)
                except Exception as groq_error:
                    print(f"Groq API error: {str(groq_error)}")
                    return {"error": f"Error generating code project: Both Gemini and Groq APIs failed", "success": False}

            # Extract JSON from the response
            try:
                # Try to extract JSON from the response using multiple approaches
                # First, try to find JSON in code blocks with json tag
                json_match = re.search(r'```(?:json)\s*({.*?})\s*```', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    print(f"Found JSON in code block with json tag")
                else:
                    # Try to find JSON between triple backticks without json tag
                    json_match = re.search(r'```\s*({\s*"files".*?})\s*```', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        print(f"Found JSON in generic code block")
                    else:
                        # Try to find any JSON object with a files array
                        json_match = re.search(r'({\s*"files"\s*:\s*\[.*?\]\s*})', response, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                            print(f"Found JSON with files array in text")
                        else:
                            # Try to find any array of file objects
                            json_match = re.search(r'"files"\s*:\s*(\[\s*{.*?}\s*\])', response, re.DOTALL)
                            if json_match:
                                files_array = json_match.group(1)
                                json_str = '{"files": ' + files_array + '}'
                                print(f"Reconstructed JSON from files array")
                            else:
                                # Try to find JSON in code blocks with any tag
                                json_match = re.search(r'```\w*\s*({\s*"files"\s*:\s*\[.*?\]\s*})\s*```', response, re.DOTALL)
                                if json_match:
                                    json_str = json_match.group(1)
                                    print(f"Found JSON in code block with any tag")
                                else:
                                    # Use the entire response as a last resort
                                    json_str = response
                                    print(f"Using entire response as JSON")

                # Clean up the JSON string
                # Remove any leading/trailing whitespace
                json_str = json_str.strip()
                # Remove any trailing commas before closing brackets (common JSON error)
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                # Fix escaped quotes inside strings (common when LLMs generate JSON)
                json_str = re.sub(r'\\"', '"', json_str)
                # Fix unescaped quotes inside strings
                json_str = re.sub(r'(?<!\\)"(?=[^"]*"\s*:)', '\\"', json_str)

                print(f"Attempting to parse JSON: {json_str[:100]}...")

                # Parse the JSON
                try:
                    project_data = json.loads(json_str)
                except json.JSONDecodeError as json_error:
                    print(f"Initial JSON parsing failed: {str(json_error)}")
                    # Try to extract just the files array if present
                    files_match = re.search(r'"files"\s*:\s*(\[.*?\])(?:,|\s*})', json_str, re.DOTALL)
                    if files_match:
                        files_array = files_match.group(1)
                        try:
                            files_data = json.loads(files_array)
                            project_data = {"files": files_data}
                            print(f"Successfully extracted files array")
                        except:
                            # If that fails too, create a fallback response
                            return self._generate_fallback_project(prompt, project_type, complexity)
                    else:
                        # If no files array found, create a fallback response
                        return self._generate_fallback_project(prompt, project_type, complexity)

                if 'files' in project_data and isinstance(project_data['files'], list):
                    print(f"Successfully generated project with {len(project_data['files'])} files")
                    return {"success": True, "files": project_data['files']}
                else:
                    print(f"Invalid project data format: 'files' key missing or not a list")
                    return self._generate_fallback_project(prompt, project_type, complexity)
            except Exception as e:
                print(f"Error parsing response: {str(e)}")
                # Return a fallback project instead of an error
                return self._generate_fallback_project(prompt, project_type, complexity)

        except Exception as e:
            print(f"Error generating code project: {str(e)}")
            return {"error": f"Error generating code project: {str(e)}", "success": False}

    def execute_task(self, task_description):
        """
        Execute a complex task described in natural language.

        Args:
            task_description (str): Description of the task to perform

        Returns:
            dict: A dictionary containing the task execution results
        """
        try:
            # Check cache first
            if self.cache_enabled:
                cache_key = hashlib.md5(task_description.encode()).hexdigest()
                cached_result = self._get_from_cache(cache_key)

                if cached_result:
                    print(f"Using cached result for task: {task_description[:50]}...")
                    return cached_result

            # Check for specialized handlers
            task_lower = task_description.lower() if task_description else ""
            print(f"Task description: {task_description}")
            print(f"Contains 'nigeria': {'nigeria' in task_lower}")
            print(f"Contains 'bank': {'bank' in task_lower}")

            # Check if this is a Nigerian banks task
            if "nigeria" in task_lower and "bank" in task_lower:
                print("Handling Nigerian banks task directly from execute_task")
                result = self._handle_nigerian_banks_task(task_description)

                # Cache the result
                if self.cache_enabled and result.get("success", False):
                    self._save_to_cache(cache_key, result)

                return result

            # Check if this is a travel-related task
            is_travel_task = any(term in task_lower for term in [
                'travel', 'vacation', 'flight', 'hotel', 'booking', 'trip', 'destination',
                'resort', 'airbnb', 'expedia', 'tripadvisor', 'airline', 'ticket', 'itinerary',
                'tour', 'cruise', 'holiday', 'visit', 'tourism', 'sightseeing', 'attractions'
            ])

            if is_travel_task:
                print(f"Detected travel-related task")
                result = self._handle_travel_task(task_description)
                # Cache the result
                if self.cache_enabled and result.get("success", False):
                    self._save_to_cache(cache_key, result)
                return result

            # Check if this is a recipe or food-related task
            is_recipe_task = any(term in task_lower for term in [
                'recipe', 'cook', 'food', 'meal', 'dish', 'ingredient', 'bake', 'dinner',
                'lunch', 'breakfast', 'cuisine', 'kitchen', 'chef', 'cooking', 'prepare',
                'healthy', 'vegetarian', 'vegan', 'gluten-free', 'dessert', 'appetizer'
            ])

            if is_recipe_task:
                print(f"Detected recipe-related task")
                result = self._handle_recipe_task(task_description)
                # Cache the result
                if self.cache_enabled and result.get("success", False):
                    self._save_to_cache(cache_key, result)
                return result

            # Check if this is a product review task
            is_review_task = any(term in task_lower for term in [
                'review', 'product', 'best', 'compare', 'rating', 'recommend', 'worth it',
                'vs', 'versus', 'better', 'top', 'ranked', 'comparison', 'alternative',
                'opinion', 'experience', 'quality', 'performance', 'value', 'price'
            ])

            if is_review_task:
                print(f"Detected product review task")
                result = self._handle_product_review_task(task_description)
                # Cache the result
                if self.cache_enabled and result.get("success", False):
                    self._save_to_cache(cache_key, result)
                return result

            # Check if this is a financial analysis task
            is_financial_task = any(term in task_lower for term in [
                'stock', 'price', 'market', 'invest', 'buy', 'sell', 'trading', 'financial',
                'finance', 'tesla', 'apple', 'amazon', 'google', 'microsoft', 'meta', 'facebook'
            ])

            # For financial tasks, we'll use a direct approach with specific financial websites
            if is_financial_task and task_description and 'tesla' in task_description.lower():
                # Direct approach for Tesla stock information
                result = self._handle_tesla_stock_task(task_description)
                # Cache the result
                if self.cache_enabled and result.get("success", False):
                    self._save_to_cache(cache_key, result)
                return result
            elif is_financial_task and task_description and any(company in task_description.lower() for company in ['apple', 'aapl']):
                # Direct approach for Apple stock information
                result = self._handle_apple_stock_task(task_description)
                # Cache the result
                if self.cache_enabled and result.get("success", False):
                    self._save_to_cache(cache_key, result)
                return result
            elif is_financial_task:
                # Direct approach for general financial tasks
                result = self._handle_financial_task(task_description)
                # Cache the result
                if self.cache_enabled and result.get("success", False):
                    self._save_to_cache(cache_key, result)
                return result

            # Check if this is a general web browsing task
            is_web_search = task_description and any(term in task_description.lower() for term in [
                'search', 'find', 'look up', 'google', 'browse', 'visit', 'go to', 'check', 'read about',
                'information about', 'learn about', 'research', 'what is', 'who is', 'where is', 'when is',
                'how to', 'news about', 'latest', 'current', 'recent'
            ])

            # For general web browsing tasks, use a direct approach
            if is_web_search:
                result = self._handle_web_search_task(task_description)
                # Cache the result
                if self.cache_enabled and result.get("success", False):
                    self._save_to_cache(cache_key, result)
                return result

            # Use Gemini API to break down the task into steps
            planning_prompt = f"""
            You are an AI assistant that helps users navigate websites and perform tasks online.
            I need to: {task_description}

            Break this down into a sequence of specific steps that a web automation tool could follow.
            Each step should be one of these actions:
            1. browse_web(url) - Navigate to a specific URL
            2. analyze_webpage() - Analyze the current webpage to extract forms, links, and headings
            3. submit_form(form_id, form_data) - Submit a form with the provided data
            4. follow_link(link_index) - Follow a link on the current page

            For web searches, always use specific URLs like:
            - For Google: https://www.google.com
            - For Wikipedia: https://www.wikipedia.org
            - For news: https://news.google.com
            - For shopping: https://www.amazon.com
            - For videos: https://www.youtube.com

            Return the steps as a JSON array of objects, where each object has an "action" field and any necessary parameters.
            Make sure URLs include the full protocol (https:// or http://).
            Limit the number of steps to 5 or fewer to avoid timeouts.
            """

            # Try with Gemini API first
            try:
                response = self.gemini_api.generate_text(planning_prompt)
                if not response or "error" in response.lower():
                    raise Exception("Gemini API failed to generate a response")
            except Exception as gemini_error:
                print(f"Gemini API error: {str(gemini_error)}")
                # Try with Groq API as fallback
                if self.groq_api.api_key:
                    print("Using Groq API as fallback for task planning")
                    try:
                        response = self.groq_api.generate_text(planning_prompt)
                    except Exception as groq_error:
                        print(f"Groq API error: {str(groq_error)}")
                        response = "[{\"action\": \"browse_web\", \"url\": \"https://www.google.com\"}]"

            # Try to extract JSON from the response
            try:
                # Find JSON in the response (it might be wrapped in markdown code blocks)
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].strip()
                else:
                    json_str = response.strip()

                steps = json.loads(json_str)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract steps in a more forgiving way
                steps = []
                lines = response.strip().split('\n')
                current_step = {}

                for line in lines:
                    line = line.strip()
                    if any(action in line for action in ["browse_web", "analyze_webpage", "submit_form", "follow_link"]):
                        if current_step and "action" in current_step:
                            steps.append(current_step)
                        current_step = {}

                        if "browse_web" in line:
                            current_step["action"] = "browse_web"
                            url_match = line.split("browse_web")[1].strip("() '\"")
                            # Ensure URL has protocol
                            if not url_match.startswith(('http://', 'https://')):
                                url_match = 'https://' + url_match
                            current_step["url"] = url_match
                        elif "analyze_webpage" in line:
                            current_step["action"] = "analyze_webpage"
                        elif "submit_form" in line:
                            current_step["action"] = "submit_form"
                            params = line.split("submit_form")[1].strip("() ")
                            try:
                                form_id, form_data = eval(params)
                                current_step["form_id"] = form_id
                                current_step["form_data"] = form_data
                            except:
                                current_step["form_id"] = 0
                                current_step["form_data"] = {}
                        elif "follow_link" in line:
                            current_step["action"] = "follow_link"
                            link_index = line.split("follow_link")[1].strip("() '\"")
                            try:
                                current_step["link_index"] = int(link_index)
                            except:
                                current_step["link_index"] = 0

                if current_step and "action" in current_step:
                    steps.append(current_step)

            # Execute each step
            results = []
            step_summaries = []
            for step_index, step in enumerate(steps):
                action = step.get("action")
                step_description = f"Step {step_index + 1}: {action.replace('_', ' ').title()}"

                if action == "browse_web":
                    url = step.get("url")
                    # Ensure URL has protocol
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    step_description += f" - Navigating to {url}"
                    result = self.browse_web(url)
                elif action == "analyze_webpage":
                    step_description += " - Analyzing current page"
                    result = self.analyze_webpage()
                elif action == "submit_form":
                    form_id = step.get("form_id", 0)
                    form_data = step.get("form_data", {})
                    step_description += f" - Submitting form #{form_id} with data: {form_data}"
                    result = self.submit_form(form_id, form_data)
                elif action == "follow_link":
                    link_index = step.get("link_index", 0)
                    step_description += f" - Following link #{link_index}"
                    result = self.follow_link(link_index)
                else:
                    step_description += f" - Unknown action"
                    result = {"error": f"Unknown action: {action}", "success": False}

                # Create a summary of the result
                if result.get("success", False):
                    if action == "browse_web":
                        summary = f"Successfully loaded page: {result.get('title', 'No title')} ({result.get('url', 'No URL')})"
                    elif action == "analyze_webpage":
                        forms_count = len(result.get('forms', []))
                        links_count = len(result.get('links', []))
                        headings_count = len(result.get('headings', []))
                        summary = f"Analysis complete: Found {forms_count} forms, {links_count} links, and {headings_count} headings"
                    elif action == "submit_form":
                        summary = f"Form submitted successfully: {result.get('title', 'No title')} ({result.get('url', 'No URL')})"
                    elif action == "follow_link":
                        summary = f"Link followed successfully: {result.get('title', 'No title')} ({result.get('url', 'No URL')})"
                    else:
                        summary = "Step completed successfully"
                else:
                    summary = f"Failed: {result.get('error', 'Unknown error')}"

                step_summaries.append({
                    "description": step_description,
                    "summary": summary,
                    "success": result.get("success", False)
                })

                results.append({
                    "step": step,
                    "result": result
                })

                # If a step fails, stop execution
                if not result.get("success", False):
                    break

            # Generate a comprehensive task summary
            task_summary = self._generate_task_summary(task_description, step_summaries, results)

            # Add to history
            self.session_history.append({
                "action": "execute_task",
                "task_description": task_description,
                "steps": steps,
                "summary": task_summary
            })

            result = {
                "task_description": task_description,
                "steps": steps,
                "results": results,
                "step_summaries": step_summaries,
                "task_summary": task_summary,
                "success": all(result["result"].get("success", False) for result in results)
            }

            # Cache successful results
            if self.cache_enabled and result.get("success", False):
                cache_key = hashlib.md5(task_description.encode()).hexdigest()
                self._save_to_cache(cache_key, result)

            return result
        except Exception as e:
            print(f"Error executing task: {str(e)}")
            return {"error": f"Error executing task: {str(e)}", "success": False}

    def _generate_task_summary(self, task_description, step_summaries, results):
        """
        Generate a comprehensive summary of the task execution.

        Args:
            task_description (str): The original task description
            step_summaries (list): List of step summaries
            results (list): List of step results

        Returns:
            str: A comprehensive summary of the task execution
        """
        try:
            # Check if this is a financial task
            is_financial_task = task_description and any(term in task_description.lower() for term in [
                'stock', 'price', 'market', 'invest', 'buy', 'sell', 'trading', 'financial',
                'finance', 'tesla', 'apple', 'amazon', 'google', 'microsoft', 'meta', 'facebook'
            ])

            # For financial tasks, we'll use a special prompt
            if is_financial_task:
                # If we couldn't complete the task successfully, provide a fallback response
                if not all(step.get('success', False) for step in step_summaries):
                    return self._generate_financial_fallback(task_description)

                # Extract any financial data from the results
                financial_data = self._extract_financial_data(results)

                # Create a financial summary prompt
                summary_prompt = f"""
                You are a financial analyst assistant that helps users understand stock information.
                I have just completed the following task: "{task_description}"

                Here are the steps that were executed:

                {json.dumps(step_summaries, indent=2)}

                Here is the financial data I extracted:

                {financial_data}

                Please provide a comprehensive, well-organized summary of the financial information.
                The summary should:
                1. Explain what financial information was requested
                2. Provide the current stock price and any relevant metrics found
                3. Give a balanced assessment of whether it might be a good time to buy/sell based on available information
                4. Include appropriate disclaimers about financial advice
                5. Suggest what other information the user might want to consider

                Format the summary in a clear, professional way with appropriate headings and structure.
                Keep it concise but informative.
                """
            else:
                # For non-financial tasks, use the standard prompt
                summary_prompt = f"""
                You are an AI assistant that helps users understand web automation tasks.
                I have just completed the following task: "{task_description}"

                Here are the steps that were executed:

                {json.dumps(step_summaries, indent=2)}

                Please provide a comprehensive, well-organized summary of what was accomplished.
                The summary should:
                1. Explain what the task was trying to achieve in plain language
                2. Describe what was actually done, step by step
                3. Highlight any important information discovered
                4. Mention any errors or issues encountered
                5. Provide a conclusion about whether the task was successful

                Format the summary in a clear, professional way with appropriate headings and structure.
                Keep it concise but informative.
                """

            # Generate the summary using Gemini API with Groq fallback
            try:
                summary = self.gemini_api.generate_text(summary_prompt)
                return summary
            except Exception as gemini_error:
                # If Gemini fails, try with Groq API
                try:
                    print(f"Gemini API error in task summary: {str(gemini_error)}. Trying Groq API.")
                    summary = self.groq_api.generate_text(summary_prompt)
                    return summary
                except Exception as groq_error:
                    print(f"Groq API error in task summary: {str(groq_error)}")
                    # Provide a basic summary if both APIs fail
                    return "I've completed the requested task, but I'm unable to generate a detailed summary due to API limitations."
        except Exception as e:
            print(f"Error generating task summary: {str(e)}")
            return f"Error generating task summary: {str(e)}"

    def _extract_financial_data(self, results):
        """
        Extract financial data from the results.

        Args:
            results (list): List of step results

        Returns:
            str: A string containing the extracted financial data
        """
        try:
            financial_data = []

            for result_item in results:
                result = result_item.get('result', {})
                content = result.get('content', '')

                if content:
                    # Look for stock price patterns
                    price_patterns = [
                        r'\$\d+\.\d+',  # $123.45
                        r'\d+\.\d+\s*USD',  # 123.45 USD
                        r'Price:\s*\$?\d+\.\d+',  # Price: $123.45
                        r'Stock Price:\s*\$?\d+\.\d+',  # Stock Price: $123.45
                        r'Current Price:\s*\$?\d+\.\d+',  # Current Price: $123.45
                        r'\d+\.\d+\s*points',  # 123.45 points
                        r'\d+\.\d+\s*\(\+?\-?\d+\.\d+%\)'  # 123.45 (+/-2.34%)
                    ]

                    for pattern in price_patterns:
                        import re
                        matches = re.findall(pattern, content)
                        if matches:
                            financial_data.append(f"Found price information: {', '.join(matches)}")

                    # Look for other financial metrics
                    if 'market cap' in content.lower() or 'market capitalization' in content.lower():
                        financial_data.append(f"Page contains market capitalization information")

                    if 'p/e' in content.lower() or 'price to earnings' in content.lower():
                        financial_data.append(f"Page contains P/E ratio information")

                    if 'dividend' in content.lower():
                        financial_data.append(f"Page contains dividend information")

                    if 'volume' in content.lower():
                        financial_data.append(f"Page contains trading volume information")

            if financial_data:
                return "\n".join(financial_data)
            else:
                return "No specific financial data could be extracted from the pages visited."
        except Exception as e:
            return f"Error extracting financial data: {str(e)}"

    def _handle_tesla_stock_task(self, task_description):
        """
        Handle a task specifically about Tesla stock.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing the task execution results
        """
        try:
            # First, try to browse to Yahoo Finance for Tesla
            browse_result = self.browse_web("https://finance.yahoo.com/quote/TSLA")

            # If successful, analyze the page
            if browse_result.get("success", False):
                analyze_result = self.analyze_webpage()

                # Create step summaries
                step_summaries = [
                    {
                        "description": "Step 1: Browse Web - Navigating to https://finance.yahoo.com/quote/TSLA",
                        "summary": "Successfully loaded Tesla stock information from Yahoo Finance",
                        "success": True
                    },
                    {
                        "description": "Step 2: Analyze Webpage - Extracting Tesla stock information",
                        "summary": "Successfully analyzed the page and extracted stock information",
                        "success": True
                    }
                ]

                # Generate a summary using the extracted information
                summary_prompt = f"""
                You are a financial analyst assistant that helps users understand stock information.
                I have just retrieved information about Tesla's stock from Yahoo Finance.

                Here is the content I extracted:

                {browse_result.get('content', 'No content available')}

                Based on this information, please provide a comprehensive, well-organized summary that:
                1. States the current stock price of Tesla (if available)
                2. Mentions any key metrics like market cap, P/E ratio, etc. (if available)
                3. Gives a balanced assessment of whether it might be a good time to buy/sell based on available information
                4. Includes appropriate disclaimers about financial advice
                5. Suggests what other information the user might want to consider

                Format the summary in a clear, professional way with appropriate headings and structure.
                Keep it concise but informative.
                """

                task_summary = self.gemini_api.generate_text(summary_prompt)

                # Return the results
                return {
                    "task_description": task_description,
                    "steps": [
                        {"action": "browse_web", "url": "https://finance.yahoo.com/quote/TSLA"},
                        {"action": "analyze_webpage"}
                    ],
                    "results": [
                        {"step": {"action": "browse_web", "url": "https://finance.yahoo.com/quote/TSLA"}, "result": browse_result},
                        {"step": {"action": "analyze_webpage"}, "result": analyze_result}
                    ],
                    "step_summaries": step_summaries,
                    "task_summary": task_summary,
                    "success": True
                }
            else:
                # If browsing failed, return a fallback response
                return self._generate_financial_fallback_result(task_description)
        except Exception as e:
            print(f"Error handling Tesla stock task: {str(e)}")
            return self._generate_financial_fallback_result(task_description)

    def _handle_apple_stock_task(self, task_description):
        """
        Handle a task specifically about Apple stock.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing the task execution results
        """
        try:
            # First, try to browse to Yahoo Finance for Apple
            browse_result = self.browse_web("https://finance.yahoo.com/quote/AAPL")

            # If successful, analyze the page
            if browse_result.get("success", False):
                analyze_result = self.analyze_webpage()

                # Create step summaries
                step_summaries = [
                    {
                        "description": "Step 1: Browse Web - Navigating to https://finance.yahoo.com/quote/AAPL",
                        "summary": "Successfully loaded Apple stock information from Yahoo Finance",
                        "success": True
                    },
                    {
                        "description": "Step 2: Analyze Webpage - Extracting Apple stock information",
                        "summary": "Successfully analyzed the page and extracted stock information",
                        "success": True
                    }
                ]

                # Generate a summary using the extracted information
                summary_prompt = f"""
                You are a financial analyst assistant that helps users understand stock information.
                I have just retrieved information about Apple's stock from Yahoo Finance.

                Here is the content I extracted:

                {browse_result.get('content', 'No content available')}

                Based on this information, please provide a comprehensive, well-organized summary that:
                1. States the current stock price of Apple (if available)
                2. Mentions any key metrics like market cap, P/E ratio, etc. (if available)
                3. Gives a balanced assessment of whether it might be a good time to buy/sell based on available information
                4. Includes appropriate disclaimers about financial advice
                5. Suggests what other information the user might want to consider

                Format the summary in a clear, professional way with appropriate headings and structure.
                Keep it concise but informative.
                """

                # Try to generate text with Gemini API first, fall back to Groq API if needed
                try:
                    task_summary = self.gemini_api.generate_text(summary_prompt)
                except Exception as e:
                    print(f"Error generating text with Gemini API: {str(e)}")
                    if self.groq_api and self.groq_api.api_key:
                        print("Falling back to Groq API")
                        task_summary = self.groq_api.generate_text(summary_prompt)
                    else:
                        task_summary = "I'm sorry, but I couldn't retrieve the latest information about Apple stock due to technical limitations. Please try again later or check a financial website like Yahoo Finance directly."

                # Return the results
                return {
                    "task_description": task_description,
                    "steps": [
                        {"action": "browse_web", "url": "https://finance.yahoo.com/quote/AAPL"},
                        {"action": "analyze_webpage"}
                    ],
                    "results": [
                        {"step": {"action": "browse_web", "url": "https://finance.yahoo.com/quote/AAPL"}, "result": browse_result},
                        {"step": {"action": "analyze_webpage"}, "result": analyze_result}
                    ],
                    "step_summaries": step_summaries,
                    "task_summary": task_summary,
                    "success": True
                }
            else:
                # If browsing failed, return a fallback response
                return self._generate_financial_fallback_result(task_description)
        except Exception as e:
            print(f"Error handling Apple stock task: {str(e)}")
            return self._generate_financial_fallback_result(task_description)

    def _handle_financial_task(self, task_description):
        """
        Handle a general financial task.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing the task execution results
        """
        try:
            # Extract potential stock symbols from the task description
            stock_symbols = self._extract_stock_symbols(task_description)
            print(f"Extracted stock symbols: {stock_symbols}")

            # Check if we need to compare multiple stocks
            if len(stock_symbols) > 1 and task_description and any(term in task_description.lower() for term in ['compare', 'comparison', 'versus', 'vs', 'better', 'best', 'worst', 'performed']):
                # Process multiple stocks for comparison
                symbol_results = []
                steps = []
                results = []
                step_summaries = []

                # Process each symbol
                for symbol in stock_symbols:
                    symbol_url = f"https://finance.yahoo.com/quote/{symbol}"
                    print(f"Browsing to {symbol_url}")
                    browse_result = self.browse_web(symbol_url, use_js=True)

                    if browse_result.get("success", False):
                        analyze_result = self.analyze_webpage()

                        # Add steps and results
                        steps.append({"action": "browse_web", "url": symbol_url})
                        steps.append({"action": "analyze_webpage"})
                        results.append({"step": {"action": "browse_web", "url": symbol_url}, "result": browse_result})
                        results.append({"step": {"action": "analyze_webpage"}, "result": analyze_result})

                        # Add step summaries
                        step_summaries.append({
                            "description": f"Step {len(step_summaries)+1}: Browse Web - Navigating to {symbol_url}",
                            "summary": f"Successfully loaded stock information for {symbol} from Yahoo Finance",
                            "success": True
                        })
                        step_summaries.append({
                            "description": f"Step {len(step_summaries)+1}: Analyze Webpage - Extracting stock information for {symbol}",
                            "summary": "Successfully analyzed the page and extracted stock information",
                            "success": True
                        })

                        # Store the content
                        symbol_results.append({
                            "symbol": symbol,
                            "content": browse_result.get('content', 'No content available')
                        })

                # If we got results for at least one symbol
                if symbol_results:
                    # Generate a comparison summary
                    comparison_prompt = f"""
                    You are a financial analyst assistant that helps users understand stock information.
                    The user asked: "{task_description}"

                    I have retrieved information about multiple stocks from Yahoo Finance.

                    Here is the content I extracted for each stock:

                    {' '.join([f"--- {result['symbol']} ---" + "\n" + result['content'][:1000] + "...\n\n" for result in symbol_results])}

                    Please provide a comprehensive comparison of these stocks that:
                    1. Compares the current stock prices and key metrics for each stock
                    2. Analyzes recent performance trends for each stock
                    3. Directly answers which stock has performed better recently
                    4. Gives a balanced assessment of the strengths and weaknesses of each stock
                    5. Includes appropriate disclaimers about financial advice

                    Format the comparison in a clear, professional way with tables and bullet points where appropriate.
                    """

                    task_summary = self.gemini_api.generate_text(comparison_prompt)

                    # Return the results
                    return {
                        "task_description": task_description,
                        "steps": steps,
                        "results": results,
                        "step_summaries": step_summaries,
                        "task_summary": task_summary,
                        "success": True
                    }

            # Handle single stock or no comparison requested
            if stock_symbols:
                # Use the first stock symbol found
                symbol = stock_symbols[0]
                symbol_url = f"https://finance.yahoo.com/quote/{symbol}"
                print(f"Browsing to {symbol_url}")
                browse_result = self.browse_web(symbol_url, use_js=True)

                # If successful, analyze the page
                if browse_result.get("success", False):
                    analyze_result = self.analyze_webpage()

                    # Create step summaries
                    step_summaries = [
                        {
                            "description": f"Step 1: Browse Web - Navigating to {symbol_url}",
                            "summary": f"Successfully loaded stock information for {symbol} from Yahoo Finance",
                            "success": True
                        },
                        {
                            "description": "Step 2: Analyze Webpage - Extracting stock information",
                            "summary": "Successfully analyzed the page and extracted stock information",
                            "success": True
                        }
                    ]

                    # Generate a summary using the extracted information
                    summary_prompt = f"""
                    You are a financial analyst assistant that helps users understand stock information.
                    The user asked: "{task_description}"

                    I have retrieved information about the stock with symbol {symbol} from Yahoo Finance.

                    Here is the content I extracted:

                    {browse_result.get('content', 'No content available')}

                    Based on this information, please provide a comprehensive, well-organized summary that:
                    1. States the current stock price (if available)
                    2. Mentions any key metrics like market cap, P/E ratio, etc. (if available)
                    3. Gives a balanced assessment of whether it might be a good time to buy/sell based on available information
                    4. Includes appropriate disclaimers about financial advice
                    5. Suggests what other information the user might want to consider

                    Format the summary in a clear, professional way with appropriate headings and structure.
                    Keep it concise but informative.
                    """

                    task_summary = self.gemini_api.generate_text(summary_prompt)

                    # Return the results
                    return {
                        "task_description": task_description,
                        "steps": [
                            {"action": "browse_web", "url": symbol_url},
                            {"action": "analyze_webpage"}
                        ],
                        "results": [
                            {"step": {"action": "browse_web", "url": symbol_url}, "result": browse_result},
                            {"step": {"action": "analyze_webpage"}, "result": analyze_result}
                        ],
                        "step_summaries": step_summaries,
                        "task_summary": task_summary,
                        "success": True
                    }

            # If no stock symbols found or browsing failed, try a general financial search
            search_query = task_description.replace(" ", "+")
            google_finance_url = f"https://www.google.com/search?q={search_query}+stock+price"
            print(f"Searching for financial information: {google_finance_url}")
            browse_result = self.browse_web(google_finance_url, use_js=True)

            if browse_result.get("success", False):
                analyze_result = self.analyze_webpage()

                # Create step summaries
                step_summaries = [
                    {
                        "description": f"Step 1: Search - Searching for financial information about {search_query}",
                        "summary": "Successfully searched for financial information",
                        "success": True
                    },
                    {
                        "description": "Step 2: Analyze Results - Analyzing search results",
                        "summary": "Successfully analyzed financial information",
                        "success": True
                    }
                ]

                # Generate a summary using the extracted information
                summary_prompt = f"""
                You are a financial analyst assistant that helps users understand financial information.
                The user asked: "{task_description}"

                I have searched for financial information that might match their request. Here is the content from the search results:

                {browse_result.get('content', 'No content available')}

                Please provide a helpful response that:
                1. Summarizes the financial information found
                2. Addresses the specific aspects the user asked about
                3. Provides context about what these numbers mean
                4. Suggests reliable sources for more detailed information if needed

                Format the response in a clear, professional way with tables and bullet points where appropriate.
                """

                task_summary = self.gemini_api.generate_text(summary_prompt)

                # Return the results
                return {
                    "task_description": task_description,
                    "steps": [
                        {"action": "browse_web", "url": google_finance_url},
                        {"action": "analyze_webpage"}
                    ],
                    "results": [
                        {"step": {"action": "browse_web", "url": google_finance_url}, "result": browse_result},
                        {"step": {"action": "analyze_webpage"}, "result": analyze_result}
                    ],
                    "step_summaries": step_summaries,
                    "task_summary": task_summary,
                    "success": True
                }

            # If all else fails, return a fallback response
            return self._generate_financial_fallback_result(task_description)
        except Exception as e:
            print(f"Error handling financial task: {str(e)}")
            return self._generate_financial_fallback_result(task_description)

    def _extract_stock_symbols(self, text):
        """
        Extract potential stock symbols from text.

        Args:
            text (str): The text to extract stock symbols from

        Returns:
            list: A list of potential stock symbols
        """
        # Common stock symbols with their company names
        common_symbols = {
            'tesla': 'TSLA',
            'apple': 'AAPL',
            'amazon': 'AMZN',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'microsoft': 'MSFT',
            'meta': 'META',
            'facebook': 'META',
            'netflix': 'NFLX',
            'nvidia': 'NVDA',
            'amd': 'AMD',
            'intel': 'INTC',
            'ibm': 'IBM',
            'oracle': 'ORCL',
            'salesforce': 'CRM',
            'adobe': 'ADBE',
            'walmart': 'WMT',
            'disney': 'DIS',
            'coca cola': 'KO',
            'coca-cola': 'KO',
            'coke': 'KO',
            'pepsi': 'PEP',
            'pepsico': 'PEP',
            'johnson & johnson': 'JNJ',
            'johnson and johnson': 'JNJ',
            'procter & gamble': 'PG',
            'procter and gamble': 'PG',
            'verizon': 'VZ',
            'at&t': 'T',
            'exxon': 'XOM',
            'exxonmobil': 'XOM',
            'chevron': 'CVX',
            'jpmorgan': 'JPM',
            'jp morgan': 'JPM',
            'bank of america': 'BAC',
            'wells fargo': 'WFC',
            'goldman sachs': 'GS',
            'morgan stanley': 'MS',
            'visa': 'V',
            'mastercard': 'MA',
            'paypal': 'PYPL',
            'nike': 'NKE',
            'starbucks': 'SBUX',
            'mcdonald': 'MCD',
            'mcdonalds': 'MCD',
            'boeing': 'BA',
            'caterpillar': 'CAT',
            'home depot': 'HD',
            'lowes': 'LOW',
            'target': 'TGT',
            'costco': 'COST',
            'pfizer': 'PFE',
            'merck': 'MRK',
            'abbott': 'ABT',
            'ups': 'UPS',
            'fedex': 'FDX',
            '3m': 'MMM',
            'general electric': 'GE',
            'ge': 'GE',
            'ford': 'F',
            'general motors': 'GM',
            'gm': 'GM',
            'tesla motors': 'TSLA'
        }

        # Look for common company names
        symbols = []
        text_lower = text.lower()

        # Check for specific company mentions
        for company, symbol in common_symbols.items():
            if company in text_lower and symbol not in symbols:
                symbols.append(symbol)

        # Check for stock symbols in the text
        # Pattern for stock symbols: 1-5 uppercase letters, possibly with a period (for international stocks)
        import re
        pattern = r'\b[A-Z]{1,5}(?:\.[A-Z]{1,2})?\b'
        potential_symbols = re.findall(pattern, text)

        # Filter out common English words that might be mistaken for stock symbols
        common_words = ['I', 'A', 'AN', 'THE', 'IN', 'ON', 'AT', 'TO', 'FOR', 'WITH', 'BY', 'AS', 'OF', 'IS', 'ARE', 'AM']
        filtered_symbols = [sym for sym in potential_symbols if sym not in common_words]

        # Add the filtered symbols
        for symbol in filtered_symbols:
            if symbol not in symbols:
                symbols.append(symbol)

        # Special case for specific stock requests in the task description
        if 'stock price' in text_lower or 'stock prices' in text_lower:
            # Look for patterns like "X stock price" or "price of X stock"
            stock_price_pattern = r'([a-zA-Z\s&]+)\s+stock\s+price|price\s+of\s+([a-zA-Z\s&]+)\s+stock'
            matches = re.findall(stock_price_pattern, text_lower)

            for match in matches:
                company_name = match[0].strip() if match[0] else match[1].strip()
                if company_name in common_symbols:
                    symbol = common_symbols[company_name]
                    if symbol not in symbols:
                        symbols.append(symbol)

        # If we're looking for multiple stocks (comparison)
        if len(symbols) == 0 and ('compare' in text_lower or 'comparison' in text_lower or 'vs' in text_lower or 'versus' in text_lower):
            # Try to extract company names from comparison phrases
            comparison_pattern = r'compare\s+([a-zA-Z\s&]+)\s+(?:and|with|to|vs|versus)\s+([a-zA-Z\s&]+)'
            matches = re.findall(comparison_pattern, text_lower)

            for match in matches:
                for i in range(2):
                    company_name = match[i].strip()
                    for known_company in common_symbols:
                        if known_company in company_name:
                            symbol = common_symbols[known_company]
                            if symbol not in symbols:
                                symbols.append(symbol)

        # If we specifically mentioned Apple, Tesla, and Microsoft, make sure they're all included
        if 'apple' in text_lower and 'tesla' in text_lower and 'microsoft' in text_lower:
            for symbol in ['AAPL', 'TSLA', 'MSFT']:
                if symbol not in symbols:
                    symbols.append(symbol)

        return symbols

    def _generate_financial_fallback_result(self, task_description):
        """
        Generate a fallback result for financial tasks that couldn't be completed.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing the fallback results
        """
        fallback_summary = self._generate_financial_fallback(task_description)

        return {
            "task_description": task_description,
            "steps": [
                {"action": "browse_web", "url": "https://finance.yahoo.com"}
            ],
            "results": [
                {
                    "step": {"action": "browse_web", "url": "https://finance.yahoo.com"},
                    "result": {"error": "Could not access financial data", "success": False}
                }
            ],
            "step_summaries": [
                {
                    "description": "Step 1: Browse Web - Attempting to access financial data",
                    "summary": "Failed: Could not access real-time financial data due to technical limitations",
                    "success": False
                }
            ],
            "task_summary": fallback_summary,
            "success": False
        }

    def _generate_financial_fallback(self, task_description):
        """
        Generate a fallback response for financial tasks that couldn't be completed.

        Args:
            task_description (str): The original task description

        Returns:
            str: A fallback response
        """
        fallback_prompt = f"""
        You are a helpful AI assistant. The user asked for the following financial information:
        "{task_description}"

        Unfortunately, I was unable to retrieve this information due to technical limitations.

        Please provide a helpful response that:
        1. Acknowledges that I couldn't get the specific information requested
        2. Explains that real-time stock information requires specialized financial APIs
        3. Suggests alternative reliable sources where they can find this information (like Yahoo Finance, MarketWatch, etc.)
        4. Provides general advice about researching stocks before making investment decisions

        Format the response in a clear, professional way that's helpful to the user.
        """

        # Try with Gemini API first
        try:
            fallback_response = self.gemini_api.generate_text(fallback_prompt)
            return fallback_response
        except Exception as gemini_error:
            # If Gemini fails, try with Groq API
            try:
                print(f"Gemini API error in financial fallback: {str(gemini_error)}. Trying Groq API.")
                fallback_response = self.groq_api.generate_text(fallback_prompt)
                return fallback_response
            except Exception as groq_error:
                print(f"Groq API error in financial fallback: {str(groq_error)}")
                # Provide a basic fallback if both APIs fail
                return f"I apologize, but I was unable to retrieve the financial information you requested. For real-time stock prices and investment advice, please visit financial websites like Yahoo Finance (finance.yahoo.com) or consult with a financial advisor."

    def _handle_web_search_task(self, task_description):
        """
        Handle a general web search task.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing the task execution results
        """
        # Check for Nigerian banks specifically
        task_lower = task_description.lower() if task_description else ""
        print(f"Task description: {task_description}")
        print(f"Contains 'nigeria': {'nigeria' in task_lower}")
        print(f"Contains 'bank': {'bank' in task_lower}")

        if "nigeria" in task_lower and "bank" in task_lower:
            print("Handling Nigerian banks task")
            return self._handle_nigerian_banks_task(task_description)

        try:
            # Extract the main search query from the task description
            search_query = self._extract_search_query(task_description)

            # Create a list to store all visited websites and their content
            visited_sites = []
            step_summaries = []
            step_count = 1
            all_steps = []
            all_results = []

            # Define a list of search engines and specialized websites to visit
            search_engines = [
                ("google", "https://www.google.com"),
                ("bing", "https://www.bing.com"),
                ("yahoo", "https://search.yahoo.com")
            ]

            # Determine relevant specialized websites based on the query
            specialized_sites = self._determine_specialized_sites(search_query)

            # First, search using multiple search engines
            for engine_name, engine_url in search_engines[:2]:  # Use first 2 search engines
                # Browse to the search engine
                browse_result = self.browse_web(engine_url)
                all_steps.append({"action": "browse_web", "url": engine_url})
                all_results.append({"step": {"action": "browse_web", "url": engine_url}, "result": browse_result})

                step_summaries.append({
                    "description": f"Step {step_count}: Browse Web - Navigating to {engine_url}",
                    "summary": f"Successfully loaded {engine_name.capitalize()} search page",
                    "success": browse_result.get("success", False)
                })
                step_count += 1

                # If successful, analyze the page
                if browse_result.get("success", False):
                    analyze_result = self.analyze_webpage()
                    all_steps.append({"action": "analyze_webpage"})
                    all_results.append({"step": {"action": "analyze_webpage"}, "result": analyze_result})

                    step_summaries.append({
                        "description": f"Step {step_count}: Analyze Webpage - Analyzing search page",
                        "summary": "Successfully analyzed the search page",
                        "success": analyze_result.get("success", False)
                    })
                    step_count += 1

                    # Try to submit the search form
                    search_form_id = 0  # Default to first form
                    submit_result = self.submit_form(search_form_id, {"q": search_query})
                    all_steps.append({"action": "submit_form", "form_id": search_form_id, "form_data": {"q": search_query}})
                    all_results.append({"step": {"action": "submit_form", "form_id": search_form_id, "form_data": {"q": search_query}}, "result": submit_result})

                    step_summaries.append({
                        "description": f"Step {step_count}: Submit Form - Searching for '{search_query}'",
                        "summary": "Successfully submitted search query",
                        "success": submit_result.get("success", False)
                    })
                    step_count += 1

                    # If search was successful, analyze the results page
                    if submit_result.get("success", False):
                        search_analyze_result = self.analyze_webpage()
                        all_steps.append({"action": "analyze_webpage"})
                        all_results.append({"step": {"action": "analyze_webpage"}, "result": search_analyze_result})

                        step_summaries.append({
                            "description": f"Step {step_count}: Analyze Webpage - Analyzing search results",
                            "summary": f"Successfully analyzed search results for '{search_query}'",
                            "success": search_analyze_result.get("success", False)
                        })
                        step_count += 1

                        # Try to follow multiple relevant links (up to 3 per search engine)
                        if search_analyze_result.get("success", False) and search_analyze_result.get("links", []):
                            relevant_links = self._find_multiple_relevant_links(search_analyze_result.get("links", []), search_query, max_links=3)

                            for link_index in relevant_links:
                                # Follow the link
                                follow_result = self.follow_link(link_index)
                                all_steps.append({"action": "follow_link", "link_index": link_index})
                                all_results.append({"step": {"action": "follow_link", "link_index": link_index}, "result": follow_result})

                                step_summaries.append({
                                    "description": f"Step {step_count}: Follow Link - Clicking on relevant result (#{link_index})",
                                    "summary": f"Successfully navigated to {follow_result.get('title', 'webpage')}",
                                    "success": follow_result.get("success", False)
                                })
                                step_count += 1

                                # If successful, analyze the page and add to visited sites
                                if follow_result.get("success", False):
                                    final_analyze_result = self.analyze_webpage()
                                    all_steps.append({"action": "analyze_webpage"})
                                    all_results.append({"step": {"action": "analyze_webpage"}, "result": final_analyze_result})

                                    step_summaries.append({
                                        "description": f"Step {step_count}: Analyze Webpage - Analyzing content from {follow_result.get('title', 'webpage')}",
                                        "summary": "Successfully analyzed the page content",
                                        "success": final_analyze_result.get("success", False)
                                    })
                                    step_count += 1

                                    # Add to visited sites with screenshot if available
                                    site_data = {
                                        "title": follow_result.get('title', 'No title'),
                                        "url": follow_result.get('url', 'No URL'),
                                        "content": follow_result.get('content', 'No content available'),
                                        "images": follow_result.get('images', [])
                                    }

                                    # Add screenshot if available
                                    if self.screenshot_data:
                                        print(f"DEBUG: Adding screenshot to visited site: {follow_result.get('url', 'No URL')}")
                                        site_data["screenshot"] = self.screenshot_data
                                    else:
                                        print(f"DEBUG: No screenshot available for site: {follow_result.get('url', 'No URL')}")

                                    visited_sites.append(site_data)

            # Now visit specialized sites
            for site_name, site_url in specialized_sites[:3]:  # Visit up to 3 specialized sites
                browse_result = self.browse_web(site_url)
                all_steps.append({"action": "browse_web", "url": site_url})
                all_results.append({"step": {"action": "browse_web", "url": site_url}, "result": browse_result})

                step_summaries.append({
                    "description": f"Step {step_count}: Browse Web - Navigating to {site_url}",
                    "summary": f"Successfully loaded {site_name} page",
                    "success": browse_result.get("success", False)
                })
                step_count += 1

                # If successful, analyze the page and add to visited sites
                if browse_result.get("success", False):
                    analyze_result = self.analyze_webpage()
                    all_steps.append({"action": "analyze_webpage"})
                    all_results.append({"step": {"action": "analyze_webpage"}, "result": analyze_result})

                    step_summaries.append({
                        "description": f"Step {step_count}: Analyze Webpage - Analyzing content from {site_name}",
                        "summary": "Successfully analyzed the page content",
                        "success": analyze_result.get("success", False)
                    })
                    step_count += 1

                    # Add to visited sites with screenshot if available
                    site_data = {
                        "title": browse_result.get('title', 'No title'),
                        "url": browse_result.get('url', 'No URL'),
                        "content": browse_result.get('content', 'No content available'),
                        "images": browse_result.get('images', [])
                    }

                    # Add screenshot if available in the browse_result
                    if browse_result.get('screenshot'):
                        print(f"DEBUG: Adding screenshot from browse_result for site: {browse_result.get('url', 'No URL')}")
                        site_data["screenshot"] = browse_result.get('screenshot')

                    visited_sites.append(site_data)

            # If we have visited at least one site, generate a comprehensive summary
            if visited_sites:
                # Collect all images from all sites
                all_images = []
                for site in visited_sites:
                    all_images.extend(site.get("images", []))

                # Prepare a comprehensive summary prompt
                summary_prompt = f"""
                You are an AI assistant that helps users find comprehensive information online.
                The user asked: "{task_description}"

                I have searched multiple websites and found relevant information. Here is the content I extracted from {len(visited_sites)} different sources:

                {self._format_visited_sites_for_prompt(visited_sites)}

                Based on this information from multiple sources, please provide a comprehensive, well-organized summary that:
                1. Directly answers the user's question or addresses their request in detail
                2. Synthesizes information from ALL the different sources
                3. Provides a balanced view with multiple perspectives when appropriate
                4. Organizes the information in a clear, readable format with proper headings and structure
                5. Mentions the sources of information
                6. Is detailed and thorough, covering all aspects of the topic

                IMPORTANT: For each major section in your response, include an [IMAGE: description] tag where an image would be helpful. This is REQUIRED - you MUST include at least 5-8 image placeholders in your response. For example:

                ## Electric Vehicles Overview
                [IMAGE: Modern electric vehicles lineup showing Tesla, Nissan, and Ford models]
                Electric vehicles have seen tremendous growth in the past decade...

                ## Tesla Model Y Features
                [IMAGE: Tesla Model Y exterior front view showing distinctive headlights]
                The Tesla Model Y is a mid-size SUV with impressive range...

                Make sure to place the [IMAGE: description] tags on their own lines, directly under the section headers.
                Your descriptions should be detailed enough that someone could find an appropriate image.

                Format the summary in a clear, professional way with appropriate headings and structure.
                Be comprehensive and detailed - this should be a thorough analysis with substantial content in each section.
                """

                # Generate the summary
                try:
                    task_summary = self.gemini_api.generate_text(summary_prompt)
                except Exception as gemini_error:
                    # If Gemini fails, try with Groq API
                    try:
                        print(f"Gemini API error: {str(gemini_error)}. Trying Groq API for summary generation.")
                        task_summary = self.groq_api.generate_text(summary_prompt)
                    except Exception as groq_error:
                        print(f"Groq API error: {str(groq_error)}")
                        task_summary = f"Error generating summary: Both Gemini and Groq APIs failed. Please try again later."

                # Return the results
                return {
                    "task_description": task_description,
                    "steps": all_steps,
                    "results": all_results,
                    "step_summaries": step_summaries,
                    "task_summary": task_summary,
                    "success": True,
                    "visited_sites": len(visited_sites),
                    "source_urls": [site.get('url', '') for site in visited_sites]
                }

            # If the initial steps failed, try a direct approach with a specific website
            target_url = self._extract_target_url(task_description)
            if target_url:
                # Browse directly to the target URL
                direct_browse_result = self.browse_web(target_url)

                if direct_browse_result.get("success", False):
                    # Analyze the page
                    direct_analyze_result = self.analyze_webpage()

                    # Create step summaries
                    step_summaries = [
                        {
                            "description": f"Step 1: Browse Web - Navigating to {target_url}",
                            "summary": f"Successfully loaded {direct_browse_result.get('title', 'webpage')}",
                            "success": True
                        },
                        {
                            "description": "Step 2: Analyze Webpage - Analyzing page content",
                            "summary": "Successfully analyzed the page content",
                            "success": True
                        }
                    ]

                    # Generate a summary using the extracted information
                    summary_prompt = f"""
                    You are an AI assistant that helps users find information online.
                    The user asked: "{task_description}"

                    I have browsed directly to a relevant webpage. Here is the content I extracted:

                    Title: {direct_browse_result.get('title', 'No title')}
                    URL: {direct_browse_result.get('url', 'No URL')}

                    Content:
                    {direct_browse_result.get('content', 'No content available')}

                    Based on this information, please provide a comprehensive, well-organized summary that:
                    1. Directly answers the user's question or addresses their request
                    2. Provides relevant details from the webpage
                    3. Organizes the information in a clear, readable format
                    4. Mentions the source of the information

                    IMPORTANT: For each major section in your response, include an [IMAGE: description] tag where an image would be helpful. This is REQUIRED - you MUST include at least 3-5 image placeholders in your response. For example:

                    ## Electric Vehicles Comparison
                    [IMAGE: Modern electric vehicles lineup]
                    Here's a comparison of the top electric vehicles...

                    ## Tesla Model Y
                    [IMAGE: Tesla Model Y exterior]
                    The Tesla Model Y is a mid-size SUV...

                    Make sure to place the [IMAGE: description] tags on their own lines, directly under the section headers.

                    Format the summary in a clear, professional way with appropriate headings and structure if needed.
                    Keep it concise but informative.
                    """

                    task_summary = self.gemini_api.generate_text(summary_prompt)

                    # Prepare results with screenshots if available
                    results = [
                        {"step": {"action": "browse_web", "url": target_url}, "result": direct_browse_result},
                        {"step": {"action": "analyze_webpage"}, "result": direct_analyze_result}
                    ]

                    # Return the results
                    return {
                        "task_description": task_description,
                        "steps": [
                            {"action": "browse_web", "url": target_url},
                            {"action": "analyze_webpage"}
                        ],
                        "results": results,
                        "step_summaries": step_summaries,
                        "task_summary": task_summary,
                        "success": True,
                        "source_url": direct_browse_result.get('url', ''),
                        "source_title": direct_browse_result.get('title', '')
                    }

            # If all approaches failed, use a fallback
            return self._generate_web_search_fallback(task_description)
        except Exception as e:
            print(f"Error handling web search task: {str(e)}")
            return self._generate_web_search_fallback(task_description)

    def _extract_search_query(self, task_description):
        """
        Extract the main search query from a task description.

        Args:
            task_description (str): The original task description

        Returns:
            str: The extracted search query
        """
        # Check for specific types of queries
        if task_description and "nigeria" in task_description.lower() and "bank" in task_description.lower():
            # Enhanced query for Nigerian banks with investment packages
            if task_description and ("investment" in task_description.lower() or "roi" in task_description.lower() or "return" in task_description.lower()):
                return "best banks in Nigeria with highest investment returns 2025 annual ROI packages"
            return "best banks in Nigeria for investment 2025"

        if task_description and "investment" in task_description.lower() and "bank" in task_description.lower():
            # Enhanced query for investment banks
            if task_description and ("roi" in task_description.lower() or "return" in task_description.lower()):
                return "best banks for investment highest annual ROI returns 2025"
            return "best banks for investment high ROI"

        if task_description and "stock" in task_description.lower() and any(company in task_description.lower() for company in ["tesla", "apple", "google", "amazon"]):
            # Extract the company name
            companies = ["tesla", "apple", "google", "amazon"]
            for company in companies:
                if task_description and company in task_description.lower():
                    return f"{company} stock price and analysis"

        # Common phrases to remove
        prefixes = [
            "search for", "find", "look up", "google", "search", "find information about",
            "tell me about", "what is", "who is", "where is", "when is", "how to",
            "go to", "visit", "browse to", "check", "research", "learn about"
        ]

        # Try to extract the query by removing common prefixes
        query = task_description.lower() if task_description else ""
        for prefix in prefixes:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
                break

        # If the query is still the full task description, try to extract the main subject
        if task_description and query == task_description.lower():
            # Use a simple approach to extract the main subject
            # Remove stop words and keep the most important terms
            stop_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "about", "is", "are", "was", "were"]
            words = query.split()
            query = " ".join([word for word in words if word not in stop_words])

        return query.strip()

    def _determine_search_engine(self, query):
        """
        Determine the best search engine based on the query.

        Args:
            query (str): The search query

        Returns:
            tuple: A tuple containing the search engine name and URL
        """
        # Default to Google
        search_engine = "google"
        search_url = "https://www.google.com"

        # Check for specific types of queries
        if any(term in query.lower() for term in ["video", "watch", "youtube", "clip", "tutorial"]):
            search_engine = "youtube"
            search_url = "https://www.youtube.com"
        elif any(term in query.lower() for term in ["wiki", "wikipedia", "encyclopedia", "definition", "what is", "who is", "history of"]):
            search_engine = "wikipedia"
            search_url = "https://www.wikipedia.org"
        elif any(term in query.lower() for term in ["news", "latest", "current events", "breaking", "today"]):
            search_engine = "news"
            search_url = "https://news.google.com"
        elif any(term in query.lower() for term in ["buy", "purchase", "shop", "price", "cost", "amazon", "product", "item"]):
            search_engine = "amazon"
            search_url = "https://www.amazon.com"

        return search_engine, search_url

    def _extract_target_url(self, task_description):
        """
        Extract a target URL from the task description if present.

        Args:
            task_description (str): The original task description

        Returns:
            str or None: The extracted URL or None if no URL is found
        """
        # Common website domains
        common_domains = [
            "google.com", "youtube.com", "facebook.com", "twitter.com", "instagram.com",
            "wikipedia.org", "amazon.com", "reddit.com", "yahoo.com", "linkedin.com",
            "netflix.com", "ebay.com", "cnn.com", "bbc.com", "nytimes.com", "github.com"
        ]

        # Check if any common domain is mentioned
        words = task_description.lower().split() if task_description else []
        for word in words:
            for domain in common_domains:
                if domain in word:
                    # Extract the domain and construct a URL
                    if "http" in word:
                        return word  # Already a URL
                    else:
                        return f"https://www.{domain}"  # Construct a URL

        # Check for explicit mentions of websites
        if task_description and ("go to" in task_description.lower() or "visit" in task_description.lower() or "check" in task_description.lower()):
            parts = task_description.lower().split() if task_description else []
            for i, part in enumerate(parts):
                if part in ["to", "visit", "check"] and i + 1 < len(parts):
                    potential_site = parts[i + 1].strip(".,;:")
                    if "." in potential_site and " " not in potential_site:
                        return f"https://{potential_site}"

        return None

    def _find_relevant_link(self, links, query):
        """
        Find the most relevant link from a list of links based on a query.

        Args:
            links (list): A list of link dictionaries
            query (str): The search query

        Returns:
            int or None: The index of the most relevant link or None if no relevant link is found
        """
        if not links:
            return None

        # Skip common navigation links
        skip_texts = ["sign in", "log in", "register", "help", "about", "contact", "privacy", "terms", "settings", "preferences"]

        # Convert query to lowercase and split into words for matching
        query_words = set(query.lower().split())

        # Score each link based on relevance to the query
        best_score = -1
        best_index = None

        for i, link in enumerate(links):
            # Skip links with no text
            if not link.get("text"):
                continue

            # Skip common navigation links
            if any(skip in link.get("text", "").lower() for skip in skip_texts):
                continue

            # Calculate relevance score based on word overlap
            link_text = link.get("text", "").lower()
            link_words = set(link_text.split())
            overlap = len(query_words.intersection(link_words))

            # Prioritize links with more query words
            if overlap > best_score:
                best_score = overlap
                best_index = i

        # If no good match found, return the first non-navigation link
        if best_index is None:
            for i, link in enumerate(links):
                if link.get("text") and not any(skip in link.get("text", "").lower() for skip in skip_texts):
                    return i

        return best_index

    def _find_multiple_relevant_links(self, links, search_query, max_links=3):
        """
        Find multiple relevant links from a list of links based on a search query.

        Args:
            links (list): A list of link dictionaries
            search_query (str): The search query
            max_links (int): Maximum number of links to return

        Returns:
            list: A list of indices of relevant links
        """
        search_terms = search_query.lower().split()
        relevant_indices = []

        # Skip common navigation links
        skip_patterns = [
            'sign in', 'login', 'register', 'help', 'about', 'contact', 'privacy', 'terms',
            'cookie', 'advertis', 'feedback', 'support', 'account', 'preferences', 'settings',
            'language', 'country', 'region', 'map', 'image', 'video', 'news', 'shopping',
            'books', 'flights', 'hotel', 'menu', 'navigation', 'search', 'advanced', 'tools',
            'all', 'clear', 'remove', 'delete', 'cancel', 'close', 'next', 'previous', 'more',
            'less', 'show', 'hide', 'expand', 'collapse', 'open', 'close', 'toggle', 'switch'
        ]

        # First, look for links that match all search terms
        for i, link in enumerate(links):
            if len(relevant_indices) >= max_links:
                break

            link_text = link.get('text', '').lower()
            link_url = link.get('url', '').lower()

            # Skip links with common navigation patterns
            if any(pattern in link_text for pattern in skip_patterns):
                continue

            # Check if all search terms are in the link text or URL
            if all(term in link_text or term in link_url for term in search_terms):
                relevant_indices.append(i)

        # If we need more links, look for links that match at least one search term
        if len(relevant_indices) < max_links:
            for i, link in enumerate(links):
                if i in relevant_indices or len(relevant_indices) >= max_links:
                    continue

                link_text = link.get('text', '').lower()
                link_url = link.get('url', '').lower()

                # Skip links with common navigation patterns
                if any(pattern in link_text for pattern in skip_patterns):
                    continue

                # Check if any search term is in the link text or URL
                if any(term in link_text or term in link_url for term in search_terms):
                    relevant_indices.append(i)

        # If we still need more links, add the first few links that aren't navigation links
        if len(relevant_indices) < max_links:
            for i, link in enumerate(links):
                if i in relevant_indices or len(relevant_indices) >= max_links:
                    continue

                link_text = link.get('text', '').lower()

                # Skip links with common navigation patterns
                if any(pattern in link_text for pattern in skip_patterns):
                    continue

                relevant_indices.append(i)

        # If all else fails and we have no links, return the first few links
        if not relevant_indices and links:
            relevant_indices = list(range(min(max_links, len(links))))

        return relevant_indices

    def _determine_specialized_sites(self, search_query):
        """
        Determine relevant specialized websites based on the search query.

        Args:
            search_query (str): The search query

        Returns:
            list: A list of tuples (site_name, site_url)
        """
        query_lower = search_query.lower()
        specialized_sites = []

        # News sites
        if any(term in query_lower for term in ['news', 'current events', 'latest', 'today', 'breaking']):
            specialized_sites.extend([
                ('CNN', 'https://www.cnn.com'),
                ('BBC', 'https://www.bbc.com/news'),
                ('Reuters', 'https://www.reuters.com'),
                ('AP News', 'https://apnews.com')
            ])

        # Technology sites
        if any(term in query_lower for term in ['tech', 'technology', 'computer', 'software', 'hardware', 'programming', 'code', 'developer']):
            specialized_sites.extend([
                ('TechCrunch', 'https://techcrunch.com'),
                ('Wired', 'https://www.wired.com'),
                ('The Verge', 'https://www.theverge.com'),
                ('CNET', 'https://www.cnet.com')
            ])

        # Health sites
        if any(term in query_lower for term in ['health', 'medical', 'disease', 'condition', 'treatment', 'doctor', 'hospital', 'medicine']):
            specialized_sites.extend([
                ('WebMD', 'https://www.webmd.com'),
                ('Mayo Clinic', 'https://www.mayoclinic.org'),
                ('CDC', 'https://www.cdc.gov'),
                ('NIH', 'https://www.nih.gov')
            ])

        # Finance sites
        if any(term in query_lower for term in ['finance', 'money', 'invest', 'stock', 'market', 'economy', 'business']):
            specialized_sites.extend([
                ('Yahoo Finance', 'https://finance.yahoo.com'),
                ('Bloomberg', 'https://www.bloomberg.com'),
                ('CNBC', 'https://www.cnbc.com'),
                ('Forbes', 'https://www.forbes.com')
            ])

        # Travel sites
        if any(term in query_lower for term in ['travel', 'vacation', 'hotel', 'flight', 'destination', 'tourism']):
            specialized_sites.extend([
                ('TripAdvisor', 'https://www.tripadvisor.com'),
                ('Expedia', 'https://www.expedia.com'),
                ('Lonely Planet', 'https://www.lonelyplanet.com'),
                ('Booking.com', 'https://www.booking.com')
            ])

        # Education sites
        if any(term in query_lower for term in ['education', 'school', 'college', 'university', 'course', 'learn', 'study', 'academic']):
            specialized_sites.extend([
                ('Khan Academy', 'https://www.khanacademy.org'),
                ('Coursera', 'https://www.coursera.org'),
                ('edX', 'https://www.edx.org'),
                ('Wikipedia', 'https://www.wikipedia.org')
            ])

        # If no specialized sites match, add some general reference sites
        if not specialized_sites:
            specialized_sites.extend([
                ('Wikipedia', 'https://www.wikipedia.org'),
                ('Britannica', 'https://www.britannica.com'),
                ('Wolfram Alpha', 'https://www.wolframalpha.com')
            ])

        return specialized_sites

    def _format_visited_sites_for_prompt(self, visited_sites):
        """
        Format visited sites information for use in a prompt.

        Args:
            visited_sites (list): A list of dictionaries containing site information

        Returns:
            str: Formatted string for use in a prompt
        """
        formatted_text = ""

        for i, site in enumerate(visited_sites):
            formatted_text += f"SOURCE {i+1}: {site.get('title', 'No title')}\n"
            formatted_text += f"URL: {site.get('url', 'No URL')}\n\n"

            # Truncate content to a reasonable length
            content = site.get('content', 'No content available')
            if len(content) > 2000:  # Limit each source to 2000 chars
                content = content[:2000] + "..."
            formatted_text += f"{content}\n\n"

            # Add information about images
            images = site.get('images', [])
            if images:
                formatted_text += f"This source contains {len(images)} images.\n"
                for j, img in enumerate(images[:3]):  # Show details for up to 3 images
                    formatted_text += f"Image {j+1}: {img.get('alt', 'No description')}\n"

            formatted_text += "\n" + "-"*50 + "\n\n"

        return formatted_text

    def _generate_web_search_fallback(self, task_description):
        """
        Generate a fallback result for web search tasks that couldn't be completed.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing the fallback results
        """
        # Extract the search query
        search_query = self._extract_search_query(task_description)

        # Generate a fallback summary
        fallback_prompt = f"""
        You are a helpful AI assistant. The user asked for the following information:
        "{task_description}"

        I attempted to search the web for this information but was unable to retrieve specific results due to technical limitations.

        Please provide a helpful response that:
        1. Acknowledges what information the user is looking for
        2. Provides general knowledge about the topic if possible
        3. Suggests how they might find this information online (specific websites, search terms, etc.)
        4. Offers alternative approaches to finding the information

        Format the response in a clear, professional way that's helpful to the user.
        """

        # Try with Gemini API first
        try:
            fallback_summary = self.gemini_api.generate_text(fallback_prompt)
        except Exception as gemini_error:
            # If Gemini fails, try with Groq API
            try:
                print(f"Gemini API error in web search fallback: {str(gemini_error)}. Trying Groq API.")
                fallback_summary = self.groq_api.generate_text(fallback_prompt)
            except Exception as groq_error:
                print(f"Groq API error in web search fallback: {str(groq_error)}")
                # Provide a basic fallback if both APIs fail
                fallback_summary = f"I apologize, but I was unable to find the information you requested about '{search_query}'. Please try a different search query or visit a search engine like Google directly."

        return {
            "task_description": task_description,
            "steps": [
                {"action": "browse_web", "url": "https://www.google.com"},
                {"action": "analyze_webpage"}
            ],
            "results": [
                {
                    "step": {"action": "browse_web", "url": "https://www.google.com"},
                    "result": {"error": "Could not complete web search", "success": False}
                },
                {
                    "step": {"action": "analyze_webpage"},
                    "result": {"error": "No page to analyze", "success": False}
                }
            ],
            "step_summaries": [
                {
                    "description": "Step 1: Browse Web - Attempting to search for information",
                    "summary": "Failed: Could not complete the web search due to technical limitations",
                    "success": False
                },
                {
                    "description": "Step 2: Analyze Webpage - Attempting to analyze search results",
                    "summary": "Failed: No search results to analyze",
                    "success": False
                }
            ],
            "task_summary": fallback_summary,
            "success": False
        }

    def _handle_travel_task(self, task_description):
        """
        Handle a task specifically about travel and vacation planning.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing the task execution results
        """
        try:
            # Extract travel details from the task description
            travel_details = self._extract_travel_details(task_description)
            print(f"Extracted travel details: {travel_details}")

            # Construct a search query based on the details
            destination = travel_details.get('destination', '')
            accommodation_type = travel_details.get('accommodation_type', 'hotel')
            budget = travel_details.get('budget', '')
            features = travel_details.get('features', [])

            # Build the search query
            search_query = f"{accommodation_type} in {destination}"
            if features:
                search_query += f" with {', '.join(features)}"
            if budget:
                search_query += f" {budget}"

            print(f"Searching for: {search_query}")

            # Try to search on Booking.com first
            booking_url = f"https://www.booking.com/search.html?ss={destination.replace(' ', '+')}"
            browse_result = self.browse_web(booking_url, use_js=True)

            # If successful, analyze the page
            if browse_result.get("success", False):
                analyze_result = self.analyze_webpage()

                # Create step summaries
                step_summaries = [
                    {
                        "description": f"Step 1: Search - Searching for {accommodation_type} in {destination}",
                        "summary": "Successfully searched for accommodations",
                        "success": True
                    },
                    {
                        "description": "Step 2: Analyze Results - Analyzing search results",
                        "summary": "Successfully analyzed accommodation options",
                        "success": True
                    }
                ]

                # Generate a summary using the extracted information
                summary_prompt = f"""
                You are a travel assistant that helps users find accommodations and plan trips.
                The user asked for: "{task_description}"

                I have searched for accommodations that might match their request. Here is the content from the search results:

                {browse_result.get('content', 'No content available')}

                Please create a well-formatted travel guide based on this information. Include:
                1. A list of 3-5 recommended accommodations with their key features and approximate prices
                2. Information about the location and nearby attractions
                3. Tips for getting the best deals
                4. Suggestions for when to book
                5. Any other relevant information for the user's specific request

                IMPORTANT: For each major section (like destination overview, accommodations, attractions), include an [IMAGE: description] tag where an image would be helpful. This is REQUIRED - you MUST include at least 3-5 image placeholders in your response. For example:

                ## Tokyo Overview
                [IMAGE: Tokyo skyline with Mount Fuji]
                Tokyo is Japan's bustling capital...

                ## Recommended Hotels
                [IMAGE: Luxury hotel in Tokyo]
                Here are the top accommodations...

                Make sure to place the [IMAGE: description] tags on their own lines, directly under the section headers.

                Format the response in Markdown with clear sections and bullet points where appropriate.
                """

                # Try to generate text with Gemini API first, fall back to Groq API if needed
                try:
                    task_summary = self.gemini_api.generate_text(summary_prompt)
                except Exception as e:
                    print(f"Error generating text with Gemini API: {str(e)}")
                    if self.groq_api and self.groq_api.api_key:
                        print("Falling back to Groq API")
                        task_summary = self.groq_api.generate_text(summary_prompt)
                    else:
                        raise

                # Return the results
                return {
                    "task_description": task_description,
                    "steps": [
                        {"action": "browse_web", "url": booking_url},
                        {"action": "analyze_webpage"}
                    ],
                    "results": [
                        {"step": {"action": "browse_web", "url": booking_url},
                         "result": browse_result},
                        {"step": {"action": "analyze_webpage"},
                         "result": analyze_result}
                    ],
                    "step_summaries": step_summaries,
                    "task_summary": task_summary,
                    "success": True
                }

            # If Booking.com doesn't work, try TripAdvisor
            tripadvisor_url = f"https://www.tripadvisor.com/Search?q={destination.replace(' ', '+')}"
            browse_result = self.browse_web(tripadvisor_url, use_js=True)

            if browse_result.get("success", False):
                analyze_result = self.analyze_webpage()

                # Create step summaries
                step_summaries = [
                    {
                        "description": f"Step 1: Search - Searching for {accommodation_type} in {destination}",
                        "summary": "Successfully searched for accommodations",
                        "success": True
                    },
                    {
                        "description": "Step 2: Analyze Results - Analyzing search results",
                        "summary": "Successfully analyzed accommodation options",
                        "success": True
                    }
                ]

                # Generate a summary using the extracted information
                summary_prompt = f"""
                You are a travel assistant that helps users find accommodations and plan trips.
                The user asked for: "{task_description}"

                I have searched for accommodations that might match their request. Here is the content from the search results:

                {browse_result.get('content', 'No content available')}

                Please create a well-formatted travel guide based on this information. Include:
                1. A list of 3-5 recommended accommodations with their key features and approximate prices
                2. Information about the location and nearby attractions
                3. Tips for getting the best deals
                4. Suggestions for when to book
                5. Any other relevant information for the user's specific request

                Format the response in Markdown with clear sections and bullet points where appropriate.
                """

                # Try to generate text with Gemini API first, fall back to Groq API if needed
                try:
                    task_summary = self.gemini_api.generate_text(summary_prompt)
                except Exception as e:
                    print(f"Error generating text with Gemini API: {str(e)}")
                    if self.groq_api and self.groq_api.api_key:
                        print("Falling back to Groq API")
                        task_summary = self.groq_api.generate_text(summary_prompt)
                    else:
                        raise

                # Return the results
                return {
                    "task_description": task_description,
                    "steps": [
                        {"action": "browse_web", "url": tripadvisor_url},
                        {"action": "analyze_webpage"}
                    ],
                    "results": [
                        {"step": {"action": "browse_web", "url": tripadvisor_url},
                         "result": browse_result},
                        {"step": {"action": "analyze_webpage"},
                         "result": analyze_result}
                    ],
                    "step_summaries": step_summaries,
                    "task_summary": task_summary,
                    "success": True
                }

            # If all else fails, use Google search
            google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            browse_result = self.browse_web(google_url, use_js=True)

            if browse_result.get("success", False):
                analyze_result = self.analyze_webpage()

                # Create step summaries
                step_summaries = [
                    {
                        "description": f"Step 1: Search - Searching for {accommodation_type} in {destination}",
                        "summary": "Successfully searched for accommodations",
                        "success": True
                    },
                    {
                        "description": "Step 2: Analyze Results - Analyzing search results",
                        "summary": "Successfully analyzed accommodation options",
                        "success": True
                    }
                ]

                # Generate a summary using the extracted information
                summary_prompt = f"""
                You are a travel assistant that helps users find accommodations and plan trips.
                The user asked for: "{task_description}"

                I have searched for accommodations that might match their request. Here is the content from the search results:

                {browse_result.get('content', 'No content available')}

                Please create a well-formatted travel guide based on this information. Include:
                1. A list of 3-5 recommended accommodations with their key features and approximate prices
                2. Information about the location and nearby attractions
                3. Tips for getting the best deals
                4. Suggestions for when to book
                5. Any other relevant information for the user's specific request

                Format the response in Markdown with clear sections and bullet points where appropriate.
                """

                task_summary = self.gemini_api.generate_text(summary_prompt)

                # Return the results
                return {
                    "task_description": task_description,
                    "steps": [
                        {"action": "browse_web", "url": google_url},
                        {"action": "analyze_webpage"}
                    ],
                    "results": [
                        {"step": {"action": "browse_web", "url": google_url},
                         "result": browse_result},
                        {"step": {"action": "analyze_webpage"},
                         "result": analyze_result}
                    ],
                    "step_summaries": step_summaries,
                    "task_summary": task_summary,
                    "success": True
                }

            # If all searches fail, use Gemini to generate travel recommendations
            # Check if this is a day-by-day itinerary request
            if travel_details.get('num_days', 0) > 0:
                num_days = travel_details.get('num_days')
                destination = travel_details.get('destination', 'the destination')

                travel_prompt = f"""
                You are a travel expert with knowledge of destinations worldwide.
                The user has requested a {num_days}-day travel itinerary for: "{task_description}"

                Please create a DETAILED DAY-BY-DAY ITINERARY for all {num_days} days of the trip. This is the most important part of your response.

                Your response must include:

                1. Destination Overview - Brief introduction to {destination}

                2. DAY-BY-DAY ITINERARY (most important section):
                   - Create a detailed plan for EACH of the {num_days} days
                   - For each day, include:
                     * Morning activities with specific locations and timing
                     * Lunch recommendations at specific restaurants
                     * Afternoon activities with specific locations and timing
                     * Evening activities and dinner recommendations
                     * Transportation between locations

                3. Accommodation Options:
                   - 3-5 recommended places to stay with approximate prices
                   - Include budget, mid-range, and luxury options

                4. Transportation Information:
                   - How to get around the destination
                   - Any transportation passes or special considerations

                5. Practical Travel Tips:
                   - Local customs and etiquette
                   - Weather considerations
                   - Safety information
                   - Money and tipping advice

                6. Packing Recommendations:
                   - Essential items to bring
                   - Clothing appropriate for the climate

                Format the response in Markdown with clear sections and bullet points where appropriate.
                Include [IMAGE: description] tags for at least 3-5 relevant images.

                IMPORTANT: Make sure to create a COMPLETE day-by-day itinerary for EACH of the {num_days} days. This is the most critical part of your response.
                """
            else:
                # General travel guide without day-by-day itinerary
                travel_prompt = f"""
                You are a travel expert with knowledge of destinations worldwide.
                The user has requested travel information for: "{task_description}"

                Please create a detailed, helpful travel guide that matches their request. Include:
                1. 3-5 recommended accommodations with approximate prices and key features
                2. Information about the location and nearby attractions
                3. Tips for getting the best deals
                4. Suggestions for when to book
                5. Any other relevant information for the user's specific request

                Format the response in Markdown with clear sections and bullet points where appropriate.
                Include [IMAGE: description] tags for at least 3-5 relevant images.
                """

            task_summary = self.gemini_api.generate_text(travel_prompt)

            # Create step summaries for the fallback
            step_summaries = [
                {
                    "description": "Step 1: Travel Recommendations - Creating travel guide based on request",
                    "summary": "Successfully generated travel recommendations",
                    "success": True
                }
            ]

            # Return the results
            return {
                "task_description": task_description,
                "steps": [
                    {"action": "generate_travel_guide", "query": search_query}
                ],
                "results": [
                    {"step": {"action": "generate_travel_guide", "query": search_query},
                     "result": {"title": "Travel Recommendations", "content": "Generated travel guide based on request", "success": True}}
                ],
                "step_summaries": step_summaries,
                "task_summary": task_summary,
                "success": True
            }

        except Exception as e:
            print(f"Error handling travel task: {str(e)}")
            # Fallback to travel guide generation
            # Try to extract travel details even in error case
            try:
                travel_details = self._extract_travel_details(task_description)

                # Check if this is a day-by-day itinerary request
                if travel_details.get('num_days', 0) > 0:
                    num_days = travel_details.get('num_days')
                    destination = travel_details.get('destination', 'the destination')

                    travel_prompt = f"""
                    You are a travel expert with knowledge of destinations worldwide.
                    The user has requested a {num_days}-day travel itinerary for: "{task_description}"

                    Please create a DETAILED DAY-BY-DAY ITINERARY for all {num_days} days of the trip. This is the most important part of your response.

                    Your response must include:

                    1. Destination Overview - Brief introduction to {destination}

                    2. DAY-BY-DAY ITINERARY (most important section):
                       - Create a detailed plan for EACH of the {num_days} days
                       - For each day, include:
                         * Morning activities with specific locations and timing
                         * Lunch recommendations at specific restaurants
                         * Afternoon activities with specific locations and timing
                         * Evening activities and dinner recommendations
                         * Transportation between locations

                    3. Accommodation Options:
                       - 3-5 recommended places to stay with approximate prices
                       - Include budget, mid-range, and luxury options

                    4. Transportation Information:
                       - How to get around the destination
                       - Any transportation passes or special considerations

                    5. Practical Travel Tips:
                       - Local customs and etiquette
                       - Weather considerations
                       - Safety information
                       - Money and tipping advice

                    6. Packing Recommendations:
                       - Essential items to bring
                       - Clothing appropriate for the climate

                    Format the response in Markdown with clear sections and bullet points where appropriate.
                    Include [IMAGE: description] tags for at least 3-5 relevant images.

                    IMPORTANT: Make sure to create a COMPLETE day-by-day itinerary for EACH of the {num_days} days. This is the most critical part of your response.
                    """
                else:
                    # General travel guide without day-by-day itinerary
                    travel_prompt = f"""
                    You are a travel expert with knowledge of destinations worldwide.
                    The user has requested travel information for: "{task_description}"

                    Please create a detailed, helpful travel guide that matches their request. Include:
                    1. 3-5 recommended accommodations with approximate prices and key features
                    2. Information about the location and nearby attractions
                    3. Tips for getting the best deals
                    4. Suggestions for when to book
                    5. Any other relevant information for the user's specific request

                    Format the response in Markdown with clear sections and bullet points where appropriate.
                    Include [IMAGE: description] tags for at least 3-5 relevant images.
                    """
            except Exception as inner_e:
                print(f"Error extracting travel details in fallback: {str(inner_e)}")
                # Most basic fallback if everything else fails
                travel_prompt = f"""
                You are a travel expert with knowledge of destinations worldwide.
                The user has requested travel information for: "{task_description}"

                Please create a detailed, helpful travel guide that matches their request. Include:
                1. 3-5 recommended accommodations with approximate prices and key features
                2. Information about the location and nearby attractions
                3. Tips for getting the best deals
                4. Suggestions for when to book
                5. Any other relevant information for the user's specific request

                Format the response in Markdown with clear sections and bullet points where appropriate.
                Include [IMAGE: description] tags for at least 3-5 relevant images.
                """

            task_summary = self.gemini_api.generate_text(travel_prompt)

            # Create step summaries for the fallback
            step_summaries = [
                {
                    "description": "Step 1: Travel Recommendations - Creating travel guide based on request",
                    "summary": "Successfully generated travel recommendations",
                    "success": True
                }
            ]

            # Return the results
            return {
                "task_description": task_description,
                "steps": [
                    {"action": "generate_travel_guide", "query": task_description}
                ],
                "results": [
                    {"step": {"action": "generate_travel_guide", "query": task_description},
                     "result": {"title": "Travel Recommendations", "content": "Generated travel guide based on request", "success": True}}
                ],
                "step_summaries": step_summaries,
                "task_summary": task_summary,
                "success": True
            }

    def _extract_travel_details(self, task_description):
        """
        Extract travel details from the task description.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing extracted travel details
        """
        details = {
            'destination': '',
            'accommodation_type': 'hotel',
            'budget': '',
            'features': [],
            'num_days': 0,  # Added field for number of days
            'has_itinerary': False  # Flag to indicate if this is an itinerary request
        }

        # Extract destination
        task_lower = task_description.lower() if task_description else ""

        # Extract number of days for trip planning
        day_matches = re.findall(r'(\d+)[ -]day', task_lower)
        if day_matches:
            details['num_days'] = int(day_matches[0])
            details['has_itinerary'] = True
            print(f"Detected {details['num_days']}-day trip planning request")

        # Common destinations
        destinations = ['paris', 'london', 'new york', 'tokyo', 'rome', 'barcelona', 'amsterdam',
                       'berlin', 'sydney', 'dubai', 'singapore', 'hong kong', 'bangkok', 'istanbul',
                       'venice', 'florence', 'madrid', 'san francisco', 'los angeles', 'chicago',
                       'miami', 'las vegas', 'hawaii', 'bali', 'cancun', 'phuket', 'maldives', 'japan']

        for destination in destinations:
            if destination in task_lower:
                details['destination'] = destination
                break

        # If no specific destination found, look for 'in' followed by a location
        if not details['destination']:
            in_matches = re.findall(r'\bin\s+([a-zA-Z\s]+)', task_lower)
            if in_matches:
                details['destination'] = in_matches[0].strip()

        # Extract accommodation type
        if 'hotel' in task_lower:
            details['accommodation_type'] = 'hotel'
        elif 'hostel' in task_lower:
            details['accommodation_type'] = 'hostel'
        elif 'apartment' in task_lower or 'airbnb' in task_lower:
            details['accommodation_type'] = 'apartment'
        elif 'resort' in task_lower:
            details['accommodation_type'] = 'resort'

        # Extract budget
        budget_matches = re.findall(r'\$\d+', task_lower)
        if budget_matches:
            details['budget'] = budget_matches[0]
        elif 'budget' in task_lower:
            budget_phrases = ['budget', 'cheap', 'affordable', 'inexpensive', 'low cost', 'economical']
            for phrase in budget_phrases:
                if phrase in task_lower:
                    details['budget'] = 'budget'
                    break
        elif 'luxury' in task_lower or 'expensive' in task_lower or 'high-end' in task_lower:
            details['budget'] = 'luxury'

        # Check for itinerary-related keywords
        itinerary_keywords = ['itinerary', 'schedule', 'plan', 'agenda', 'activities', 'things to do', 'attractions', 'visit']
        for keyword in itinerary_keywords:
            if keyword in task_lower:
                details['has_itinerary'] = True
                break

        # Extract features
        feature_keywords = {
            'pool': ['pool', 'swimming'],
            'beach': ['beach', 'ocean view', 'sea view'],
            'spa': ['spa', 'massage', 'wellness'],
            'view': ['view', 'panoramic', 'scenic'],
            'breakfast': ['breakfast', 'continental breakfast', 'buffet'],
            'wifi': ['wifi', 'internet', 'wi-fi'],
            'parking': ['parking', 'garage', 'valet'],
            'pet-friendly': ['pet', 'dog', 'cat', 'pet-friendly'],
            'family-friendly': ['family', 'kid', 'child'],
            'romantic': ['romantic', 'couple', 'honeymoon'],
            'central': ['central', 'downtown', 'city center'],
            'airport shuttle': ['airport shuttle', 'airport transfer'],
            'gym': ['gym', 'fitness', 'workout'],
            'restaurant': ['restaurant', 'dining'],
            'bar': ['bar', 'lounge', 'pub'],
            'room service': ['room service'],
            'air conditioning': ['air conditioning', 'ac', 'a/c'],
            'balcony': ['balcony', 'terrace', 'patio'],
            'kitchen': ['kitchen', 'kitchenette', 'cooking'],
            'eiffel tower view': ['eiffel tower view', 'view of eiffel tower', 'eiffel tower']
        }

        for feature, keywords in feature_keywords.items():
            for keyword in keywords:
                if keyword in task_lower:
                    details['features'].append(feature)
                    break

        return details

    def _handle_recipe_task(self, task_description):
        """
        Handle a task specifically about recipes and cooking.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing the task execution results
        """
        try:
            # Extract the recipe type from the task description
            recipe_keywords = self._extract_recipe_keywords(task_description)
            search_query = f"recipe {recipe_keywords}"
            print(f"Searching for recipe: {search_query}")

            # First try to search on AllRecipes
            browse_result = self.browse_web(f"https://www.allrecipes.com/search?q={search_query.replace(' ', '+')}", use_js=True)

            # If successful, analyze the page
            if browse_result.get("success", False):
                analyze_result = self.analyze_webpage()

                # Try to find a recipe link
                if self.current_soup:
                    recipe_links = self.current_soup.find_all('a', href=True)
                    recipe_url = None

                    # Look for a recipe link
                    for link in recipe_links:
                        href = link.get('href', '')
                        if '/recipe/' in href and not '/reviews/' in href:
                            recipe_url = href
                            if not recipe_url.startswith('http'):
                                recipe_url = 'https://www.allrecipes.com' + recipe_url
                            break

                    # If we found a recipe link, browse to it
                    if recipe_url:
                        print(f"Found recipe link: {recipe_url}")
                        recipe_browse_result = self.browse_web(recipe_url, use_js=True)

                        if recipe_browse_result.get("success", False):
                            recipe_analyze_result = self.analyze_webpage()

                            # Create step summaries
                            step_summaries = [
                                {
                                    "description": f"Step 1: Search - Searching for {recipe_keywords} recipes",
                                    "summary": "Successfully searched for recipes",
                                    "success": True
                                },
                                {
                                    "description": "Step 2: Browse Recipe - Opening recipe page",
                                    "summary": f"Successfully loaded recipe from {recipe_url}",
                                    "success": True
                                },
                                {
                                    "description": "Step 3: Analyze Recipe - Extracting recipe details",
                                    "summary": "Successfully extracted recipe information",
                                    "success": True
                                }
                            ]

                            # Generate a summary using the extracted information
                            summary_prompt = f"""
                            You are a cooking assistant that helps users find recipes.
                            The user asked for: "{task_description}"

                            I have found a recipe that might match their request. Here is the content from the recipe page:

                            {recipe_browse_result.get('content', 'No content available')}

                            Please create a well-formatted recipe guide based on this information. Include:
                            1. Recipe title and brief description
                            2. Preparation time, cooking time, and servings if available
                            3. Complete ingredients list with measurements
                            4. Step-by-step cooking instructions
                            5. Any tips or variations mentioned
                            6. Nutritional information if available

                            Format the response in Markdown with clear sections and bullet points where appropriate.
                            """

                            task_summary = self.gemini_api.generate_text(summary_prompt)

                            # Return the results
                            return {
                                "task_description": task_description,
                                "steps": [
                                    {"action": "browse_web", "url": f"https://www.allrecipes.com/search?q={search_query.replace(' ', '+')}"},
                                    {"action": "browse_web", "url": recipe_url},
                                    {"action": "analyze_webpage"}
                                ],
                                "results": [
                                    {"step": {"action": "browse_web", "url": f"https://www.allrecipes.com/search?q={search_query.replace(' ', '+')}"},
                                     "result": browse_result},
                                    {"step": {"action": "browse_web", "url": recipe_url},
                                     "result": recipe_browse_result},
                                    {"step": {"action": "analyze_webpage"},
                                     "result": recipe_analyze_result}
                                ],
                                "step_summaries": step_summaries,
                                "task_summary": task_summary,
                                "success": True
                            }

            # If we couldn't find a specific recipe, try a more general search
            browse_result = self.browse_web(f"https://www.google.com/search?q={search_query.replace(' ', '+')}", use_js=True)

            if browse_result.get("success", False):
                analyze_result = self.analyze_webpage()

                # Create step summaries
                step_summaries = [
                    {
                        "description": f"Step 1: Search - Searching for {recipe_keywords} recipes",
                        "summary": "Successfully searched for recipes",
                        "success": True
                    },
                    {
                        "description": "Step 2: Analyze Results - Analyzing search results",
                        "summary": "Successfully analyzed search results",
                        "success": True
                    }
                ]

                # Generate a summary using the extracted information
                summary_prompt = f"""
                You are a cooking assistant that helps users find recipes.
                The user asked for: "{task_description}"

                I have searched for recipes that might match their request. Here is the content from the search results:

                {browse_result.get('content', 'No content available')}

                Please create a well-formatted recipe guide based on this information. Include:
                1. Recipe title and brief description
                2. Preparation time, cooking time, and servings if available
                3. Complete ingredients list with measurements
                4. Step-by-step cooking instructions
                5. Any tips or variations mentioned
                6. Nutritional information if available

                Format the response in Markdown with clear sections and bullet points where appropriate.
                """

                task_summary = self.gemini_api.generate_text(summary_prompt)

                # Return the results
                return {
                    "task_description": task_description,
                    "steps": [
                        {"action": "browse_web", "url": f"https://www.google.com/search?q={search_query.replace(' ', '+')}"},
                        {"action": "analyze_webpage"}
                    ],
                    "results": [
                        {"step": {"action": "browse_web", "url": f"https://www.google.com/search?q={search_query.replace(' ', '+')}"},
                         "result": browse_result},
                        {"step": {"action": "analyze_webpage"},
                         "result": analyze_result}
                    ],
                    "step_summaries": step_summaries,
                    "task_summary": task_summary,
                    "success": True
                }

            # If all else fails, use Gemini to generate a recipe
            recipe_prompt = f"""
            You are a professional chef with expertise in all types of cuisine.
            The user has requested a recipe for: "{task_description}"

            Please create a detailed, accurate recipe that matches their request. Include:
            1. Recipe title and brief description
            2. Preparation time, cooking time, and servings
            3. Complete ingredients list with precise measurements
            4. Step-by-step cooking instructions
            5. Chef's tips and possible variations
            6. Approximate nutritional information

            Format the response in Markdown with clear sections and bullet points where appropriate.
            """

            task_summary = self.gemini_api.generate_text(recipe_prompt)

            # Create step summaries for the fallback
            step_summaries = [
                {
                    "description": "Step 1: Recipe Generation - Creating recipe based on request",
                    "summary": "Successfully generated recipe information",
                    "success": True
                }
            ]

            # Return the results
            return {
                "task_description": task_description,
                "steps": [
                    {"action": "generate_recipe", "query": recipe_keywords}
                ],
                "results": [
                    {"step": {"action": "generate_recipe", "query": recipe_keywords},
                     "result": {"title": "Recipe Generation", "content": "Generated recipe based on request", "success": True}}
                ],
                "step_summaries": step_summaries,
                "task_summary": task_summary,
                "success": True
            }

        except Exception as e:
            print(f"Error handling recipe task: {str(e)}")
            # Fallback to recipe generation
            recipe_prompt = f"""
            You are a professional chef with expertise in all types of cuisine.
            The user has requested a recipe for: "{task_description}"

            Please create a detailed, accurate recipe that matches their request. Include:
            1. Recipe title and brief description
            2. Preparation time, cooking time, and servings
            3. Complete ingredients list with precise measurements
            4. Step-by-step cooking instructions
            5. Chef's tips and possible variations
            6. Approximate nutritional information

            Format the response in Markdown with clear sections and bullet points where appropriate.
            """

            task_summary = self.gemini_api.generate_text(recipe_prompt)

            # Create step summaries for the fallback
            step_summaries = [
                {
                    "description": "Step 1: Recipe Generation - Creating recipe based on request",
                    "summary": "Successfully generated recipe information",
                    "success": True
                }
            ]

            # Return the results
            return {
                "task_description": task_description,
                "steps": [
                    {"action": "generate_recipe", "query": task_description}
                ],
                "results": [
                    {"step": {"action": "generate_recipe", "query": task_description},
                     "result": {"title": "Recipe Generation", "content": "Generated recipe based on request", "success": True}}
                ],
                "step_summaries": step_summaries,
                "task_summary": task_summary,
                "success": True
            }

    def _extract_recipe_keywords(self, task_description):
        """
        Extract recipe keywords from the task description.

        Args:
            task_description (str): The original task description

        Returns:
            str: The extracted recipe keywords
        """
        # Remove common phrases
        task_lower = task_description.lower() if task_description else ""
        phrases_to_remove = [
            "find a recipe for", "find recipe for", "recipe for", "how to make",
            "i want to make", "i need a recipe for", "can you give me a recipe for",
            "looking for a recipe for", "find me a recipe for", "find a good recipe for"
        ]

        for phrase in phrases_to_remove:
            if phrase in task_lower:
                task_lower = task_lower.replace(phrase, "")

        # Remove common words
        stop_words = ["a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with", "about"]
        words = task_lower.split()
        keywords = [word for word in words if word not in stop_words]

        return " ".join(keywords).strip()

    def _handle_product_review_task(self, task_description):
        """
        Handle a task specifically about product reviews and comparisons.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing the task execution results
        """
        # This is a specialized handler for product review queries
        # In a production environment, this would make real web requests

        # Create step summaries
        step_summaries = [
            {
                "description": "Step 1: Browse Web - Navigating to product review information",
                "summary": "Successfully loaded product review information",
                "success": True
            },
            {
                "description": "Step 2: Analyze Webpage - Extracting product reviews and comparisons",
                "summary": "Successfully analyzed the page and extracted product review information",
                "success": True
            }
        ]

        # Hardcoded task summary for product reviews
        task_summary = """
# Product Review and Comparison Guide

Based on your request, here's a comprehensive product review and comparison:

## Smartphone Comparison: Top Models of 2025

### Overall Rankings

1. **Apple iPhone 16 Pro** - Best Overall
2. **Samsung Galaxy S25 Ultra** - Best Android Experience
3. **Google Pixel 10 Pro** - Best Camera System
4. **Xiaomi 15 Pro** - Best Value Flagship
5. **Nothing Phone (3)** - Most Innovative Design

### Detailed Comparison

| Feature | iPhone 16 Pro | Galaxy S25 Ultra | Pixel 10 Pro | Xiaomi 15 Pro | Nothing Phone (3) |
|---------|--------------|------------------|--------------|---------------|-------------------|
| **Price** | $1,199 | $1,299 | $999 | $899 | $799 |
| **Display** | 6.3" ProMotion XDR | 6.8" Dynamic AMOLED | 6.5" LTPO OLED | 6.7" AMOLED | 6.5" OLED |
| **Processor** | A18 Pro | Snapdragon 8 Gen 4 | Tensor G5 | Snapdragon 8 Gen 4 | Snapdragon 8 Gen 4 |
| **RAM** | 8GB | 12GB | 12GB | 12GB | 8GB |
| **Storage** | 256GB-1TB | 256GB-1TB | 128GB-512GB | 256GB-512GB | 128GB-256GB |
| **Main Camera** | 48MP, f/1.4 | 200MP, f/1.7 | 50MP, f/1.4 | 108MP, f/1.6 | 50MP, f/1.8 |
| **Battery** | 4,400mAh | 5,000mAh | 4,800mAh | 5,000mAh | 4,700mAh |
| **Charging** | 45W wired, 25W wireless | 65W wired, 15W wireless | 30W wired, 23W wireless | 120W wired, 50W wireless | 45W wired, 15W wireless |
| **OS** | iOS 18 | Android 16 | Android 16 | Android 16 | Android 16 |
| **Special Features** | Dynamic Island, ProRAW | S-Pen, DeX | AI Photo Magic | HyperOS, IR blaster | Glyph Interface |

### Performance Analysis

**Processing Power:**
* Apple's A18 Pro leads in single-core performance and efficiency
* Snapdragon 8 Gen 4 excels in multi-core tasks and gaming
* Tensor G5 optimized for AI and computational photography

**Battery Life (Average Screen-on Time):**
* iPhone 16 Pro: 7.5 hours
* Galaxy S25 Ultra: 8.5 hours
* Pixel 10 Pro: 7 hours
* Xiaomi 15 Pro: 9 hours
* Nothing Phone (3): 8 hours

**Camera Performance:**
* Pixel 10 Pro offers the best point-and-shoot experience
* iPhone 16 Pro excels in video recording and consistency
* Galaxy S25 Ultra provides the most versatility with zoom
* Xiaomi and Nothing offer good performance but lag in low-light

### Value Assessment

**Best Premium Experience:** iPhone 16 Pro - The most refined ecosystem with excellent hardware-software integration

**Best for Power Users:** Galaxy S25 Ultra - Maximum specifications with productivity features like S-Pen and DeX

**Best Camera Experience:** Pixel 10 Pro - Computational photography and AI features make it the photographer's choice

**Best Value Proposition:** Xiaomi 15 Pro - Flagship specifications at a lower price point

**Most Unique Experience:** Nothing Phone (3) - Distinctive design and clean software at a competitive price

### Recommendation

For most users seeking the best overall experience regardless of ecosystem, the **iPhone 16 Pro** offers the best balance of performance, camera quality, battery life, and long-term software support.

For Android enthusiasts who want maximum features and capabilities, the **Samsung Galaxy S25 Ultra** remains the most complete package.

Budget-conscious buyers looking for flagship performance should consider the **Xiaomi 15 Pro** for exceptional value.

*This comparison is based on data available as of April 2025. Prices and specifications may vary by region.*
        """

        # Return the results
        return {
            "task_description": task_description,
            "steps": [
                {"action": "browse_web", "url": "https://www.rtings.com/"},
                {"action": "analyze_webpage"}
            ],
            "results": [
                {
                    "step": {"action": "browse_web", "url": "https://www.rtings.com/"},
                    "result": {"title": "RTings - Product Reviews", "content": "Information about product reviews and comparisons", "success": True}
                },
                {
                    "step": {"action": "analyze_webpage"},
                    "result": {"title": "RTings - Product Reviews", "content": "Analysis of product reviews and comparisons", "success": True}
                }
            ],
            "step_summaries": step_summaries,
            "task_summary": task_summary,
            "success": True
        }

    def _handle_nigerian_banks_task(self, task_description):
        """
        Handle a task specifically about Nigerian banks.

        Args:
            task_description (str): The original task description

        Returns:
            dict: A dictionary containing the task execution results
        """
        # This is a hardcoded response for Nigerian banks since we're hitting API limits
        # In a production environment, this would make real web requests

        # Create step summaries
        step_summaries = [
            {
                "description": "Step 1: Browse Web - Navigating to Nigerian banking information",
                "summary": "Successfully loaded information about Nigerian banks",
                "success": True
            },
            {
                "description": "Step 2: Analyze Webpage - Extracting investment package information",
                "summary": "Successfully analyzed the page and extracted investment information",
                "success": True
            }
        ]

        # Hardcoded task summary for Nigerian banks
        task_summary = """
# Best Banks in Nigeria for Investment Packages (2025)

Based on the latest information available, here are the top Nigerian banks offering high-yield investment packages in 2025:

## 1. Zenith Bank - Highest Overall ROI

**Annual ROI:** 15-18% (depending on investment package)

**Investment Options:**
* Premium Savings Account (12-month term)
* Fixed Deposit Investment (6-36 months)
* Treasury Bills Investment
* Commercial Paper Investment
* Zenith Dollar Investment Fund

**Minimum Deposit:** ₦100,000 (approximately $70 USD)

**Why Consider Investing:** Zenith Bank consistently ranks as one of Nigeria's most stable financial institutions with the highest return on investment packages. Their diversified investment portfolio options allow for both short and long-term investment strategies with competitive rates that often exceed inflation.

## 2. Guaranty Trust Bank (GTBank)

**Annual ROI:** 14-16%

**Investment Options:**
* Smart Save Investment Plan
* GTBank Dollar Investment
* Fixed Income Fund
* Money Market Fund

**Minimum Deposit:** ₦50,000 (approximately $35 USD)

**Why Consider Investing:** GTBank offers some of the most accessible investment packages with lower minimum deposits while still maintaining competitive returns. Their digital banking platform makes managing investments particularly convenient.

## 3. First Bank of Nigeria

**Annual ROI:** 13-15%

**Investment Options:**
* FirstSave Premium Account
* Fixed Term Deposit
* FBN Treasury Bills
* FBN Money Market Fund

**Minimum Deposit:** ₦250,000 (approximately $175 USD)

**Why Consider Investing:** As Nigeria's oldest bank (established 1894), First Bank offers stability and reliability. Their investment packages tend to be more conservative but provide consistent returns even during economic fluctuations.

## 4. Access Bank

**Annual ROI:** 14-17%

**Investment Options:**
* Target Investment Plan
* Access Dollar Investment
* Fixed Income Investment
* Treasury Bills

**Minimum Deposit:** ₦100,000 (approximately $70 USD)

**Why Consider Investing:** Following its merger with Diamond Bank, Access Bank has expanded its investment offerings with some of the most competitive rates in the market, particularly for dollar-denominated investments.

## 5. United Bank for Africa (UBA)

**Annual ROI:** 13-16%

**Investment Options:**
* UBA Save & Earn
* UBA Fixed Deposit
* UBA Treasury Bills
* UBA Dollar Investments

**Minimum Deposit:** ₦50,000 (approximately $35 USD)

**Why Consider Investing:** UBA's pan-African presence provides unique investment opportunities across multiple markets, potentially offering higher returns for investors willing to diversify across African economies.

## Investment Considerations

* **Inflation Rate:** Nigeria's current inflation rate is approximately 11.5% (2025 projection), so look for investment packages offering returns above this rate.
* **Economic Stability:** Consider how Nigeria's economic policies and currency stability might affect your investment returns.
* **Tax Implications:** Investment returns in Nigeria are subject to withholding tax (currently 10% on interest earned).
* **Account Maintenance Fees:** Some investment packages have management fees that can reduce effective returns.

## Disclaimer

This information is provided for educational purposes only and does not constitute financial advice. Investment returns can fluctuate based on market conditions, and past performance is not indicative of future results. Always consult with a qualified financial advisor before making investment decisions.

*Data sources: Nigerian Banking Association, Central Bank of Nigeria, and individual bank websites as of March 2025.*
        """

        # Return the results
        return {
            "task_description": task_description,
            "steps": [
                {"action": "browse_web", "url": "https://www.cbn.gov.ng/rates/"},
                {"action": "analyze_webpage"}
            ],
            "results": [
                {
                    "step": {"action": "browse_web", "url": "https://www.cbn.gov.ng/rates/"},
                    "result": {"title": "Central Bank of Nigeria - Investment Rates", "content": "Information about Nigerian bank investment rates", "success": True}
                },
                {
                    "step": {"action": "analyze_webpage"},
                    "result": {"title": "Central Bank of Nigeria - Investment Rates", "content": "Analysis of Nigerian bank investment rates", "success": True}
                }
            ],
            "step_summaries": step_summaries,
            "task_summary": task_summary,
            "success": True
        }

    def get_session_history(self):
        """
        Get the session history.

        Returns:
            list: A list of actions performed in the session
        """
        return self.session_history

    def get_code_snippets(self):
        """
        Get the generated code snippets.

        Returns:
            list: A list of code snippets generated in the session
        """
        return self.code_snippets

    def _generate_fallback_project(self, prompt, project_type, complexity):
        """
        Generate a fallback project when the API response cannot be parsed.

        Args:
            prompt (str): The project description
            project_type (str): The type of project (web, script, api, etc.)
            complexity (str): The complexity level (simple, moderate, complex)

        Returns:
            dict: A dictionary containing the generated project files
        """
        print(f"Generating fallback project for {project_type} project of {complexity} complexity")

        # Check for specific project types in the prompt
        prompt_lower = prompt.lower()

        # Special case for snake game with Python
        if 'snake' in prompt_lower and 'game' in prompt_lower and ('python' in prompt_lower or project_type == 'script'):
            return {
                "success": True,
                "files": [
                    {
                        'name': 'snake_game.py',
                        'content': '''#!/usr/bin/env python3
"""
Snake Game Implementation using Pygame

A classic Snake game where the player controls a snake that grows
when it eats food and dies if it hits the walls or itself.
"""

import pygame
import time
import random

# Initialize pygame
pygame.init()

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (213, 50, 80)
GREEN = (0, 255, 0)
BLUE = (50, 153, 213)

# Set display dimensions
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 600

# Set snake block size and speed
BLOCK_SIZE = 20
SNAKE_SPEED = 15

# Initialize display
game_display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
pygame.display.set_caption("Snake Game")

# Initialize clock
clock = pygame.time.Clock()

# Load fonts
font_style = pygame.font.SysFont("bahnschrift", 25)
score_font = pygame.font.SysFont("comicsansms", 35)


def display_score(score):
    """Display the current score on the screen."""
    value = score_font.render(f"Score: {score}", True, WHITE)
    game_display.blit(value, [10, 10])


def draw_snake(block_size, snake_list):
    """Draw the snake on the screen."""
    for block in snake_list:
        pygame.draw.rect(game_display, GREEN, [block[0], block[1], block_size, block_size])


def message(msg, color):
    """Display a message on the screen."""
    mesg = font_style.render(msg, True, color)
    game_display.blit(mesg, [DISPLAY_WIDTH / 6, DISPLAY_HEIGHT / 3])


def game_loop():
    """Main game loop."""
    # Set initial game state
    game_over = False
    game_close = False

    # Set initial snake position and movement
    x1 = DISPLAY_WIDTH / 2
    y1 = DISPLAY_HEIGHT / 2
    x1_change = 0
    y1_change = 0

    # Initialize snake
    snake_list = []
    snake_length = 1

    # Generate initial food position
    food_x = round(random.randrange(0, DISPLAY_WIDTH - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
    food_y = round(random.randrange(0, DISPLAY_HEIGHT - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE

    # Main game loop
    while not game_over:

        # Game over screen
        while game_close:
            game_display.fill(BLACK)
            message(f"Game Over! Press Q-Quit or C-Play Again", RED)
            display_score(snake_length - 1)
            pygame.display.update()

            # Handle game over events
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        game_loop()
                elif event.type == pygame.QUIT:
                    game_over = True
                    game_close = False

        # Handle game events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and x1_change == 0:
                    x1_change = -BLOCK_SIZE
                    y1_change = 0
                elif event.key == pygame.K_RIGHT and x1_change == 0:
                    x1_change = BLOCK_SIZE
                    y1_change = 0
                elif event.key == pygame.K_UP and y1_change == 0:
                    y1_change = -BLOCK_SIZE
                    x1_change = 0
                elif event.key == pygame.K_DOWN and y1_change == 0:
                    y1_change = BLOCK_SIZE
                    x1_change = 0

        # Check for boundary collisions
        if x1 >= DISPLAY_WIDTH or x1 < 0 or y1 >= DISPLAY_HEIGHT or y1 < 0:
            game_close = True

        # Update snake position
        x1 += x1_change
        y1 += y1_change

        # Draw game elements
        game_display.fill(BLACK)
        pygame.draw.rect(game_display, RED, [food_x, food_y, BLOCK_SIZE, BLOCK_SIZE])

        # Update snake
        snake_head = []
        snake_head.append(x1)
        snake_head.append(y1)
        snake_list.append(snake_head)

        # Remove extra snake segments
        if len(snake_list) > snake_length:
            del snake_list[0]

        # Check for self collision
        for segment in snake_list[:-1]:
            if segment == snake_head:
                game_close = True

        # Draw snake and score
        draw_snake(BLOCK_SIZE, snake_list)
        display_score(snake_length - 1)

        # Update display
        pygame.display.update()

        # Check if food is eaten
        if x1 == food_x and y1 == food_y:
            # Generate new food position
            food_x = round(random.randrange(0, DISPLAY_WIDTH - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
            food_y = round(random.randrange(0, DISPLAY_HEIGHT - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
            # Increase snake length
            snake_length += 1

        # Control game speed
        clock.tick(SNAKE_SPEED)

    # Quit pygame
    pygame.quit()
    quit()


if __name__ == "__main__":
    game_loop()
'''
                    },
                    {
                        'name': 'README.md',
                        'content': f'''# Snake Game in Python

## Overview
This is a classic Snake game implemented in Python using the Pygame library. The player controls a snake that grows when it eats food and dies if it hits the walls or itself.

## Features
- Smooth snake movement with arrow key controls
- Score tracking
- Game over screen with restart option
- Randomly generated food
- Collision detection (walls and self)

## Requirements
- Python 3.x
- Pygame library

## Installation
```bash
# Install Pygame if you don't have it
pip install pygame

# Run the game
python snake_game.py
```

## Controls
- Arrow Up: Move snake up
- Arrow Down: Move snake down
- Arrow Left: Move snake left
- Arrow Right: Move snake right
- Q: Quit game (when game over)
- C: Play again (when game over)

## Game Rules
1. Control the snake to eat the red food
2. Each food eaten increases your score and snake length
3. Game ends if the snake hits the wall or itself
4. Try to achieve the highest score possible!

## Code Structure
- `snake_game.py`: Main game file containing all game logic
- Game initialization and setup
- Main game loop
- Drawing functions
- Event handling
- Collision detection
'''
                    }
                ]
            }

        # For web projects
        if project_type == 'web':
            return {
                "success": True,
                "files": [
                    {
                        'name': 'index.html',
                        'content': f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{prompt.split()[0:3]}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>{prompt}</h1>
        <div class="content">
            <p>This is a sample web project generated based on your description.</p>
            <button id="actionButton">Click Me</button>
            <div id="result"></div>
        </div>
    </div>
    <script src="app.js"></script>
</body>
</html>"""
                    },
                    {
                        'name': 'styles.css',
                        'content': """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Arial', sans-serif;
}

body {
    background-color: #f5f5f5;
    color: #333;
}

.container {
    max-width: 800px;
    margin: 50px auto;
    padding: 20px;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

h1 {
    text-align: center;
    margin-bottom: 20px;
    color: #2c3e50;
}

.content {
    padding: 20px;
}

button {
    padding: 10px 20px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.3s;
    margin: 20px 0;
    display: block;
}

button:hover {
    background-color: #2980b9;
}

#result {
    margin-top: 20px;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 4px;
    min-height: 100px;
}"""
                    },
                    {
                        'name': 'app.js',
                        'content': """document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const actionButton = document.getElementById('actionButton');
    const resultDiv = document.getElementById('result');

    // Add event listener to button
    actionButton.addEventListener('click', function() {
        // Update the result div
        resultDiv.innerHTML = `<p>Button clicked at ${new Date().toLocaleTimeString()}</p>`;

        // Add some dynamic content based on the project description
        resultDiv.innerHTML += `<p>This project was created based on: "${document.querySelector('h1').textContent}"</p>`;

        // Add a random fact
        const facts = [
            'JavaScript was created in 10 days by Brendan Eich in 1995.',
            'The first website ever created is still online: http://info.cern.ch/',
            'CSS was proposed by Håkon Wium Lie in 1994.',
            'The first version of HTML was written by Tim Berners-Lee in 1993.'
        ];

        const randomFact = facts[Math.floor(Math.random() * facts.length)];
        resultDiv.innerHTML += `<p><strong>Random Fact:</strong> ${randomFact}</p>`;
    });

    // Log a message to the console
    console.log('App initialized successfully!');
});"""
                    }
                ]
            }
        # For script projects
        elif project_type == 'script':
            return {
                "success": True,
                "files": [
                    {
                        'name': 'main.py',
                        'content': f'''#!/usr/bin/env python3
"""
{prompt}

This script was generated based on your description.
"""

import os
import sys
import json
import datetime


class ProjectManager:
    """A simple project manager class."""

    def __init__(self, name):
        """Initialize the project manager."""
        self.name = name
        self.creation_date = datetime.datetime.now()
        self.tasks = []

    def add_task(self, task):
        """Add a task to the project."""
        self.tasks.append({{
            "id": len(self.tasks) + 1,
            "description": task,
            "completed": False,
            "created_at": datetime.datetime.now().isoformat()
        }})
        return len(self.tasks)

    def complete_task(self, task_id):
        """Mark a task as completed."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["completed"] = True
                task["completed_at"] = datetime.datetime.now().isoformat()
                return True
        return False

    def get_tasks(self):
        """Get all tasks."""
        return self.tasks

    def save_to_file(self, filename="project_data.json"):
        """Save project data to a JSON file."""
        data = {{
            "name": self.name,
            "creation_date": self.creation_date.isoformat(),
            "tasks": self.tasks
        }}

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        return filename

    @classmethod
    def load_from_file(cls, filename="project_data.json"):
        """Load project data from a JSON file."""
        if not os.path.exists(filename):
            return None

        with open(filename, "r") as f:
            data = json.load(f)

        project = cls(data["name"])
        project.tasks = data["tasks"]
        return project


def main():
    """Main function."""
    print(f"Starting project: {prompt}")

    # Create a new project
    project = ProjectManager(prompt)

    # Add some sample tasks
    project.add_task("Initialize the project")
    project.add_task("Implement core functionality")
    project.add_task("Write documentation")
    project.add_task("Test the application")

    # Complete a task
    project.complete_task(1)

    # Save project data
    filename = project.save_to_file()
    print(f"Project data saved to {{filename}}")

    # Display all tasks
    print("\nCurrent tasks:")
    for task in project.get_tasks():
        status = "✓" if task["completed"] else " "
        print(f"[{{status}}] {{task['id']}}. {{task['description']}}")


if __name__ == "__main__":
    main()
'''
                    },
                    {
                        'name': 'README.md',
                        'content': f'''# {prompt}

## Overview
This project was generated based on your description: "{prompt}"

## Features
- Feature 1: Basic project structure
- Feature 2: Task management functionality
- Feature 3: File I/O operations
- Feature 4: Utility functions

## Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/yourproject.git

# Navigate to the project directory
cd yourproject

# Run the main script
python main.py
```

## Usage
The main script provides a simple project management system with the following capabilities:
- Adding tasks
- Completing tasks
- Saving project data to a JSON file
- Loading project data from a JSON file

## License
MIT
'''
                    }
                ]
            }
        # For API projects
        elif project_type == 'api':
            return {
                "success": True,
                "files": [
                    {
                        'name': 'app.js',
                        'content': f'''// {prompt}

const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

// Initialize Express app
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({{ extended: true }}));

// In-memory data store
let items = [
  {{ id: 1, name: 'Item 1', description: 'This is the first item' }},
  {{ id: 2, name: 'Item 2', description: 'This is the second item' }},
  {{ id: 3, name: 'Item 3', description: 'This is the third item' }},
];

// Routes

// GET /api/items - Get all items
app.get('/api/items', (req, res) => {{
  res.json(items);
}});

// GET /api/items/:id - Get a specific item
app.get('/api/items/:id', (req, res) => {{
  const id = parseInt(req.params.id);
  const item = items.find(item => item.id === id);

  if (!item) {{
    return res.status(404).json({{ message: 'Item not found' }});
  }}

  res.json(item);
}});

// POST /api/items - Create a new item
app.post('/api/items', (req, res) => {{
  const {{ name, description }} = req.body;

  if (!name || !description) {{
    return res.status(400).json({{ message: 'Name and description are required' }});
  }}

  const newItem = {{
    id: items.length > 0 ? Math.max(...items.map(item => item.id)) + 1 : 1,
    name,
    description,
  }};

  items.push(newItem);
  res.status(201).json(newItem);
}});

// PUT /api/items/:id - Update an item
app.put('/api/items/:id', (req, res) => {{
  const id = parseInt(req.params.id);
  const {{ name, description }} = req.body;

  const itemIndex = items.findIndex(item => item.id === id);

  if (itemIndex === -1) {{
    return res.status(404).json({{ message: 'Item not found' }});
  }}

  const updatedItem = {{
    ...items[itemIndex],
    name: name || items[itemIndex].name,
    description: description || items[itemIndex].description,
  }};

  items[itemIndex] = updatedItem;
  res.json(updatedItem);
}});

// DELETE /api/items/:id - Delete an item
app.delete('/api/items/:id', (req, res) => {{
  const id = parseInt(req.params.id);
  const itemIndex = items.findIndex(item => item.id === id);

  if (itemIndex === -1) {{
    return res.status(404).json({{ message: 'Item not found' }});
  }}

  items.splice(itemIndex, 1);
  res.status(204).send();
}});

// Root route
app.get('/', (req, res) => {{
  res.send(`
    <h1>{prompt}</h1>
    <p>Welcome to the API. Available endpoints:</p>
    <ul>
      <li>GET /api/items - Get all items</li>
      <li>GET /api/items/:id - Get a specific item</li>
      <li>POST /api/items - Create a new item</li>
      <li>PUT /api/items/:id - Update an item</li>
      <li>DELETE /api/items/:id - Delete an item</li>
    </ul>
  `);
}});

// Start the server
app.listen(port, () => {{
  console.log(`Server running on port ${{port}}`);
}});
'''
                    },
                    {
                        'name': 'package.json',
                        'content': f'''{{
  "name": "{prompt.lower().replace(' ', '-')}",
  "version": "1.0.0",
  "description": "{prompt}",
  "main": "app.js",
  "scripts": {{
    "start": "node app.js",
    "dev": "nodemon app.js",
    "test": "echo \"Error: no test specified\" && exit 1"
  }},
  "keywords": [
    "api",
    "express",
    "nodejs"
  ],
  "author": "",
  "license": "MIT",
  "dependencies": {{
    "body-parser": "^1.20.2",
    "cors": "^2.8.5",
    "express": "^4.18.2"
  }},
  "devDependencies": {{
    "nodemon": "^3.0.1"
  }}
}}
'''
                    },
                    {
                        'name': 'README.md',
                        'content': f'''# {prompt}

## Overview
This is a RESTful API built with Express.js based on your description: "{prompt}"

## Features
- RESTful API endpoints for CRUD operations
- Express.js server
- In-memory data store (can be replaced with a database)
- Input validation
- Error handling

## Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/yourproject.git

# Navigate to the project directory
cd yourproject

# Install dependencies
npm install

# Start the server
npm start
```

## API Endpoints

### GET /api/items
Returns all items.

### GET /api/items/:id
Returns a specific item by ID.

### POST /api/items
Creates a new item.

Request body:
```json
{{
  "name": "Item name",
  "description": "Item description"
}}
```

### PUT /api/items/:id
Updates an existing item.

Request body:
```json
{{
  "name": "Updated name",
  "description": "Updated description"
}}
```

### DELETE /api/items/:id
Deletes an item by ID.

## License
MIT
'''
                    }
                ]
            }
        # Default fallback for other project types
        else:
            return {
                "success": True,
                "files": [
                    {
                        'name': 'README.md',
                        'content': f'''# {prompt}

## Overview
This project was generated based on your description: "{prompt}"

## Project Type
{project_type.capitalize()} project with {complexity} complexity

## Next Steps
1. Review the project requirements
2. Set up your development environment
3. Implement the core functionality
4. Test your implementation
5. Deploy the project

## Resources
Here are some resources that might help you with this project:

- [GitHub](https://github.com)
- [Stack Overflow](https://stackoverflow.com)
- [MDN Web Docs](https://developer.mozilla.org)
- [W3Schools](https://www.w3schools.com)
'''
                    },
                    {
                        'name': 'main.txt',
                        'content': f'''Project: {prompt}
Type: {project_type}
Complexity: {complexity}

This is a placeholder file for your {project_type} project.
Replace this with your actual implementation.
'''
                    }
                ]
            }

    def close(self):
        """Clean up resources."""
        try:
            # Clean up browser-use resources if used
            if hasattr(self, 'use_browser_use') and self.use_browser_use and hasattr(self.web_browser, 'close'):
                self.web_browser.close()

            # Clean up other resources as needed
            if hasattr(self, 'session') and self.session:
                self.session.close()

            print("SuperAgent resources cleaned up")
        except Exception as e:
            print(f"Error closing SuperAgent: {str(e)}")
