"""
API for the Live Browser.

This module provides API endpoints for interacting with the Live Browser.
"""

import os
import time
import json
import logging
import traceback
from flask import Blueprint, request, jsonify

from app.visual_browser.live_browser import live_browser

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Blueprint
live_browser_api = Blueprint('live_browser_api', __name__)

@live_browser_api.route('/start', methods=['POST'])
def start():
    """
    Start the Live Browser.
    """
    try:
        result = live_browser.start()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in start endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/stop', methods=['POST'])
def stop():
    """
    Stop the Live Browser.
    """
    try:
        result = live_browser.stop()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in stop endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/navigate', methods=['POST'])
def navigate():
    """
    Navigate to a URL.
    """
    try:
        data = request.json or {}
        url = data.get('url')

        if not url:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            })

        result = live_browser.navigate(url)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in navigate endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/click', methods=['POST'])
def click():
    """
    Click on an element or at specific coordinates.
    """
    try:
        data = request.json or {}
        selector = data.get('selector')
        x = data.get('x')
        y = data.get('y')
        text = data.get('text')

        result = live_browser.click(selector, x, y, text)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in click endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/type', methods=['POST'])
def type_text():
    """
    Type text into an input field.
    """
    try:
        data = request.json or {}
        text = data.get('text')
        selector = data.get('selector')

        if not text:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            })

        result = live_browser.type_text(text, selector)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in type endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/scroll', methods=['POST'])
def scroll():
    """
    Scroll the page.
    """
    try:
        data = request.json or {}
        direction = data.get('direction', 'down')
        distance = data.get('distance', 300)

        result = live_browser.scroll(direction, distance)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in scroll endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/press-key', methods=['POST'])
def press_key():
    """
    Press a key on the keyboard.
    """
    try:
        data = request.json or {}
        key = data.get('key')
        selector = data.get('selector')

        if not key:
            return jsonify({
                'success': False,
                'error': 'Key is required'
            })

        result = live_browser.press_key(key, selector)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in press-key endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/execute-task', methods=['POST'])
def execute_task():
    """
    Execute a task autonomously.

    Supports both simple tasks (search, fill_form) and complex natural language tasks.
    For natural language tasks, use task_type='natural_language' and task_data={'task': 'your task description'}.
    """
    try:
        data = request.json or {}

        # Check if this is a simple text input (for backward compatibility)
        if isinstance(data, dict) and 'text' in data and len(data) == 1:
            # Convert simple text input to natural language task
            task_type = 'natural_language'
            task_data = {'task': data['text']}
        else:
            # Normal structured input
            task_type = data.get('task_type')
            task_data = data.get('task_data', {})

            # If no task type but we have a 'task' field, assume natural language
            if not task_type and 'task' in data:
                task_type = 'natural_language'
                task_data = {'task': data['task']}

        # If still no task type, check if we have a query that could be a natural language task
        if not task_type and 'query' in data:
            query = data['query']
            # If query is a longer text (more than 3 words), treat as natural language
            if len(query.split()) > 3:
                task_type = 'natural_language'
                task_data = {'task': query}
            else:
                task_type = 'search'
                task_data = {'query': query}

        if not task_type:
            return jsonify({
                'success': False,
                'error': 'Task type is required'
            })

        # Log the task for debugging
        logger.info(f"Executing task: type={task_type}, data={task_data}")

        # Execute the task
        result = live_browser.execute_task(task_type, task_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in execute-task endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/task-chain/create', methods=['POST'])
def create_task_chain():
    """
    Create a new task chain.
    """
    try:
        result = live_browser.create_task_chain()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in create-task-chain endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/task-chain/add-task', methods=['POST'])
def add_task_to_chain():
    """
    Add a task to the task chain.
    """
    try:
        data = request.json or {}
        task_type = data.get('task_type')
        task_data = data.get('task_data', {})
        description = data.get('description')

        # Handle condition if provided
        condition = None
        if 'condition' in data:
            condition_data = data['condition']
            condition_type = condition_data.get('type')
            condition_value = condition_data.get('value')

            if condition_type and condition_value is not None:
                condition_result = live_browser.create_conditional_task(condition_type, condition_value)
                if condition_result.get('success', False):
                    condition = condition_result.get('condition')

        if not task_type:
            return jsonify({
                'success': False,
                'error': 'Task type is required'
            })

        result = live_browser.add_task_to_chain(task_type, task_data, condition, description)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in add-task-to-chain endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/task-chain/execute', methods=['POST'])
def execute_task_chain():
    """
    Execute the task chain.
    """
    try:
        result = live_browser.execute_task_chain()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in execute-task-chain endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/task-chain/progress', methods=['GET'])
def get_task_chain_progress():
    """
    Get the current progress of the task chain.
    """
    try:
        result = live_browser.get_task_chain_progress()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get-task-chain-progress endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/visual/find-text', methods=['POST'])
def find_text_on_screen():
    """
    Find text on the screen using OCR.
    """
    try:
        data = request.json or {}
        text = data.get('text')
        case_sensitive = data.get('case_sensitive', False)

        if not text:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            })

        result = live_browser.find_text_on_screen(text, case_sensitive)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in find-text-on-screen endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/visual/click-text', methods=['POST'])
