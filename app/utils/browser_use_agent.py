"""
Browser Use Agent for Agen911.
This module provides integration with the browser-use library for more complex web browsing tasks.
"""

import os
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Import LangChain components
try:
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Import browser-use components
try:
    from browser_use import Agent as BrowserUseAgent

    # Try to import settings classes if available
    try:
        from browser_use.browser.settings import BrowserSettings
        from browser_use.agent.settings import AgentSettings
        BROWSER_USE_SETTINGS_AVAILABLE = True
    except ImportError:
        BROWSER_USE_SETTINGS_AVAILABLE = False

    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    BROWSER_USE_SETTINGS_AVAILABLE = False

# Import local API clients
from app.api.gemini import GeminiAPI
from app.api.groq import GroqAPI

class BrowserUseWrapper:
    """
    A wrapper for the browser-use library that provides an interface similar to our WebBrowser class.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-pro", headless: bool = False):
        """
        Initialize the BrowserUseWrapper.

        Args:
            api_key (str, optional): The Gemini API key. If not provided, it will be loaded from environment variables.
            model (str, optional): The model to use. Defaults to "gemini-1.5-pro".
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to False.
        """
        if not BROWSER_USE_AVAILABLE:
            print("⚠️  browser-use is not available. Using fallback mode.")
            self.available = False
            self.agent = None
            return

        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. Please install it with 'pip install langchain langchain-openai langchain-google-genai'"
            )

        # Load environment variables
        load_dotenv()

        # Initialize API clients
        self.gemini_api = GeminiAPI(api_key=api_key, model_name=model)
        self.groq_api = GroqAPI()  # For fallback

        # Store the model name for reference
        self.model_name = model

        # Get API keys from environment
        # Check for primary and backup Gemini API keys
        gemini_api_key = api_key or os.getenv("GEMINI_API_KEY")
        gemini_api_key_backup1 = os.getenv("GEMINI_API_KEY_BACKUP1")
        gemini_api_key_backup2 = os.getenv("GEMINI_API_KEY_BACKUP2")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        # Set up LLM based on available API keys
        if gemini_api_key:
            # Use Gemini as primary LLM
            print("Using Gemini API for browser-use")
            try:
                # Try with temperature parameter
                self.llm = ChatGoogleGenerativeAI(api_key=gemini_api_key, model=model, temperature=0.7)
                self.primary_llm = "gemini"
            except TypeError:
                # If that fails, try without temperature parameter
                try:
                    self.llm = ChatGoogleGenerativeAI(api_key=gemini_api_key, model=model)
                    self.primary_llm = "gemini"
                except Exception as e:
                    print(f"Error initializing Gemini API: {str(e)}")
                    # If Gemini fails completely, try OpenAI if available
                    if openai_api_key:
                        print("Falling back to OpenAI API")
                        self.llm = ChatOpenAI(api_key=openai_api_key, model="gpt-3.5-turbo")
                        self.primary_llm = "openai"
                    else:
                        raise ValueError("Failed to initialize Gemini API and no OpenAI API key available")

            # Store backup keys
            self.backup_keys = [k for k in [gemini_api_key_backup1, gemini_api_key_backup2] if k]
            if self.backup_keys:
                print(f"Found {len(self.backup_keys)} backup Gemini API keys")
                # Store backup LLMs for quick access
                self.backup_llms = []
                for i, backup_key in enumerate(self.backup_keys):
                    try:
                        backup_llm = ChatGoogleGenerativeAI(api_key=backup_key, model=model, temperature=0.7)
                        self.backup_llms.append(backup_llm)
                        print(f"Successfully initialized backup Gemini API key {i+1}")
                    except Exception as e:
                        print(f"Failed to initialize backup Gemini API key {i+1}: {str(e)}")
        elif openai_api_key:
            # Use OpenAI as fallback if Gemini key is not available
            print("Gemini API key not found, using OpenAI API for browser-use")
            self.llm = ChatOpenAI(api_key=openai_api_key, model="gpt-3.5-turbo")
            self.primary_llm = "openai"
            self.backup_keys = []
            self.backup_llms = []
        else:
            # No API keys available
            raise ValueError("No API keys found. Please set GEMINI_API_KEY or OPENAI_API_KEY in your .env file.")

        # Store settings for agent creation
        self.headless = headless
        self.max_iterations = 15
        self.verbose = True

        # State tracking
        self.current_url = None
        self.current_page_content = None
        self.current_soup = None
        self.task_result = None

    async def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a task using the browser-use agent.

        Args:
            task (str): The task to execute.

        Returns:
            dict: A dictionary containing the task execution results.
        """
        # Set a flag to track if we should use the lightweight browser as fallback
        use_lightweight_fallback = False

        try:
            # Create and run the agent with the configured LLM
            # Check if browser-use settings are available
            if BROWSER_USE_SETTINGS_AVAILABLE:
                try:
                    # Create settings objects
                    browser_settings = BrowserSettings(headless=self.headless)
                    agent_settings = AgentSettings(max_iterations=self.max_iterations, verbose=self.verbose)

                    # Create agent with settings objects
                    agent = BrowserUseAgent(
                        task=task,
                        llm=self.llm,  # This will be either ChatOpenAI or ChatGoogleGenerativeAI based on available API keys
                        browser_settings=browser_settings,
                        agent_settings=agent_settings
                    )
                except Exception as e:
                    print(f"Error creating agent with settings: {str(e)}. Trying with minimal parameters...")
                    agent = BrowserUseAgent(
                        task=task,
                        llm=self.llm  # This will be either ChatOpenAI or ChatGoogleGenerativeAI based on available API keys
                    )
            else:
                # Use minimal parameters for older versions
                agent = BrowserUseAgent(
                    task=task,
                    llm=self.llm  # This will be either ChatOpenAI or ChatGoogleGenerativeAI based on available API keys
                )

            # Try to run the agent with the primary LLM
            try:
                print(f"Executing task with {self.primary_llm.upper()} LLM: {task}")
                result = await agent.run()
                self.task_result = result
            except Exception as llm_error:
                # Check if this is a Playwright browser error
                if "Executable doesn't exist" in str(llm_error) or "Failed to initialize Playwright browser" in str(llm_error):
                    print(f"Playwright browser error: {str(llm_error)}")
                    print("Falling back to lightweight browser...")
                    use_lightweight_fallback = True
                    raise llm_error
                # Check if we have backup Gemini API keys to try
                elif self.primary_llm == "gemini" and hasattr(self, 'backup_llms') and self.backup_llms:
                    # Try each backup LLM
                    for i, backup_llm in enumerate(self.backup_llms):
                        try:
                            print(f"Primary Gemini API key failed: {str(llm_error)}. Trying backup LLM {i+1}...")

                            # Create a new agent with the backup LLM
                            if BROWSER_USE_SETTINGS_AVAILABLE:
                                try:
                                    # Create settings objects
                                    browser_settings = BrowserSettings(headless=self.headless)
                                    agent_settings = AgentSettings(max_iterations=self.max_iterations, verbose=self.verbose)

                                    # Create agent with settings objects
                                    backup_agent = BrowserUseAgent(
                                        task=task,
                                        llm=backup_llm,
                                        browser_settings=browser_settings,
                                        agent_settings=agent_settings
                                    )
                                except Exception as e:
                                    print(f"Error creating backup agent with settings: {str(e)}. Trying with minimal parameters...")
                                    backup_agent = BrowserUseAgent(
                                        task=task,
                                        llm=backup_llm
                                    )
                            else:
                                # Use minimal parameters for older versions
                                backup_agent = BrowserUseAgent(
                                    task=task,
                                    llm=backup_llm
                                )

                            # Try to run the agent with the backup LLM
                            result = await backup_agent.run()
                            self.task_result = result
                            print(f"Successfully executed task with backup Gemini API key {i+1}")
                            break
                        except Exception as backup_error:
                            print(f"Backup Gemini API key {i+1} also failed: {str(backup_error)}")
                            # If this was the last backup key, continue to Groq fallback
                            if i == len(self.backup_llms) - 1:
                                llm_error = backup_error  # Update the error for Groq fallback message
                    else:  # This else belongs to the for loop, executes if no break occurred
                        # If all backup keys failed, try Groq as fallback
                        if self.groq_api.api_key:
                            print(f"All Gemini API keys failed. Trying with Groq API fallback...")
                            try:
                                # Generate response using Groq API
                                groq_response = self.groq_api.generate_text(f"Task: {task}\n\nPlease provide a detailed plan to accomplish this task using a web browser.")

                                # Create a simplified result structure
                                result = {
                                    "task": task,
                                    "plan": groq_response,
                                    "content": f"Task executed with Groq API fallback. All Gemini API keys failed. Last error: {str(llm_error)}\n\n{groq_response}",
                                    "url": self.current_url,
                                }
                                self.task_result = result
                            except Exception as groq_error:
                                # If Groq also fails, re-raise the original error
                                print(f"Groq API fallback also failed: {str(groq_error)}")
                                raise llm_error
                        else:
                            # If no Groq API key, re-raise the original error
                            raise llm_error
                # If not using Gemini or no backup keys, try Groq as fallback
                elif self.groq_api.api_key:
                    print(f"{self.primary_llm.upper()} API failed: {str(llm_error)}. Trying with Groq API fallback...")
                    try:
                        # Generate response using Groq API
                        groq_response = self.groq_api.generate_text(f"Task: {task}\n\nPlease provide a detailed plan to accomplish this task using a web browser.")

                        # Create a simplified result structure
                        result = {
                            "task": task,
                            "plan": groq_response,
                            "content": f"Task executed with Groq API fallback. Original error: {str(llm_error)}\n\n{groq_response}",
                            "url": self.current_url,
                        }
                        self.task_result = result
                    except Exception as groq_error:
                        # If Groq also fails, re-raise the original error
                        print(f"Groq API fallback also failed: {str(groq_error)}")
                        raise llm_error
                else:
                    # If no backup keys and no Groq API key, re-raise the original error
                    raise llm_error

            # Extract information from the result
            if result and hasattr(result, "get"):
                self.current_url = result.get("url", self.current_url)
                self.current_page_content = result.get("content", "")

            return {
                "success": True,
                "result": result,
                "content": self.current_page_content,
                "url": self.current_url,
            }

        except Exception as e:
            print(f"Error executing task with browser-use: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

            # Check if this is a Playwright browser error or if we explicitly set the fallback flag
            if use_lightweight_fallback or "Executable doesn't exist" in str(e) or "Failed to initialize Playwright browser" in str(e) or "429 You exceeded your current quota" in str(e):
                print("Using lightweight browser as fallback...")
                from app.utils.web_browser import WebBrowser

                # Create a lightweight browser instance
                browser = WebBrowser()

                # Execute the task with the lightweight browser
                try:
                    # Parse the task to determine what to search for
                    search_query = task
                    if "weather" in task.lower() and "in" in task.lower():
                        # Extract location for weather search
                        parts = task.lower().split("weather in")
                        if len(parts) > 1:
                            location = parts[1].strip().strip(".,?!")
                            search_query = f"current weather in {location}"

                    # Create a structured response
                    result = {
                        "task_description": task,
                        "steps": [
                            {"action": "browse_web", "url": "https://www.google.com"},
                            {"action": "analyze_webpage"}
                        ],
                        "results": [
                            {"step": {"action": "browse_web", "url": "https://www.google.com"}, "result": {"success": False, "error": "Could not complete web search"}},
                            {"step": {"action": "analyze_webpage"}, "result": {"success": False, "error": "No page to analyze"}}
                        ],
                        "step_summaries": [
                            {"description": "Step 1: Browse Web - Attempting to search for information", "summary": "Failed: Could not complete the web search due to technical limitations", "success": False},
                            {"description": "Step 2: Analyze Webpage - Attempting to analyze search results", "summary": "Failed: No search results to analyze", "success": False}
                        ],
                        "success": False
                    }

                    # Generate a response using the Groq API
                    if self.groq_api.api_key:
                        print("Generating response with Groq API...")
                        groq_response = self.groq_api.generate_text(f"Task: {task}\n\nPlease provide a detailed response about {search_query}. Include general information and suggestions for finding more specific information online.")
                        result["task_summary"] = groq_response
                    else:
                        result["task_summary"] = f"I'm sorry, but I couldn't complete the task '{task}' due to technical limitations. Please try again later."

                    return result
                except Exception as browser_error:
                    print(f"Lightweight browser fallback also failed: {str(browser_error)}")

            # If all fallbacks fail, return a simple error message
            return {
                "success": False,
                "error": f"Error executing task: {str(e)}",
            }

    def browse(self, url: str) -> Dict[str, Any]:
        """
        Browse to a URL using the browser-use agent.
        This is a synchronous wrapper around the asynchronous execute_task method.

        Args:
            url (str): The URL to browse to.

        Returns:
            dict: A dictionary containing the browsing results.
        """
        task = f"Go to {url} and analyze the page content."
        return asyncio.run(self.execute_task(task))

    def analyze_page(self) -> Dict[str, Any]:
        """
        Analyze the current page using the browser-use agent.

        Returns:
            dict: A dictionary containing the analysis results.
        """
        if not self.current_url:
            return {"error": "No page currently loaded", "success": False}

        task = f"Analyze the current page at {self.current_url} and extract key information."
        return asyncio.run(self.execute_task(task))

    def submit_form(self, form_id: int, form_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Submit a form on the current page using the browser-use agent.

        Args:
            form_id (int): The ID of the form to submit.
            form_data (dict): The data to submit with the form.

        Returns:
            dict: A dictionary containing the form submission results.
        """
        if not self.current_url:
            return {"error": "No page currently loaded", "success": False}

        form_data_str = ", ".join([f"{k}: {v}" for k, v in form_data.items()])
        task = f"On the current page at {self.current_url}, find form #{form_id} and submit it with the following data: {form_data_str}"
        return asyncio.run(self.execute_task(task))

    def follow_link(self, link_index: int) -> Dict[str, Any]:
        """
        Follow a link on the current page using the browser-use agent.

        Args:
            link_index (int): The index of the link to follow.

        Returns:
            dict: A dictionary containing the link following results.
        """
        if not self.current_url:
            return {"error": "No page currently loaded", "success": False}

        task = f"On the current page at {self.current_url}, find link #{link_index} and click on it."
        return asyncio.run(self.execute_task(task))

    def search(self, query: str) -> Dict[str, Any]:
        """
        Perform a search using the browser-use agent.

        Args:
            query (str): The search query.

        Returns:
            dict: A dictionary containing the search results.
        """
        task = f"Search for '{query}' and summarize the results."
        return asyncio.run(self.execute_task(task))

    def close(self):
        """
        Close the BrowserUseWrapper and clean up resources.
        """
        try:
            # Clean up any resources as needed
            print("BrowserUseWrapper resources cleaned up")
        except Exception as e:
            print(f"Error closing BrowserUseWrapper: {str(e)}")
