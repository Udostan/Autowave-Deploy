"""
WebSocket Server for Visual Browser.

This module provides a WebSocket server for real-time communication with the browser.
"""

import logging
import json
import threading
import time
from typing import Dict, Any, List, Set

from flask import Flask
from flask_socketio import SocketIO, emit

from app.visual_browser.browser_manager import browser_manager

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app and SocketIO instance
socketio_app = Flask(__name__)
socketio = SocketIO(socketio_app, cors_allowed_origins="*")

# Connected clients
connected_clients: Dict[str, str] = {}  # Maps client_id to session_id

# Session screenshots
session_data: Dict[str, Dict[str, Any]] = {}

@socketio.on('connect')
def handle_connect():
    """
    Handle client connection.
    """
    from flask_socketio import request
    client_id = request.sid
    logger.info(f"Client connected: {client_id}")

    # Send welcome message
    emit('connected', {
        'message': 'Connected to Visual Browser WebSocket server',
        'client_id': client_id
    })

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle client disconnection.
    """
    from flask_socketio import request
    client_id = request.sid

    # Get session ID for this client
    session_id = connected_clients.get(client_id)

    if client_id in connected_clients:
        del connected_clients[client_id]
        logger.info(f"Client disconnected: {client_id}")

    # Check if this was the last client for this session
    if session_id:
        is_last_client = session_id not in [s for s in connected_clients.values()]

        if is_last_client:
            # Close the browser for this session
            logger.info(f"Closing browser for session {session_id} as last client disconnected")
            browser_manager.close_browser(session_id)

            # Clean up session data
            if session_id in session_data:
                del session_data[session_id]

@socketio.on('register_session')
def handle_register_session(data):
    """
    Handle session registration.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = data.get('session_id', f"session_{int(time.time())}")

    # Register client with session
    connected_clients[client_id] = session_id
    logger.info(f"Client {client_id} registered with session {session_id}")

    # Initialize session data if needed
    if session_id not in session_data:
        session_data[session_id] = {
            'screenshot': None,
            'url': None,
            'title': None
        }

    # Send current session data to client
    if session_data[session_id]['screenshot']:
        emit('screenshot', {
            'screenshot': session_data[session_id]['screenshot'],
            'url': session_data[session_id]['url'],
            'title': session_data[session_id]['title']
        })

    # Return success
    emit('session_registered', {
        'session_id': session_id,
        'message': f"Registered with session {session_id}"
    })

@socketio.on('navigate')
def handle_navigate(data):
    """
    Handle navigate command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    url = data.get('url')

    if not url:
        emit('error', {'message': 'URL is required'})
        return

    logger.info(f"Navigating to {url} for session {session_id}")

    # Navigate to URL
    result = browser_manager.navigate(session_id, url)

    if result['success']:
        # Update session data
        session_data[session_id] = {
            'screenshot': result['screenshot'],
            'url': result['url'],
            'title': result.get('title', '')
        }

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': result['url'],
                    'title': result.get('title', '')
                }, room=cid)
    else:
        emit('error', {'message': result.get('error', 'Error navigating to URL')})

@socketio.on('click')
def handle_click(data):
    """
    Handle click command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    selector = data.get('selector')
    x = data.get('x')
    y = data.get('y')

    if not selector and (x is None or y is None):
        emit('error', {'message': 'Either selector or coordinates (x, y) must be provided'})
        return

    logger.info(f"Clicking on element with selector: {selector} or at coordinates: ({x}, {y}) for session {session_id}")

    # Click
    result = browser_manager.click(session_id, selector, x, y)

    if result['success']:
        # Update session data
        session_data[session_id]['screenshot'] = result['screenshot']
        if 'url' in result:
            session_data[session_id]['url'] = result['url']
        if 'title' in result:
            session_data[session_id]['title'] = result['title']

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': result.get('url', session_data[session_id]['url']),
                    'title': result.get('title', session_data[session_id].get('title', ''))
                }, room=cid)
    else:
        emit('error', {'message': result.get('error', 'Error clicking')})

