"""
API endpoints for the Prime Agent functionality.
"""

import json
import traceback
from datetime import datetime
from flask import jsonify, request, Blueprint
from app.agents.super_agent import SuperAgent
from app.utils.session_manager import SessionManager
from app.agents.tasks.task_factory import TaskFactory
from app.utils.web_browser import WebBrowser
from app.utils.mcp_client import MCPClient
from app.services.credit_service import CreditService

# Create Blueprint for Super Agent API
super_agent_bp = Blueprint('super_agent', __name__, url_prefix='/api/super-agent')

# Global instances to maintain session state
_super_agent_instance = None
_mcp_client = MCPClient(base_url="http://localhost:5011")

print(f"Initialized MCP client with base URL: http://localhost:5011")

def get_super_agent(use_browser_use=False, use_advanced_browser=False):
    """
    Get or create a Prime Agent instance.

    Args:
        use_browser_use (bool, optional): Whether to use the browser-use library for web browsing. Defaults to False.
        use_advanced_browser (bool, optional): Whether to use advanced browser capabilities. Defaults to False.

    Returns:
        SuperAgent: The Prime Agent instance
    """
    global _super_agent_instance
    if _super_agent_instance is None:
        _super_agent_instance = SuperAgent(use_browser_use=use_browser_use, use_advanced_browser=use_advanced_browser)
    return _super_agent_instance


def generate_planning_steps(task_description, agent):
    """
    Generate planning steps for a task.

    Args:
        task_description (str): The task description
        agent: The agent instance

    Returns:
        list: A list of planning steps
    """
    try:
        # Define the planning prompt
        planning_prompt = f"""
        I need to plan how to execute the following task: "{task_description}"

        Please provide a detailed step-by-step plan for how to approach this task. Include:
        1. Initial information gathering steps
        2. Research sources to consult
        3. Specific actions to take
        4. How to organize and present the information
        5. Any potential challenges and how to address them

        Format your response as a list of steps, with each step having a clear action and rationale.
        """

        # Try to generate planning steps with Gemini API first, fall back to Groq API if needed
        try:
            planning_text = agent.gemini_api.generate_text(planning_prompt)
        except Exception as e:
            print(f"Error generating planning steps with Gemini API: {str(e)}")
            if hasattr(agent, 'groq_api') and agent.groq_api and agent.groq_api.api_key:
                print("Falling back to Groq API for planning steps")
                planning_text = agent.groq_api.generate_text(planning_prompt)
            else:
                raise

        # Parse the planning text into steps
        planning_steps = []
        lines = planning_text.strip().split('\n')
        current_step = ""
        step_number = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a new step (starts with a number or has 'Step' in it)
            if line.startswith(f"{step_number}.") or line.startswith(f"Step {step_number}:") or line.startswith(f"Step {step_number}."):
                if current_step:
                    planning_steps.append(current_step)
                current_step = line
                step_number += 1
            else:
                current_step += "\n" + line

        # Add the last step if there is one
        if current_step:
            planning_steps.append(current_step)

        # If we couldn't parse steps properly, just split by newlines
        if not planning_steps:
            planning_steps = [line for line in lines if line]

        return planning_steps
    except Exception as e:
        print(f"Error generating planning steps: {str(e)}")
        return [f"Error generating planning steps: {str(e)}"]

def browse_web():
    """
    Browse to a URL using the Prime Agent.

    Returns:
        dict: A dictionary containing the page content
    """
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({"error": "URL is required", "success": False}), 400

        agent = get_super_agent()
        result = agent.browse_web(url)

        return jsonify(result)
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            "error": f"Error browsing web: {str(e)}",
            "traceback": traceback_str,
            "success": False
        }), 500

def submit_form():
    """
    Submit a form with the provided data.

    Returns:
        dict: A dictionary containing the response
    """
    try:
        form_id = request.json.get('form_id', 0)
        form_data = request.json.get('form_data', {})

        agent = get_super_agent()
        result = agent.submit_form(form_id, form_data)

        return jsonify(result)
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            "error": f"Error submitting form: {str(e)}",
            "traceback": traceback_str,
            "success": False
        }), 500

def follow_link():
    """
    Follow a link on the current page.

    Returns:
        dict: A dictionary containing the response
    """
    try:
        link_index = request.json.get('link_index', 0)

        agent = get_super_agent()
        result = agent.follow_link(link_index)

        return jsonify(result)
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            "error": f"Error following link: {str(e)}",
            "traceback": traceback_str,
            "success": False
        }), 500

