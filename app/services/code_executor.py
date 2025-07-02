"""
Code Execution Service - Executes generated code and provides visualization
"""

import os
import sys
import tempfile
import subprocess
import threading
import time
import json
import base64
import io
from PIL import Image
import uuid
import logging
import traceback

logger = logging.getLogger(__name__)

class CodeExecutor:
    """
    Service to execute generated code and provide visualization
    """

    def __init__(self, temp_dir=None):
        """
        Initialize the code executor

        Args:
            temp_dir (str, optional): Directory to store temporary files. Defaults to None.
        """
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self.running_processes = {}
        self.output_cache = {}

    def create_project_files(self, files):
        """
        Create project files in a temporary directory

        Args:
            files (list): List of file objects with name and content

        Returns:
            str: Path to the project directory
        """
        # Create a unique project ID
        project_id = str(uuid.uuid4())
        project_dir = os.path.join(self.temp_dir, project_id)

        # Create project directory
        os.makedirs(project_dir, exist_ok=True)

        # Create files
        for file in files:
            file_path = os.path.join(project_dir, file['name'])

            # Create subdirectories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write file content
            with open(file_path, 'w') as f:
                f.write(file['content'])

        return project_dir, project_id

    def find_main_file(self, project_dir):
        """
        Find the main file to execute

        Args:
            project_dir (str): Path to the project directory

        Returns:
            str: Path to the main file
        """
        # Look for common main file names
        common_main_files = [
            'main.py',
            'app.py',
            'snake_game.py',
            'game.py',
            'index.py',
            'run.py'
        ]

        for file_name in common_main_files:
            file_path = os.path.join(project_dir, file_name)
            if os.path.exists(file_path):
                return file_path

        # If no common main file found, look for any Python file
        for file_name in os.listdir(project_dir):
            if file_name.endswith('.py'):
                return os.path.join(project_dir, file_name)

        return None

    def execute_python_code(self, project_dir, project_id):
        """
        Execute Python code and capture output

        Args:
            project_dir (str): Path to the project directory
            project_id (str): Unique project ID

        Returns:
            dict: Execution result with status and output
        """
        main_file = self.find_main_file(project_dir)

        if not main_file:
            return {
                'status': 'error',
                'output': 'No Python file found to execute'
            }

        # Initialize output cache for this project
        self.output_cache[project_id] = {
            'status': 'running',
            'output': '',
            'images': [],
            'last_update': time.time()
        }

        # Create a virtual display for GUI applications
        env = os.environ.copy()

        # Start the process
        try:
            # For Pygame applications, we need to capture the display
            process = subprocess.Popen(
                [sys.executable, main_file],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            self.running_processes[project_id] = process

            # Start threads to read stdout and stderr
            threading.Thread(target=self._read_output, args=(process.stdout, project_id, 'stdout')).start()
            threading.Thread(target=self._read_output, args=(process.stderr, project_id, 'stderr')).start()

            # Start a thread to capture screenshots for GUI applications
            threading.Thread(target=self._capture_screenshots, args=(project_dir, project_id)).start()

            return {
                'status': 'started',
                'project_id': project_id
            }

        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            return {
                'status': 'error',
                'output': f"Error executing code: {str(e)}"
            }

    def _read_output(self, pipe, project_id, stream_type):
        """
        Read output from a pipe and update the output cache

        Args:
            pipe: Pipe to read from
            project_id (str): Project ID
            stream_type (str): Type of stream (stdout or stderr)
        """
        for line in pipe:
            if project_id in self.output_cache:
                if stream_type == 'stderr':
                    line = f"ERROR: {line}"

                self.output_cache[project_id]['output'] += line
                self.output_cache[project_id]['last_update'] = time.time()

    def _capture_screenshots(self, project_dir, project_id):
        """
        Capture screenshots of GUI applications

        Args:
            project_dir (str): Path to the project directory
            project_id (str): Project ID
        """
        # Wait for the application to start
        time.sleep(2)

        # For Pygame applications, we need to modify the code to capture screenshots
        # Find all Python files in the project directory
        python_files = [f for f in os.listdir(project_dir) if f.endswith('.py')]
        main_file = self.find_main_file(project_dir)

        if main_file:
            main_file_name = os.path.basename(main_file)

            # Read the content of the main file
            with open(main_file, 'r') as f:
                content = f.read()

            # Check if this is a Pygame application
            if 'pygame' in content:
                # Create a modified version of the file that captures screenshots
                modified_content = self._modify_pygame_code(content)

                # Write the modified content to a new file
                modified_file = os.path.join(project_dir, f"modified_{main_file_name}")
                with open(modified_file, 'w') as f:
                    f.write(modified_content)

                # Execute the modified file in a separate process
                try:
                    process = subprocess.Popen(
                        [sys.executable, modified_file],
                        cwd=project_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )

                    # Read output from the process
                    threading.Thread(target=self._read_output, args=(process.stdout, project_id, 'stdout')).start()
                    threading.Thread(target=self._read_output, args=(process.stderr, project_id, 'stderr')).start()

                    # Wait for the process to complete
                    process.wait()
                except Exception as e:
                    logger.error(f"Error executing modified Pygame code: {str(e)}")

                # Check if screenshots were generated
                screenshot_dir = os.path.join(project_dir, 'screenshots')
                if os.path.exists(screenshot_dir):
                    # Get all screenshots
                    screenshots = sorted([f for f in os.listdir(screenshot_dir) if f.endswith('.png')])

                    # Add screenshots to the output cache
                    for screenshot in screenshots:
                        try:
                            # Read the screenshot
                            with open(os.path.join(screenshot_dir, screenshot), 'rb') as f:
                                img_data = f.read()

                            # Convert the screenshot to base64
                            img_str = base64.b64encode(img_data).decode()

                            # Add the screenshot to the output cache
                            if project_id in self.output_cache:
                                self.output_cache[project_id]['images'].append(img_str)
                                self.output_cache[project_id]['last_update'] = time.time()
                        except Exception as e:
                            logger.error(f"Error processing screenshot: {str(e)}")
                return

        # Fallback: Try to capture screenshots using Pygame directly
        try:
            import pygame
            pygame.init()

            # Check if the process is still running
            while project_id in self.running_processes and self.running_processes[project_id].poll() is None:
                try:
                    # Try to get a screenshot
                    screenshot = self._capture_pygame_screenshot()

                    if screenshot:
                        # Convert the screenshot to base64
                        buffered = io.BytesIO()
                        screenshot.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()

                        # Add the screenshot to the output cache
                        if project_id in self.output_cache:
                            self.output_cache[project_id]['images'].append(img_str)
                            self.output_cache[project_id]['last_update'] = time.time()
                except Exception as e:
                    logger.error(f"Error capturing screenshot: {str(e)}")

                # Wait before capturing the next screenshot
                time.sleep(1)
        except ImportError:
            logger.warning("Pygame not available, cannot capture screenshots")

    def _modify_pygame_code(self, content):
        """
        Modify Pygame code to capture screenshots

        Args:
            content (str): Original Python code content

        Returns:
            str: Modified Python code content
        """
        # Add imports for screenshot capture
        imports = """
import os
import pygame
import time
import sys
"""

        # Add screenshot capture code
        screenshot_code = """
# Create screenshots directory
os.makedirs('screenshots', exist_ok=True)

# Original pygame.display.flip function
original_flip = pygame.display.flip

# Screenshot counter
screenshot_counter = 0
max_screenshots = 30
last_screenshot_time = time.time()

# Override pygame.display.flip to capture screenshots
def custom_flip():
    global screenshot_counter, last_screenshot_time
    # Call the original flip function
    original_flip()

    # Capture screenshot every 0.5 seconds, up to max_screenshots
    current_time = time.time()
    if current_time - last_screenshot_time >= 0.5 and screenshot_counter < max_screenshots:
        # Get the current display surface
        surface = pygame.display.get_surface()
        if surface:
            # Save the screenshot
            pygame.image.save(surface, f'screenshots/screenshot_{screenshot_counter:03d}.png')
            screenshot_counter += 1
            last_screenshot_time = current_time

# Replace the original flip function with our custom one
pygame.display.flip = custom_flip
"""

        # Check if the code already has imports
        if 'import pygame' in content:
            # Add screenshot code after the imports
            import_end = content.find('import pygame') + len('import pygame')
            # Find the next line after imports
            next_line = content.find('\n', import_end) + 1

            # Insert screenshot code after imports
            modified_content = content[:next_line] + screenshot_code + content[next_line:]
        else:
            # Add imports and screenshot code at the beginning
            modified_content = imports + screenshot_code + content

        return modified_content

    def _capture_pygame_screenshot(self):
        """
        Capture a screenshot of a Pygame application

        Returns:
            PIL.Image: Screenshot image
        """
        try:
            import pygame

            # Get the current display surface
            surface = pygame.display.get_surface()

            if surface:
                # Convert the surface to a PIL image
                raw_str = pygame.image.tostring(surface, "RGB", False)
                size = surface.get_size()

                # Create a PIL image from the raw string
                image = Image.frombytes("RGB", size, raw_str)
                return image
        except Exception as e:
            logger.error(f"Error capturing Pygame screenshot: {str(e)}")

        return None

    def get_execution_status(self, project_id):
        """
        Get the current execution status

        Args:
            project_id (str): Project ID

        Returns:
            dict: Execution status
        """
        if project_id not in self.output_cache:
            return {
                'status': 'not_found',
                'output': 'Project not found'
            }

        # Check if the process is still running
        if project_id in self.running_processes:
            process = self.running_processes[project_id]
            if process.poll() is not None:
                # Process has finished
                self.output_cache[project_id]['status'] = 'completed'

                # Get the return code
                return_code = process.poll()
                if return_code != 0:
                    self.output_cache[project_id]['status'] = 'error'

                # Remove the process from running processes
                del self.running_processes[project_id]

        # Return the current status
        return {
            'status': self.output_cache[project_id]['status'],
            'output': self.output_cache[project_id]['output'],
            'images': self.output_cache[project_id]['images'][-5:] if self.output_cache[project_id]['images'] else []
        }

    def stop_execution(self, project_id):
        """
        Stop code execution

        Args:
            project_id (str): Project ID

        Returns:
            dict: Result of the stop operation
        """
        if project_id in self.running_processes:
            process = self.running_processes[project_id]

            # Terminate the process
            process.terminate()

            # Wait for the process to terminate
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()

            # Remove the process from running processes
            del self.running_processes[project_id]

            # Update the output cache
            if project_id in self.output_cache:
                self.output_cache[project_id]['status'] = 'stopped'

            return {
                'status': 'stopped',
                'message': 'Execution stopped'
            }

        return {
            'status': 'not_found',
            'message': 'Project not found or already stopped'
        }

    def cleanup_old_projects(self, max_age=3600):
        """
        Clean up old projects

        Args:
            max_age (int, optional): Maximum age in seconds. Defaults to 3600 (1 hour).
        """
        current_time = time.time()

        # Clean up output cache
        projects_to_remove = []
        for project_id, cache in self.output_cache.items():
            if current_time - cache['last_update'] > max_age:
                projects_to_remove.append(project_id)

        for project_id in projects_to_remove:
            # Stop execution if still running
            if project_id in self.running_processes:
                self.stop_execution(project_id)

            # Remove from output cache
            if project_id in self.output_cache:
                del self.output_cache[project_id]

            # Remove project directory
            project_dir = os.path.join(self.temp_dir, project_id)
            if os.path.exists(project_dir):
                try:
                    import shutil
                    shutil.rmtree(project_dir)
                except Exception as e:
                    logger.error(f"Error removing project directory: {str(e)}")

# Create a singleton instance
code_executor = CodeExecutor()