@socketio.on('type')
def handle_type(data):
    """
    Handle type command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    text = data.get('text')
    selector = data.get('selector')

    if not text:
        emit('error', {'message': 'Text is required'})
        return

    logger.info(f"Typing '{text}' into element with selector: {selector} for session {session_id}")

    # Type
    result = browser_manager.type(session_id, text, selector)

    if result['success']:
        # Update session data
        session_data[session_id]['screenshot'] = result['screenshot']

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': session_data[session_id]['url'],
                    'title': session_data[session_id].get('title', '')
                }, room=cid)
    else:
        emit('error', {'message': result.get('error', 'Error typing')})

@socketio.on('scroll')
def handle_scroll(data):
    """
    Handle scroll command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    direction = data.get('direction', 'down')
    distance = data.get('distance', 300)

    logger.info(f"Scrolling {direction} by {distance} pixels for session {session_id}")

    # Scroll
    result = browser_manager.scroll(session_id, direction, distance)

    if result['success']:
        # Update session data
        session_data[session_id]['screenshot'] = result['screenshot']

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': session_data[session_id]['url'],
                    'title': session_data[session_id].get('title', '')
                }, room=cid)
    else:
        emit('error', {'message': result.get('error', 'Error scrolling')})

@socketio.on('back')
def handle_back():
    """
    Handle back command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    logger.info(f"Going back in history for session {session_id}")

    # Go back
    result = browser_manager.go_back(session_id)

    if result['success']:
        # Update session data
        session_data[session_id]['screenshot'] = result['screenshot']
        session_data[session_id]['url'] = result['url']
        session_data[session_id]['title'] = result.get('title', '')

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': result['url'],
                    'title': result.get('title', '')
                }, room=cid)
    else:
        emit('error', {'message': result.get('error', 'Error going back')})

@socketio.on('forward')
def handle_forward():
    """
    Handle forward command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    logger.info(f"Going forward in history for session {session_id}")

    # Go forward
    result = browser_manager.go_forward(session_id)

    if result['success']:
        # Update session data
        session_data[session_id]['screenshot'] = result['screenshot']
        session_data[session_id]['url'] = result['url']
        session_data[session_id]['title'] = result.get('title', '')

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': result['url'],
                    'title': result.get('title', '')
                }, room=cid)
    else:
        emit('error', {'message': result.get('error', 'Error going forward')})

@socketio.on('info')
def handle_info():
    """
    Handle info command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    logger.info(f"Getting page information for session {session_id}")

    # Get page information
    result = browser_manager.get_page_info(session_id)

    if result['success']:
        emit('info', {
            'title': result['title'],
            'url': result['url'],
            'links': result['links'],
            'images': result.get('images', []),
            'inputs': result['inputs'],
            'buttons': result['buttons']
        })
    else:
        emit('error', {'message': result.get('error', 'Error getting page information')})

@socketio.on('fill_form')
def handle_fill_form(data):
    """
    Handle fill_form command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    form_data = data.get('form_data', {})

    if not form_data:
        emit('error', {'message': 'Form data is required'})
        return

    logger.info(f"Filling form with {len(form_data)} fields for session {session_id}")

    # Fill form
    result = browser_manager.fill_form(session_id, form_data)

    if result['success']:
        # Update session data
        session_data[session_id]['screenshot'] = result['screenshot']

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': session_data[session_id]['url'],
                    'title': session_data[session_id].get('title', '')
                }, room=cid)

        # Send form result
        emit('form_result', {
            'successful_fields': result.get('successful_fields', []),
            'failed_fields': result.get('failed_fields', [])
        })
    else:
        emit('error', {'message': result.get('error', 'Error filling form')})

@socketio.on('hover')
def handle_hover(data):
    """
    Handle hover command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    selector = data.get('selector')
    x = data.get('x')
    y = data.get('y')

    if not selector and (x is None or y is None):
        emit('error', {'message': 'Either selector or coordinates (x, y) must be provided'})
        return

    logger.info(f"Hovering over element with selector: {selector} or at coordinates: ({x}, {y}) for session {session_id}")

    # Hover
    result = browser_manager.hover(session_id, selector, x, y)

    if result['success']:
        # Update session data
        session_data[session_id]['screenshot'] = result['screenshot']

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': session_data[session_id]['url'],
                    'title': session_data[session_id].get('title', '')
                }, room=cid)
    else:
        emit('error', {'message': result.get('error', 'Error hovering')})

@socketio.on('drag_and_drop')
def handle_drag_and_drop(data):
    """
    Handle drag_and_drop command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    source_selector = data.get('source_selector')
    target_selector = data.get('target_selector')

    if not source_selector or not target_selector:
        emit('error', {'message': 'Source and target selectors are required'})
        return

    logger.info(f"Dragging element with selector '{source_selector}' to element with selector '{target_selector}' for session {session_id}")

    # Drag and drop
    result = browser_manager.drag_and_drop(session_id, source_selector, target_selector)

    if result['success']:
        # Update session data
        session_data[session_id]['screenshot'] = result['screenshot']

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': session_data[session_id]['url'],
                    'title': session_data[session_id].get('title', '')
                }, room=cid)
    else:
        emit('error', {'message': result.get('error', 'Error dragging and dropping')})