# This function is replaced by follow_link

def generate_code():
    """
    Generate code using the Prime Agent.

    Returns:
        dict: A dictionary containing the generated code
    """
    try:
        prompt = request.json.get('prompt')
        language = request.json.get('language', 'javascript')

        if not prompt:
            return jsonify({"error": "Prompt is required", "success": False}), 400

        agent = get_super_agent()
        result = agent.generate_code(prompt, language)

        return jsonify(result)
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            "error": f"Error generating code: {str(e)}",
            "traceback": traceback_str,
            "success": False
        }), 500

def analyze_webpage():
    """
    Analyze the current webpage.

    Returns:
        dict: A dictionary containing the analysis results
    """
    try:
        agent = get_super_agent()
        result = agent.analyze_webpage()

        return jsonify(result)
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            "error": f"Error analyzing webpage: {str(e)}",
            "traceback": traceback_str,
            "success": False
        }), 500

from app.agents.tasks.task_factory import TaskFactory
from app.utils.session_manager import SessionManager
from app.utils.web_browser import WebBrowser
from app.utils.simple_orchestrator import SimpleOrchestrator

@super_agent_bp.route('/task-status', methods=['GET'])
def get_task_status():
    """
    Get the status of a task.

    Returns:
        dict: A dictionary containing the task status and result
    """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({"error": "Session ID is required", "success": False}), 400

        # Get the session
        session_manager = SessionManager()
        session = session_manager.get_session(session_id)

        if not session:
            return jsonify({"error": "Session not found", "success": False}), 404

        # Get the session history
        history = session.get_history(limit=1)  # Get the most recent history item

        # Check if there's a task result
        task_result = None
        for i in range(len(session.get_history())):
            key = f"task_result_{i}"
            if session.has_data(key):
                task_result = session.get_data(key)
                break

        # Determine the task status
        status = "in_progress"
        if task_result and task_result.get('success', False):
            status = "complete"

        # Get the thinking steps
        thinking_steps = []
        if task_result and task_result.get('planning_steps'):
            thinking_steps = task_result.get('planning_steps')

        # Get the progress updates from the task manager
        progress = []
        if 'task_id' in session.data:
            task_id = session.data['task_id']
            from app.prime_agent.task_manager import task_manager
            progress = task_manager.get_task_progress(task_id)

        return jsonify({
            "success": True,
            "status": status,
            "thinking_steps": thinking_steps,
            "progress": progress,
            "result": task_result,
            "last_activity": session.last_activity.isoformat()
        })
    except Exception as e:
        print(f"Error getting task status: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500

@super_agent_bp.route('/execute-task', methods=['POST'])
def execute_task():
    """
    Execute a complex task described in natural language.

    Returns:
        dict: A dictionary containing the task execution results
    """
    try:
        print("Received execute_task request")
        print("Request JSON:", request.json)

        task_description = request.json.get('task_description')
        use_browser_use = request.json.get('use_browser_use', False)
        use_advanced_browser = request.json.get('use_advanced_browser', False)
        session_id = request.json.get('session_id')

        if not task_description:
            return jsonify({"error": "Task description is required", "success": False}), 400

        # Get user ID from session or request
        user_id = request.json.get('user_id', 'anonymous_user')

        # Initialize credit service for token-based consumption
        credit_service = CreditService()

        # Determine task type for minimum charge calculation
        if use_advanced_browser or use_browser_use or len(task_description) > 200:
            task_type = 'prime_agent_complex'  # Higher minimum for complex tasks
        else:
            task_type = 'prime_agent_basic'    # Lower minimum for basic tasks

        # Pre-consume minimum credits (will be adjusted after execution)
        pre_credit_result = credit_service.consume_credits(
            user_id=user_id,
            task_type=task_type,
            input_text=task_description,
            output_text="",  # Will update after execution
            use_token_based=True
        )

        if not pre_credit_result['success']:
            return jsonify({
                'success': False,
                'error': pre_credit_result.get('error', 'Insufficient credits'),
                'credits_consumed': 0,
                'remaining_credits': pre_credit_result.get('remaining_credits', 0),
                'credits_needed': pre_credit_result.get('credits_needed', 0)
            }), 402  # Payment Required

        print(f"Executing task: {task_description}")
        print(f"Using browser-use: {use_browser_use}")
        print(f"Using advanced browser: {use_advanced_browser}")

        # Get or create session
        session_manager = SessionManager()
        if session_id:
            session = session_manager.get_session(session_id)
            if not session:
                session = session_manager.create_session()
                session_id = session.session_id
        else:
            session = session_manager.create_session()
            session_id = session.session_id

        # Create a task in the task manager
        from app.prime_agent.task_manager import task_manager
        task_id = task_manager.create_task(task_description, use_advanced_browser)

        # Store the task ID in the session
        session.data['task_id'] = task_id

        # Update session with task details
        session.add_to_history("task_execution", {
            "task_description": task_description,
            "use_browser_use": use_browser_use,
            "use_advanced_browser": use_advanced_browser,
            "task_id": task_id,
            "timestamp": session.last_activity.isoformat()
        })
        session_manager.update_session(session)

        # Initialize the Prime Agent
        agent = get_super_agent(use_browser_use=use_browser_use, use_advanced_browser=use_advanced_browser)

        # Generate planning steps
        planning_steps = generate_planning_steps(task_description, agent)

        # Check if we should use the simple orchestrator
        use_simple_orchestrator = request.json.get('use_simple_orchestrator', True)

        if use_simple_orchestrator:
            print("Using simple orchestrator with advanced browser capabilities")
            # Initialize the simple orchestrator with advanced browser capabilities
            simple_orchestrator = SimpleOrchestrator()
            # Execute the task using the simple orchestrator
            result = simple_orchestrator.execute_task(task_description)
        else:
            # Check if we have a task-specific handler
            task_factory = TaskFactory()
            task_handler = task_factory.create_task(
                task_description=task_description,
                web_browser=WebBrowser(use_advanced_browser=use_advanced_browser),
                gemini_api=agent.gemini_api,
                groq_api=agent.groq_api if hasattr(agent, 'groq_api') else None
            )

            # If we have a task-specific handler, use it
            if task_handler:
                print(f"Using task-specific handler: {task_handler.__class__.__name__}")
                result = task_handler.execute()
            else:
                # Otherwise, use the generic task execution
                print("Using generic task execution")
                result = agent.execute_task(task_description)

        # Convert result to a serializable format
        try:
            # Try to serialize the result
            serialized_result = json.dumps(result, indent=2)
            print(f"Task execution result: {serialized_result}")
        except TypeError as e:
            # If serialization fails, log the error and create a simplified result
            print(f"Error serializing result: {str(e)}")
            # Create a simplified version of the result that can be serialized
            if isinstance(result, dict):
                # Keep only serializable parts
                simplified_result = {}
                for key, value in result.items():
                    try:
                        # Test if this key-value pair can be serialized
                        json.dumps({key: value})
                        simplified_result[key] = value
                    except (TypeError, OverflowError):
                        # If not serializable, convert to string or exclude
                        try:
                            simplified_result[key] = str(value)
                        except:
                            simplified_result[key] = "<non-serializable value>"
                result = simplified_result
            else:
                # If not a dict, convert the entire result to a string
                result = {"result": str(result)}

        # Ensure we have a valid response
        if result is None:
            print("Task execution returned None")
            return jsonify({
                "error": "Task execution returned None",
                "success": False,
                "task_description": task_description
            }), 500

        # Add task description to result if not present
        if 'task_description' not in result:
            result['task_description'] = task_description

        # Ensure success field is present
        if 'success' not in result:
            result['success'] = False

        # Add debug information about screenshots
        if 'results' in result and isinstance(result['results'], list):
            screenshot_count = 0
            for item in result['results']:
                if 'result' in item and 'screenshot' in item['result']:
                    screenshot_count += 1
                    print(f"DEBUG: Found screenshot in result, size: {len(item['result']['screenshot'])} bytes")
            print(f"DEBUG: Total screenshots found: {screenshot_count}")
        else:
            print("DEBUG: No results array found in result or results is not a list")

        # Add session ID and planning steps to result
        result['session_id'] = session_id
        result['planning_steps'] = planning_steps

        # Calculate final token-based credits after task execution
        output_text = str(result.get('result', ''))
        execution_time = (datetime.now() - datetime.now()).total_seconds() / 60  # Placeholder for actual timing
        tool_calls = len(result.get('results', [])) if 'results' in result else 0

        # Calculate actual credits consumed based on tokens
        final_credit_result = credit_service.calculate_token_based_credits(
            input_text=task_description,
            output_text=output_text,
            task_type=task_type,
            execution_time_minutes=execution_time,
            tool_calls=tool_calls,
            image_count=0  # Could be enhanced to count actual images
        )

        # Get updated credit status after consumption
        updated_credit_status = credit_service.get_user_credits(user_id)

        # Add credit consumption info to response
        result['credits_consumed'] = pre_credit_result['credits_consumed']
        result['remaining_credits'] = updated_credit_status.get('remaining', 50)
        result['credit_breakdown'] = final_credit_result  # Include detailed breakdown

        # Update session with task result
        session.set_data(f"task_result_{len(session.get_history())}", result)
        session_manager.update_session(session)

        print("Returning result to client:", json.dumps(result, indent=2)[:500])
        return jsonify(result)
    except Exception as e:
        traceback_str = traceback.format_exc()
        print(f"Error executing task: {str(e)}\n{traceback_str}")
        return jsonify({
            "error": f"Error executing task: {str(e)}",
            "traceback": traceback_str,
            "success": False,
            "task_description": task_description if 'task_description' in locals() else 'Unknown'
        }), 500

def get_session_history():
    """
    Get the history of a specific session.

    Returns:
        dict: A dictionary containing the session history
    """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({"error": "Session ID is required", "success": False}), 400

        # Get the session
        session_manager = SessionManager()
        session = session_manager.get_session(session_id)

        if not session:
            return jsonify({"error": "Session not found", "success": False}), 404

        # Get the session history
        history = session.get_history(limit=0)  # Get all history items

        return jsonify({
            "success": True,
            "history": history,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat()
        })
    except Exception as e:
        print(f"Error getting session history: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500

def clear_session():
    """
    Clear a specific session.

    Returns:
        dict: A dictionary indicating success or failure
    """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({"error": "Session ID is required", "success": False}), 400

        # Get the session manager
        session_manager = SessionManager()

        # Delete the session
        session_manager.delete_session(session_id)

        return jsonify({"success": True, "message": "Session cleared successfully"})
    except Exception as e:
        print(f"Error clearing session: {str(e)}")
        return jsonify({"error": str(e), "success": False}), 500

def get_code_snippets():
    """
    Get the generated code snippets.

    Returns:
        dict: A dictionary containing the code snippets
    """
    try:
        agent = get_super_agent()
        snippets = agent.get_code_snippets()

        return jsonify({
            "snippets": snippets,
            "success": True
        })
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            "error": f"Error getting code snippets: {str(e)}",
            "traceback": traceback_str,
            "success": False
        }), 500

def reset_agent():
    """
    Reset the Prime Agent.

    Returns:
        dict: A dictionary indicating success or failure
    """
    try:
        use_browser_use = request.json.get('use_browser_use', False)

        global _super_agent_instance
        if _super_agent_instance:
            if hasattr(_super_agent_instance, 'close'):
                _super_agent_instance.close()
            _super_agent_instance = None

        # Create a new instance if requested
        if request.json.get('create_new', False):
            _super_agent_instance = SuperAgent(use_browser_use=use_browser_use)

        return jsonify({
            "message": "Prime Agent reset successfully",
            "success": True
        })
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            "error": f"Error resetting Prime Agent: {str(e)}",
            "traceback": traceback_str,
            "success": False
        }), 500

def process_task_summary_with_mcp(task_summary):
    """
    Process the task summary to include images from the MCP server.

    Args:
        task_summary (str): The task summary text with image placeholders

    Returns:
        str: The processed task summary with image URLs
    """
    global _mcp_client

    print(f"Processing task summary with MCP: {task_summary[:100]}...")

    # Import the ImageExtractor class
    from app.utils.image_extractor import ImageExtractor

    # Create an instance of the ImageExtractor
    image_extractor = ImageExtractor(mcp_client=_mcp_client)
    print("Created ImageExtractor instance for processing task summary")

    # Process the summary with a dummy section_images dictionary
    # This will use direct image search for each placeholder
    processed_summary = image_extractor.process_summary_with_images(task_summary, {})

    print(f"Final summary with images: {processed_summary[:200]}...")
    return processed_summary