def click_text_on_screen():
    """
    Click on text found on the screen.
    """
    try:
        data = request.json or {}
        text = data.get('text')
        case_sensitive = data.get('case_sensitive', False)

        if not text:
            return jsonify({
                'success': False,
                'error': 'Text is required'
            })

        result = live_browser.click_text_on_screen(text, case_sensitive)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in click-text-on-screen endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/visual/ocr', methods=['POST'])
def perform_ocr():
    """
    Perform OCR on the current screenshot.
    """
    try:
        data = request.json or {}
        region = data.get('region')

        result = live_browser.perform_ocr(region)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in perform-ocr endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/screenshot', methods=['GET', 'POST'])
def screenshot():
    """
    Get a screenshot of the Live Browser.

    Returns the screenshot as an image or JSON response.
    If download=true is specified, the image will be returned with Content-Disposition header.
    """
    from flask import send_file, Response
    import io

    # Check if JSON format is requested
    want_json = False
    if request.method == 'GET':
        want_json = request.args.get('json', '').lower() == 'true'
    elif request.method == 'POST':
        if request.is_json and request.json:
            want_json = request.json.get('json', False)
        else:
            # Handle form data
            want_json = request.form.get('json', '').lower() == 'true'

    try:
        # Check if browser is running
        if not live_browser.is_running:
            if want_json:
                return jsonify({
                    'success': False,
                    'error': 'Browser is not running'
                })
            else:
                # Return a JSON error instead of a placeholder image
                return jsonify({
                    'success': False,
                    'error': 'Browser is not running'
                })

        # Take a new screenshot if requested
        take_new = request.args.get('new', '').lower() == 'true'
        # Safely check JSON content
        if request.is_json:
            try:
                json_data = request.get_json(silent=True)
                if json_data and json_data.get('new', False):
                    take_new = True
            except:
                pass

        # Get screenshot data
        screenshot_data = None
        screenshot_path = None

        if take_new:
            try:
                # Take a new screenshot directly from the browser
                screenshot_data = live_browser.driver.get_screenshot_as_png()
            except Exception as ss_error:
                logger.warning(f"Error taking new screenshot directly: {str(ss_error)}")

                # No screenshot service available
                logger.warning("Screenshot service not available")

        # If we don't have screenshot data yet, use the browser's current screenshot
        if not screenshot_data and not screenshot_path:
            # Use browser's current screenshot
            if hasattr(live_browser, 'current_screenshot') and live_browser.current_screenshot:
                screenshot_path = live_browser.current_screenshot

        # If we have a screenshot path but no data, load the file
        if screenshot_path and not screenshot_data:
            try:
                # Convert relative path to absolute
                if screenshot_path.startswith('/static/'):
                    file_path = os.path.join('agen911/app', screenshot_path[1:])  # Remove leading slash
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            screenshot_data = f.read()
            except Exception as file_error:
                logger.warning(f"Error loading screenshot file: {str(file_error)}")

        # If we still don't have screenshot data, try taking a new screenshot
        if not screenshot_data:
            try:
                screenshot_data = live_browser.driver.get_screenshot_as_png()
            except Exception as direct_error:
                logger.warning(f"Error taking direct screenshot: {str(direct_error)}")

                # If all attempts failed, return an error
                if want_json:
                    return jsonify({
                        'success': False,
                        'error': 'No screenshot available'
                    })
                else:
                    # Return a JSON error instead of a placeholder image
                    return jsonify({
                        'success': False,
                        'error': 'No screenshot available'
                    })

        # Determine if this is a download request
        is_download = request.args.get('download', '').lower() == 'true'

        # If JSON response is requested, return JSON
        if want_json:
            # Convert screenshot data to base64
            import base64
            screenshot_base64 = base64.b64encode(screenshot_data).decode('utf-8')

            return jsonify({
                'success': True,
                'screenshot': f"data:image/png;base64,{screenshot_base64}",
                'timestamp': int(time.time())
            })

        # Otherwise, return the image directly
        timestamp = int(time.time())
        filename = f"screenshot_{timestamp}.png"

        # Create a response with the image data
        response = Response(screenshot_data, mimetype='image/png')

        # If download is requested, add Content-Disposition header
        if is_download:
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
    except Exception as e:
        logger.error(f"Error in screenshot endpoint: {str(e)}")
        logger.error(traceback.format_exc())

        if want_json:
            return jsonify({
                'success': False,
                'error': str(e)
            })
        else:
            # Return a JSON error instead of a placeholder image
            return jsonify({
                'success': False,
                'error': str(e)
            })

