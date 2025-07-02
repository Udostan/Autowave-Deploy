"""
Simple Code Executor Service

This module provides a simplified service for executing code in a sandboxed environment.
It focuses on reliability rather than advanced features.
"""

import os
import sys
import uuid
import time
import logging
import threading
import subprocess
import tempfile
import shutil
# Removed unused imports: base64, io, PIL.Image

logger = logging.getLogger(__name__)

class SimpleCodeExecutor:
    """
    A simplified code executor that focuses on reliability
    """

    def __init__(self):
        """
        Initialize the simple code executor
        """
        self.running_processes = {}
        self.output_cache = {}
        self.project_dirs = {}

    def execute_project(self, files):
        """
        Execute a project with multiple files

        Args:
            files (list): List of file objects with name and content

        Returns:
            dict: Execution result with project_id and success status
        """
        try:
            # Create a unique project ID
            project_id = str(uuid.uuid4())

            # Create a temporary directory for the project
            # Use environment variable for temp directory if available
            temp_base = os.environ.get('TEMP_DIR', '/tmp') if os.environ.get('DATA_DIR') else None
            project_dir = tempfile.mkdtemp(dir=temp_base)
            self.project_dirs[project_id] = project_dir

            # Write files to the project directory
            for file in files:
                file_path = os.path.join(project_dir, file['name'])
                # Create directories if needed
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(file['content'])

            # Initialize output cache
            self.output_cache[project_id] = {
                'output': '',
                'images': [],
                'status': 'initializing',
                'last_update': time.time()
            }

            # Find the main file to execute
            main_file = self._find_main_file(project_dir)
            if not main_file:
                self.output_cache[project_id]['output'] += "ERROR: Could not find a main file to execute.\n"
                self.output_cache[project_id]['status'] = 'error'
                return {'success': False, 'project_id': project_id, 'error': 'No main file found'}

            # Start execution in a separate thread
            threading.Thread(target=self._execute_project_thread,
                            args=(project_id, project_dir, main_file)).start()

            return {'success': True, 'project_id': project_id}

        except Exception as e:
            logger.error(f"Error executing project: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _find_main_file(self, project_dir):
        """
        Find the main file to execute in a project

        Args:
            project_dir (str): Path to the project directory

        Returns:
            str or None: Path to the main file or None if not found
        """
        # List of possible main file names in order of priority
        main_file_names = [
            'main.py',
            'app.py',
            'run.py',
            'snake_game.py',
            'game.py',
            'calculator.py',
            'index.py'
        ]

        # Check for files with if __name__ == '__main__'
        python_files = []
        for root, _, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        # First, look for specific main file names
        for name in main_file_names:
            for file_path in python_files:
                if os.path.basename(file_path) == name:
                    return file_path

        # Then, look for files with if __name__ == '__main__'
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if "__name__" in content and "__main__" in content:
                        return file_path
            except:
                pass

        # If no main file found, return the first Python file
        if python_files:
            return python_files[0]

        return None

    def _execute_project_thread(self, project_id, project_dir, main_file):
        """
        Execute a project in a separate thread

        Args:
            project_id (str): Project ID
            project_dir (str): Path to the project directory
            main_file (str): Path to the main file to execute
        """
        try:
            # Update status
            self.output_cache[project_id]['status'] = 'running'
            self.output_cache[project_id]['output'] += f"Executing {os.path.basename(main_file)}...\n"

            # Prepare environment variables
            env = os.environ.copy()

            # Fix Flask environment variables
            env['FLASK_DEBUG'] = 'True'
            # Remove deprecated FLASK_ENV to prevent warnings
            if 'FLASK_ENV' in env:
                del env['FLASK_ENV']
            # Set Python to not buffer output for better real-time feedback
            env['PYTHONUNBUFFERED'] = '1'

            # For Pygame applications, set SDL_VIDEODRIVER to 'dummy'
            if self._is_pygame_project(project_dir):
                self.output_cache[project_id]['output'] += "Detected Pygame application. Setting SDL_VIDEODRIVER to 'dummy' for headless operation.\n"
                env['SDL_VIDEODRIVER'] = 'dummy'

            # For Flask applications, modify the code to use a different port
            if self._is_flask_project(project_dir):
                self.output_cache[project_id]['output'] += "Detected Flask application. Modifying to use port 5002 to avoid conflicts.\n"
                self._modify_flask_port(main_file)

            # Check if we're in a cloud environment
            is_cloud_env = os.environ.get('VERCEL') or os.environ.get('NETLIFY')

            # In cloud environments, use a more restricted execution approach
            if is_cloud_env:
                self.output_cache[project_id]['output'] += "Running in cloud environment with restricted execution.\n"

                # Use a shorter timeout for cloud environments
                timeout = 15  # 15 seconds timeout for cloud environments

                try:
                    # Use check_output instead of Popen for simpler process management
                    result = subprocess.check_output(
                        [sys.executable, main_file],
                        cwd=project_dir,
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=timeout,
                        env=env
                    )
                    self.output_cache[project_id]['output'] += result
                    self.output_cache[project_id]['status'] = 'completed'
                    return
                except subprocess.TimeoutExpired as e:
                    self.output_cache[project_id]['output'] += f"\nExecution timed out after {timeout} seconds.\n"
                    self.output_cache[project_id]['status'] = 'error'
                    return
                except subprocess.CalledProcessError as e:
                    self.output_cache[project_id]['output'] += f"\nExecution failed with exit code {e.returncode}.\n"
                    self.output_cache[project_id]['output'] += e.output
                    self.output_cache[project_id]['status'] = 'error'
                    return

            # For non-cloud environments, use the standard approach with Popen
            process = subprocess.Popen(
                [sys.executable, main_file],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )

            # Store the process
            self.running_processes[project_id] = process

            # Start threads to read output
            stdout_thread = threading.Thread(
                target=self._read_output,
                args=(process.stdout, project_id, 'stdout')
            )
            stderr_thread = threading.Thread(
                target=self._read_output,
                args=(process.stderr, project_id, 'stderr')
            )

            stdout_thread.start()
            stderr_thread.start()

            # Wait for the process to complete (with a timeout)
            try:
                process.wait(timeout=30)  # 30 seconds timeout
            except subprocess.TimeoutExpired:
                self.output_cache[project_id]['output'] += "\nExecution timed out after 30 seconds.\n"
                process.terminate()
                try:
                    process.wait(timeout=5)
                except:
                    process.kill()

            # Wait for output threads to complete
            stdout_thread.join()
            stderr_thread.join()

            # Update status
            if process.returncode == 0:
                self.output_cache[project_id]['status'] = 'completed'
                self.output_cache[project_id]['output'] += "\nExecution completed successfully.\n"
            else:
                self.output_cache[project_id]['status'] = 'error'
                self.output_cache[project_id]['output'] += f"\nExecution failed with exit code {process.returncode}.\n"

        except Exception as e:
            logger.error(f"Error executing project: {str(e)}")
            self.output_cache[project_id]['output'] += f"ERROR: {str(e)}\n"
            self.output_cache[project_id]['status'] = 'error'

        finally:
            # Clean up
            if project_id in self.running_processes:
                del self.running_processes[project_id]

    def _read_output(self, pipe, project_id, stream_type):
        """
        Read output from a process pipe

        Args:
            pipe: Process pipe to read from
            project_id (str): Project ID
            stream_type (str): Type of stream ('stdout' or 'stderr')
        """
        prefix = "ERROR: " if stream_type == 'stderr' else ""

        for line in pipe:
            if project_id in self.output_cache:
                self.output_cache[project_id]['output'] += f"{prefix}{line}"
                self.output_cache[project_id]['last_update'] = time.time()

    def _is_pygame_project(self, project_dir):
        """
        Check if the project uses Pygame

        Args:
            project_dir (str): Path to the project directory

        Returns:
            bool: True if the project uses Pygame, False otherwise
        """
        # Check all Python files for Pygame imports
        for root, _, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            if 'import pygame' in content or 'from pygame' in content:
                                return True
                    except:
                        pass

        return False

    def _is_flask_project(self, project_dir):
        """
        Check if the project uses Flask

        Args:
            project_dir (str): Path to the project directory

        Returns:
            bool: True if the project uses Flask, False otherwise
        """
        # Check all Python files for Flask imports
        for root, _, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            if 'from flask import' in content or 'import flask' in content or 'flask(' in content:
                                return True
                    except:
                        pass
        return False

    def _modify_flask_port(self, main_file):
        """
        Modify Flask application to use a different port

        Args:
            main_file (str): Path to the main Flask file
        """
        try:
            with open(main_file, 'r') as f:
                content = f.read()

            # Replace common Flask run patterns to use port 5002 with better conflict handling
            modifications = [
                ('app.run(debug=True)', 'app.run(debug=True, port=5002, host="127.0.0.1", use_reloader=False)'),
                ('app.run()', 'app.run(port=5002, host="127.0.0.1", use_reloader=False)'),
                ('app.run(debug=False)', 'app.run(debug=False, port=5002, host="127.0.0.1", use_reloader=False)'),
                ('app.run(host=', 'app.run(port=5002, host='),
                ('app.run(port=5000', 'app.run(port=5002'),
                ('app.run(port=5001', 'app.run(port=5002'),
                ('port=5000', 'port=5002'),
                ('port=5001', 'port=5002'),
                # Add use_reloader=False to prevent reloader issues
                ('app.run(debug=True, port=5002, host="127.0.0.1")', 'app.run(debug=True, port=5002, host="127.0.0.1", use_reloader=False)'),
            ]

            for old, new in modifications:
                content = content.replace(old, new)

            # If no app.run() found, add it with the correct port
            if 'app.run(' not in content and 'if __name__' in content:
                # Find the if __name__ == '__main__' block and add app.run
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '__name__' in line and '__main__' in line:
                        # Add app.run after this line with port finding logic
                        lines.insert(i + 1, '    import socket')
                        lines.insert(i + 2, '    def find_port(start=5002):')
                        lines.insert(i + 3, '        for p in range(start, start+100):')
                        lines.insert(i + 4, '            try:')
                        lines.insert(i + 5, '                with socket.socket() as s:')
                        lines.insert(i + 6, '                    s.bind(("127.0.0.1", p))')
                        lines.insert(i + 7, '                    return p')
                        lines.insert(i + 8, '            except: continue')
                        lines.insert(i + 9, '        return 5002')
                        lines.insert(i + 10, '    port = find_port()')
                        lines.insert(i + 11, '    print(f"Starting Flask app on port {port}")')
                        lines.insert(i + 12, '    app.run(debug=True, port=port, host="127.0.0.1", use_reloader=False)')
                        break
                content = '\n'.join(lines)

            with open(main_file, 'w') as f:
                f.write(content)

        except Exception as e:
            logger.error(f"Error modifying Flask port: {str(e)}")

    def get_execution_status(self, project_id):
        """
        Get the current execution status of a project

        Args:
            project_id (str): Project ID

        Returns:
            dict: Execution status
        """
        if project_id in self.output_cache:
            return {
                'success': True,
                'status': self.output_cache[project_id]
            }

        return {'success': False, 'error': 'Project not found'}

    def stop_execution(self, project_id):
        """
        Stop the execution of a project

        Args:
            project_id (str): Project ID

        Returns:
            dict: Result with success status
        """
        if project_id in self.running_processes:
            try:
                # Terminate the process
                self.running_processes[project_id].terminate()

                # Wait for the process to terminate
                try:
                    self.running_processes[project_id].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    self.running_processes[project_id].kill()

                # Update status
                if project_id in self.output_cache:
                    self.output_cache[project_id]['status'] = 'stopped'
                    self.output_cache[project_id]['output'] += "\nExecution stopped by user.\n"

                # Clean up
                del self.running_processes[project_id]

                return {'success': True}
            except Exception as e:
                logger.error(f"Error stopping execution: {str(e)}")
                return {'success': False, 'error': str(e)}

        return {'success': False, 'error': 'Project not running'}

    def clean_up(self):
        """
        Clean up resources
        """
        # Stop all running processes
        for project_id, process in list(self.running_processes.items()):
            try:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            except:
                pass

        # Clear dictionaries
        self.running_processes.clear()
        self.output_cache.clear()

        # Remove temporary directories
        for project_dir in self.project_dirs.values():
            try:
                shutil.rmtree(project_dir)
            except:
                pass

        self.project_dirs.clear()

# Create a singleton instance
simple_executor = SimpleCodeExecutor()