@socketio.on('press_key')
def handle_press_key(data):
    """
    Handle press_key command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    key = data.get('key')
    selector = data.get('selector')

    if not key:
        emit('error', {'message': 'Key is required'})
        return

    logger.info(f"Pressing key '{key}' on element with selector: {selector} for session {session_id}")

    # Press key
    result = browser_manager.press_key(session_id, key, selector)

    if result['success']:
        # Update session data
        session_data[session_id]['screenshot'] = result['screenshot']
        if 'url' in result:
            session_data[session_id]['url'] = result['url']
        if 'title' in result:
            session_data[session_id]['title'] = result['title']

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': result.get('url', session_data[session_id]['url']),
                    'title': result.get('title', session_data[session_id].get('title', ''))
                }, room=cid)
    else:
        emit('error', {'message': result.get('error', 'Error pressing key')})

@socketio.on('refresh')
def handle_refresh():
    """
    Handle refresh command.
    """
    from flask_socketio import request
    client_id = request.sid
    session_id = connected_clients.get(client_id)

    if not session_id:
        emit('error', {'message': 'Not registered with a session'})
        return

    logger.info(f"Refreshing page for session {session_id}")

    # Refresh
    result = browser_manager.refresh(session_id)

    if result['success']:
        # Update session data
        session_data[session_id]['screenshot'] = result['screenshot']
        session_data[session_id]['url'] = result['url']
        session_data[session_id]['title'] = result.get('title', '')

        # Broadcast to all clients in this session
        for cid, sid in connected_clients.items():
            if sid == session_id:
                socketio.emit('screenshot', {
                    'screenshot': result['screenshot'],
                    'url': result['url'],
                    'title': result.get('title', '')
                }, room=cid)
    else:
        emit('error', {'message': result.get('error', 'Error refreshing')})

def start_websocket_server(host='0.0.0.0', port=5026):
    """
    Start the WebSocket server.

    Args:
        host (str, optional): The host to bind to. Defaults to '0.0.0.0'.
        port (int, optional): The port to bind to. Defaults to 5002.
    """
    try:
        logger.info(f"Starting WebSocket server on {host}:{port}")
        print(f"Starting WebSocket server on {host}:{port}")
        socketio.run(socketio_app, host=host, port=port, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Error starting WebSocket server: {str(e)}")
        print(f"Error starting WebSocket server: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(error_trace)
        print(error_trace)

def start_websocket_server_thread():
    """
    Start the WebSocket server in a separate thread.
    """
    try:
        logger.info("Starting WebSocket server thread...")
        print("Starting WebSocket server thread...")
        thread = threading.Thread(target=start_websocket_server)
        thread.daemon = True
        thread.start()
        logger.info("WebSocket server thread started")
        print("WebSocket server thread started")
        return thread
    except Exception as e:
        logger.error(f"Error starting WebSocket server thread: {str(e)}")
        print(f"Error starting WebSocket server thread: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(error_trace)
        print(error_trace)
        return None

def send_message(data):
    """
    Send a message to all connected clients.

    Args:
        data (dict): The message data to send.
    """
    try:
        # Get message type
        message_type = data.get('type', 'message')

        # Log message
        logger.debug(f"Broadcasting message of type '{message_type}'")

        # Broadcast to all clients
        socketio.emit(message_type, data, broadcast=True)

        return True
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Add event handlers for browser events
@socketio.on('browser_event')
def handle_browser_event(data):
    """
    Handle browser events from the client.
    """
    from flask_socketio import request
    client_id = request.sid

    # Log event
    logger.debug(f"Received browser event from client {client_id}: {data.get('type', 'unknown')}")

    # Broadcast to all clients
    socketio.emit('browser_event', data, broadcast=True, include_self=False)