@live_browser_api.route('/back', methods=['POST'])
def go_back():
    """
    Go back in browser history.
    """
    try:
        if not live_browser.is_running:
            return jsonify({
                'success': False,
                'error': 'Browser is not running'
            })

        # Execute back command
        try:
            live_browser.driver.back()

            # Wait for page to load
            time.sleep(1)

            # Get current URL
            current_url = live_browser.driver.current_url

            return jsonify({
                'success': True,
                'url': current_url,
                'message': 'Successfully went back in history'
            })
        except Exception as e:
            logger.error(f"Error going back: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            })
    except Exception as e:
        logger.error(f"Error in back endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/forward', methods=['POST'])
def go_forward():
    """
    Go forward in browser history.
    """
    try:
        if not live_browser.is_running:
            return jsonify({
                'success': False,
                'error': 'Browser is not running'
            })

        # Execute forward command
        try:
            live_browser.driver.forward()

            # Wait for page to load
            time.sleep(1)

            # Get current URL
            current_url = live_browser.driver.current_url

            return jsonify({
                'success': True,
                'url': current_url,
                'message': 'Successfully went forward in history'
            })
        except Exception as e:
            logger.error(f"Error going forward: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            })
    except Exception as e:
        logger.error(f"Error in forward endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/screenshot-json', methods=['GET', 'POST'])
def screenshot_json():
    """
    Get a screenshot of the Live Browser as JSON with base64 data.
    """
    try:
        # Check if browser is running
        if not live_browser.is_running:
            return jsonify({
                'success': False,
                'error': 'Browser is not running'
            })

        # Take a new screenshot
        try:
            # Take a new screenshot directly from the browser
            screenshot_data = live_browser.driver.get_screenshot_as_png()
        except Exception as ss_error:
            logger.warning(f"Error taking new screenshot directly: {str(ss_error)}")
            return jsonify({
                'success': False,
                'error': f"Error taking screenshot: {str(ss_error)}"
            })

        # Convert screenshot data to base64
        import base64
        screenshot_base64 = base64.b64encode(screenshot_data).decode('utf-8')

        return jsonify({
            'success': True,
            'screenshot': f"data:image/png;base64,{screenshot_base64}",
            'timestamp': int(time.time())
        })
    except Exception as e:
        logger.error(f"Error in screenshot-json endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@live_browser_api.route('/status', methods=['GET'])
def status():
    """
    Get the status of the Live Browser.
    """
    try:
        # Check if browser is running
        if not live_browser.is_running:
            return jsonify({
                'success': False,
                'error': 'Browser is not running'
            })

        # Get current screenshot
        screenshot = None
        # Use browser's current screenshot
        if hasattr(live_browser, 'current_screenshot') and live_browser.current_screenshot:
            screenshot = live_browser.current_screenshot

        # Return status with more details
        return jsonify({
            'success': True,
            'is_running': live_browser.is_running,
            'current_url': live_browser.current_url,
            'screenshot': screenshot,
            'timestamp': int(time.time())
        })
    except Exception as e:
        logger.error(f"Error in status endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })
