"""
API endpoints for executing code in a sandboxed environment.
"""

import os
import sys
import json
import uuid
import tempfile
import subprocess
import traceback
from flask import jsonify, request, Blueprint, current_app
from werkzeug.utils import secure_filename
from app.services.simple_code_executor import simple_executor

# Create Blueprint for Code Executor API
code_executor_bp = Blueprint('code_executor', __name__, url_prefix='/api/code-executor')

# Define the maximum execution time (in seconds)
MAX_EXECUTION_TIME = 30

@code_executor_bp.route('/execute', methods=['POST'])
def execute_code():
    """
    Execute code in a sandboxed environment.

    Returns:
        JSON response with execution results
    """
    try:
        # Get request data
        data = request.json
        code = data.get('code', '')
        language = data.get('language', 'python')

        if not code:
            return jsonify({
                'success': False,
                'error': 'No code provided'
            })

        # Currently only support Python
        if language.lower() != 'python':
            return jsonify({
                'success': False,
                'error': f'Language {language} is not supported yet. Only Python is supported.'
            })

        # Create a temporary directory for execution
        temp_dir = tempfile.mkdtemp(prefix='code_executor_')

        try:
            # Create a unique ID for this execution
            execution_id = str(uuid.uuid4())

            # Create a temporary file for the code
            file_path = os.path.join(temp_dir, f'code_{execution_id}.py')

            # Write the code to the file
            with open(file_path, 'w') as f:
                f.write(code)

            # Execute the code in a subprocess with timeout
            result = execute_python_code(file_path)

            return jsonify({
                'success': True,
                'result': result
            })

        finally:
            # Clean up temporary files
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary files: {str(cleanup_error)}")

    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': f"Failed to execute code: {str(e)}",
            'traceback': traceback_str
        })

def execute_python_code(file_path):
    """
    Execute Python code in a subprocess with timeout.

    Args:
        file_path (str): Path to the Python file

    Returns:
        dict: Execution results
    """
    try:
        # Execute the code in a subprocess with timeout
        process = subprocess.Popen(
            [sys.executable, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=MAX_EXECUTION_TIME)
            return {
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': process.returncode
            }
        except subprocess.TimeoutExpired:
            # Kill the process if it times out
            process.kill()
            stdout, stderr = process.communicate()
            return {
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': -1,
                'timeout': True
            }

    except Exception as e:
        return {
            'stdout': '',
            'stderr': f"Error executing code: {str(e)}",
            'exit_code': -1
        }

@code_executor_bp.route('/execute-project', methods=['POST'])
def execute_project():
    """
    Execute a project with multiple files.

    Returns:
        JSON response with execution results
    """
    try:
        # Get request data
        data = request.json
        files = data.get('files', [])

        if not files:
            return jsonify({
                'success': False,
                'error': 'No files provided'
            })

        # Execute the project using the simple executor
        result = simple_executor.execute_project(files)

        return jsonify(result)

    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': f"Failed to execute project: {str(e)}",
            'traceback': traceback_str
        })

@code_executor_bp.route('/status/<project_id>', methods=['GET'])
def get_execution_status(project_id):
    """
    Get the execution status of a project

    Args:
        project_id (str): Project ID

    Returns:
        JSON response with execution status
    """
    try:
        # Get the execution status
        result = simple_executor.get_execution_status(project_id)

        return jsonify(result)

    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': f"Error getting execution status: {str(e)}",
            'traceback': traceback_str
        })

@code_executor_bp.route('/stop/<project_id>', methods=['POST'])
def stop_execution(project_id):
    """
    Stop code execution

    Args:
        project_id (str): Project ID

    Returns:
        JSON response with stop result
    """
    try:
        # Stop the execution
        result = simple_executor.stop_execution(project_id)

        return jsonify(result)

    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': f"Error stopping execution: {str(e)}",
            'traceback': traceback_str
        })
