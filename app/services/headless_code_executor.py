"""
Headless Code Executor Service

This module provides functionality to execute code in a headless environment,
capturing output and screenshots for GUI applications.
"""

import os
import sys
import uuid
import time
import base64
import io
import json
import logging
import threading
import subprocess
import tempfile
import shutil
from PIL import Image

from app.services.virtual_display import VirtualDisplayManager

logger = logging.getLogger(__name__)

class HeadlessCodeExecutor:
    """
    Executes code in a headless environment and captures output and screenshots
    """

    def __init__(self):
        """
        Initialize the headless code executor
        """
        self.running_processes = {}
        self.output_cache = {}
        self.display_manager = VirtualDisplayManager()
        self.screenshot_threads = {}
        self.project_dirs = {}

    def execute_project(self, files):
        """
        Execute a project with multiple files

        Args:
            files (list): List of file objects with name and content

        Returns:
            dict: Execution result with project_id and success status
        """
        # Create a unique project ID
        project_id = str(uuid.uuid4())

        # Create a temporary directory for the project
        project_dir = tempfile.mkdtemp()
        self.project_dirs[project_id] = project_dir

        # Write files to the project directory
        for file in files:
            file_path = os.path.join(project_dir, file['name'])
            with open(file_path, 'w') as f:
                f.write(file['content'])

        # Initialize output cache
        self.output_cache[project_id] = {
            'output': '',
            'images': [],
            'status': 'initializing',
            'last_update': time.time()
        }

        # Start virtual display if needed
        has_gui = self._project_has_gui(files)
        if has_gui:
            display_started = self.display_manager.start_display(800, 600)

            # Check if we're using the fallback display
            if display_started and self.display_manager.using_fallback:
                self.output_cache[project_id]['output'] += "INFO: Using pure Python fallback display. Screenshots will be available but may not reflect actual GUI output.\n"
                self.output_cache[project_id]['status'] = 'running'
            elif not display_started:
                self.output_cache[project_id]['output'] += "WARNING: Could not start any virtual display. GUI applications may not work correctly.\n"
                self.output_cache[project_id]['output'] += "GUI applications will run in the local environment instead of the virtual display.\n"
                self.output_cache[project_id]['status'] = 'warning'

                # Add a message about how to install Xvfb
                self.output_cache[project_id]['output'] += "\nTo enable virtual display for GUI applications, install Xvfb:\n"
                self.output_cache[project_id]['output'] += "  - On Ubuntu/Debian: sudo apt-get install xvfb\n"
                self.output_cache[project_id]['output'] += "  - On macOS: brew install xquartz\n"
                self.output_cache[project_id]['output'] += "  - See deployment_guide.md for more details\n"

        # Find the main file to execute
        main_file = self.find_main_file(project_dir)
        if not main_file:
            self.output_cache[project_id]['output'] += "ERROR: Could not find a main file to execute.\n"
            self.output_cache[project_id]['status'] = 'error'
            return {'success': False, 'project_id': project_id, 'error': 'No main file found'}

        # Start execution in a separate thread
        threading.Thread(target=self._execute_project_thread,
                         args=(project_id, project_dir, main_file, has_gui)).start()

        return {'success': True, 'project_id': project_id}

    def _project_has_gui(self, files):
        """
        Check if the project uses GUI libraries

        Args:
            files (list): List of file objects with name and content

        Returns:
            bool: True if the project uses GUI libraries, False otherwise
        """
        gui_libraries = ['pygame', 'tkinter', 'PyQt', 'PySide', 'kivy', 'turtle']

        for file in files:
            if file['name'].endswith('.py'):
                content = file['content'].lower()
                for lib in gui_libraries:
                    if f'import {lib.lower()}' in content or f'from {lib.lower()}' in content:
                        return True

        return False

    def _is_pygame_project(self, project_dir):
        """
        Check if the project uses Pygame

        Args:
            project_dir (str): Path to the project directory

        Returns:
            bool: True if the project uses Pygame, False otherwise
        """
        # Check all Python files for Pygame imports
        python_files = [f for f in os.listdir(project_dir) if f.endswith('.py')]

        for file in python_files:
            file_path = os.path.join(project_dir, file)
            try:
                with open(file_path, 'r') as f:
                    content = f.read().lower()
                    if 'import pygame' in content or 'from pygame' in content:
                        return True
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {str(e)}")

        return False

    def find_main_file(self, project_dir):
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
        python_files = [f for f in os.listdir(project_dir) if f.endswith('.py')]

        # First, look for specific main file names
        for name in main_file_names:
            if name in python_files:
                return os.path.join(project_dir, name)

        # Then, look for files with if __name__ == '__main__'
        for file in python_files:
            file_path = os.path.join(project_dir, file)
            with open(file_path, 'r') as f:
                content = f.read()
                if "__name__" in content and "__main__" in content:
                    return file_path

        # If no main file found, return the first Python file
        if python_files:
            return os.path.join(project_dir, python_files[0])

        return None

    def _execute_project_thread(self, project_id, project_dir, main_file, has_gui):
        """
        Execute a project in a separate thread

        Args:
            project_id (str): Project ID
            project_dir (str): Path to the project directory
            main_file (str): Path to the main file to execute
            has_gui (bool): Whether the project uses GUI libraries
        """
        try:
            # Update status
            self.output_cache[project_id]['status'] = 'running'

            # Prepare environment variables
            env = os.environ.copy()

            # If this is a GUI application but we couldn't start a virtual display,
            # add a note about it to the output
            if has_gui and not self.display_manager.is_display_running():
                self.output_cache[project_id]['output'] += "\nRunning GUI application in the local environment.\n"
                self.output_cache[project_id]['output'] += "Note: The application window may appear on your desktop.\n"

                # For Pygame applications, set SDL_VIDEODRIVER to 'dummy' if no display is available
                # This allows Pygame to run without a display, but graphics won't be visible
                if self._is_pygame_project(project_dir):
                    self.output_cache[project_id]['output'] += "Detected Pygame application. Setting SDL_VIDEODRIVER to 'dummy' for headless operation.\n"
                    env['SDL_VIDEODRIVER'] = 'dummy'

            # Start the process
            process = subprocess.Popen(
                [sys.executable, main_file],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env  # Use the modified environment
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

            # Start screenshot thread if GUI and any display is running
            if has_gui and self.display_manager.is_display_running():
                # If using fallback display, add a note
                if self.display_manager.using_fallback:
                    self.output_cache[project_id]['output'] += "\nUsing pure Python fallback display for screenshots.\n"
                    self.output_cache[project_id]['output'] += "Screenshots will show a simulated display rather than actual GUI output.\n"

                screenshot_thread = threading.Thread(
                    target=self._capture_screenshots_thread,
                    args=(project_id,)
                )
                screenshot_thread.daemon = True
                screenshot_thread.start()
                self.screenshot_threads[project_id] = screenshot_thread
            elif has_gui:
                # If we have a GUI but no virtual display, add a message
                self.output_cache[project_id]['output'] += "\nCannot capture screenshots without a virtual display.\n"
                self.output_cache[project_id]['output'] += "Install Xvfb to enable screenshot capture.\n"

            # Wait for the process to complete
            process.wait()

            # Wait for output threads to complete
            stdout_thread.join()
            stderr_thread.join()

            # Update status
            if process.returncode == 0:
                self.output_cache[project_id]['status'] = 'completed'
            else:
                self.output_cache[project_id]['status'] = 'error'

        except Exception as e:
            logger.error(f"Error executing project: {str(e)}")
            self.output_cache[project_id]['output'] += f"ERROR: {str(e)}\n"
            self.output_cache[project_id]['status'] = 'error'

        finally:
            # Clean up
            if project_id in self.running_processes:
                del self.running_processes[project_id]

            # Stop the virtual display if it was started
            if has_gui:
                self.display_manager.stop_display()

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

    def _capture_screenshots_thread(self, project_id):
        """
        Capture screenshots in a separate thread

        Args:
            project_id (str): Project ID
        """
        # Wait for the application to start
        time.sleep(2)

        # Capture screenshots every 0.5 seconds
        max_screenshots = 30
        screenshot_count = 0

        while (project_id in self.running_processes and
               self.running_processes[project_id].poll() is None and
               screenshot_count < max_screenshots):

            try:
                # Capture screenshot
                screenshot = self.display_manager.get_base64_screenshot()

                if screenshot and project_id in self.output_cache:
                    self.output_cache[project_id]['images'].append(screenshot)
                    self.output_cache[project_id]['last_update'] = time.time()
                    screenshot_count += 1
            except Exception as e:
                logger.error(f"Error capturing screenshot: {str(e)}")

            # Wait before capturing the next screenshot
            time.sleep(0.5)

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

        # Stop virtual display
        self.display_manager.stop_display()

        # Remove temporary directories
        for project_dir in self.project_dirs.values():
            try:
                shutil.rmtree(project_dir)
            except:
                pass

        self.project_dirs.clear()

# Create a singleton instance
headless_executor = HeadlessCodeExecutor()