@super_agent_bp.route('/generate-project', methods=['POST'])
def generate_project():
    """
    Generate a code project based on the provided prompt.

    Returns:
        JSON response with the generated project files
    """
    try:
        # Get request data
        data = request.json
        prompt = data.get('prompt', '')
        project_type = data.get('project_type', 'web')
        complexity = data.get('complexity', 'simple')

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'No prompt provided'
            })

        print(f"Generating project for prompt: {prompt}")
        print(f"Project type: {project_type}, Complexity: {complexity}")

        # Get the Prime Agent instance
        agent = get_super_agent()

        # Generate the project files directly using the Prime Agent's method
        response = agent.generate_code_project(prompt, project_type, complexity)

        # If the response is None, return an error
        if response is None:
            return jsonify({
                'success': False,
                'error': 'Failed to generate project'
            })

        # Return the generated files
        return jsonify({
            'success': True,
            'files': response.get('files', [])
        })

    except Exception as e:
        print(f"Error generating project: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f"Failed to generate project: {str(e)}"
        })


# Removed fallback implementation since it's now in the SuperAgent class
def generate_fallback_project(prompt, project_type, complexity):
    """
    Generate a fallback project for testing purposes.

    Args:
        prompt (str): The project description
        project_type (str): The type of project
        complexity (str): The complexity level

    Returns:
        list: A list of file objects with name and content
    """
    # For web projects
    if project_type == 'web':
        return [
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
    # For script projects
    elif project_type == 'script':
        return [
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
                'name': 'utils.py',
                'content': f'''#!/usr/bin/env python3
"""
Utility functions for the project.
"""

import os
import sys
import datetime
import random
import string


def generate_id(length=8):
    """Generate a random ID."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def get_timestamp():
    """Get the current timestamp."""
    return datetime.datetime.now().isoformat()


def create_directory(directory):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        return True
    return False


def read_file(filename):
    """Read the contents of a file."""
    if not os.path.exists(filename):
        return None

    with open(filename, 'r') as f:
        return f.read()


def write_file(filename, content):
    """Write content to a file."""
    with open(filename, 'w') as f:
        f.write(content)
    return True


def append_to_file(filename, content):
    """Append content to a file."""
    with open(filename, 'a') as f:
        f.write(content)
    return True


def log_message(message, level='INFO'):
    """Log a message with timestamp."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{{level}}] {{timestamp}} - {{message}}")


def parse_arguments():
    """Parse command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description='Project utility script')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--output', '-o', type=str, help='Output file')
    parser.add_argument('--input', '-i', type=str, help='Input file')

    return parser.parse_args()


def main():
    """Main function for testing utilities."""
    args = parse_arguments()

    log_message("Utility script started")

    if args.verbose:
        log_message("Verbose mode enabled", "DEBUG")

    # Test ID generation
    test_id = generate_id()
    log_message(f"Generated ID: {{test_id}}")

    # Test directory creation
    test_dir = 'test_directory'
    if create_directory(test_dir):
        log_message(f"Created directory: {{test_dir}}")
    else:
        log_message(f"Directory already exists: {{test_dir}}", "WARNING")

    # Test file operations
    test_file = os.path.join(test_dir, 'test_file.txt')
    write_file(test_file, f"Test content generated at {{get_timestamp()}}\n")
    log_message(f"Created file: {{test_file}}")

    append_to_file(test_file, f"Additional content appended at {{get_timestamp()}}\n")
    log_message(f"Appended to file: {{test_file}}")

    content = read_file(test_file)
    log_message(f"File content:\n{{content}}")

    log_message("Utility script completed")


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

# Install dependencies (if any)
pip install -r requirements.txt
```

## Usage
```bash
# Run the main script
python main.py

# Run the utility script
python utils.py --verbose
```

## Project Structure
```
.
├── main.py          # Main script
├── utils.py         # Utility functions
├── README.md        # Project documentation
└── project_data.json # Generated project data
```

## License
MIT
'''
            }
        ]


# Register routes
super_agent_bp.add_url_rule('/browse', 'browse_web', browse_web, methods=['POST'])
super_agent_bp.add_url_rule('/submit-form', 'submit_form', submit_form, methods=['POST'])
super_agent_bp.add_url_rule('/follow-link', 'follow_link', follow_link, methods=['POST'])
super_agent_bp.add_url_rule('/generate-code', 'generate_code', generate_code, methods=['POST'])
super_agent_bp.add_url_rule('/analyze-webpage', 'analyze_webpage', analyze_webpage, methods=['POST'])
super_agent_bp.add_url_rule('/session-history', 'get_session_history', get_session_history, methods=['GET'])
super_agent_bp.add_url_rule('/clear-session', 'clear_session', clear_session, methods=['DELETE'])
super_agent_bp.add_url_rule('/code-snippets', 'get_code_snippets', get_code_snippets, methods=['GET'])
super_agent_bp.add_url_rule('/reset', 'reset_agent', reset_agent, methods=['POST'])