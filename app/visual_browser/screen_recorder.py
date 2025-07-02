"""
Screen Recorder Module

This module provides functionality to record the browser screen and stream it to clients.
"""

import os
import time
import json
import base64
import logging
import threading
import asyncio
from io import BytesIO
from typing import Dict, Any, Optional, Set, List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
websocket_clients = set()
recording_service = None

class ScreenRecorder:
    """
    A class for recording the browser screen and streaming it to clients.
    """
    
    def __init__(self, live_browser):
        """
        Initialize the Screen Recorder.
        
        Args:
            live_browser: The Live Browser instance.
        """
        self.live_browser = live_browser
        self.is_running = False
        self.is_recording = False
        self.capture_thread = None
        self.recording_thread = None
        self.screenshot_interval = 300  # milliseconds (3-4 FPS)
        self.last_screenshot = None
        self.last_screenshot_time = 0
        
        # Create recordings directory if it doesn't exist
        self.recordings_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          'static', 'recordings')
        if not os.path.exists(self.recordings_dir):
            os.makedirs(self.recordings_dir)
            logger.info(f"Created recordings directory: {self.recordings_dir}")
        
        # Current recording info
        self.current_recording = {
            'id': None,
            'path': None,
            'start_time': None,
            'frames': 0,
            'metadata': {}
        }
        
        # List of available recordings
        self.recordings = self._load_recordings()
        
        logger.info("Screen Recorder initialized")
    
    def start_capture(self):
        """
        Start capturing screenshots.
        
        Returns:
            bool: True if capture started successfully, False otherwise.
        """
        if self.is_running:
            logger.warning("Screen capture is already running")
            return False
        
        logger.info("Starting screen capture...")
        
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        logger.info("Screen capture started")
        return True
    
    def stop_capture(self):
        """
        Stop capturing screenshots.
        
        Returns:
            bool: True if capture stopped successfully, False otherwise.
        """
        if not self.is_running:
            logger.warning("Screen capture is not running")
            return False
        
        logger.info("Stopping screen capture...")
        
        self.is_running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=5)
            self.capture_thread = None
        
        logger.info("Screen capture stopped")
        return True
    
    def start_recording(self):
        """
        Start recording screenshots.
        
        Returns:
            dict: Information about the recording.
        """
        if self.is_recording:
            logger.warning("Recording is already in progress")
            return {
                'success': False,
                'error': 'Recording is already in progress'
            }
        
        logger.info("Starting recording...")
        
        # Generate recording ID and path
        recording_id = int(time.time())
        recording_path = os.path.join(self.recordings_dir, f"recording_{recording_id}")
        
        # Create recording directory
        if not os.path.exists(recording_path):
            os.makedirs(recording_path)
        
        # Set current recording info
        self.current_recording = {
            'id': recording_id,
            'path': recording_path,
            'start_time': time.time(),
            'frames': 0,
            'metadata': {
                'start_url': self.live_browser.current_url,
                'start_time': datetime.now().isoformat(),
                'browser': 'Chrome',
                'status': 'recording'
            }
        }
        
        # Save metadata
        self._save_recording_metadata()
        
        # Start recording
        self.is_recording = True
        
        logger.info(f"Recording started with ID: {recording_id}")
        
        return {
            'success': True,
            'recording_id': recording_id,
            'message': 'Recording started'
        }
    
    def stop_recording(self):
        """
        Stop recording screenshots.
        
        Returns:
            dict: Information about the recording.
        """
        if not self.is_recording:
            logger.warning("No recording in progress")
            return {
                'success': False,
                'error': 'No recording in progress'
            }
        
        logger.info("Stopping recording...")
        
        # Update metadata
        self.current_recording['metadata']['end_time'] = datetime.now().isoformat()
        self.current_recording['metadata']['duration'] = time.time() - self.current_recording['start_time']
        self.current_recording['metadata']['frames'] = self.current_recording['frames']
        self.current_recording['metadata']['end_url'] = self.live_browser.current_url
        self.current_recording['metadata']['status'] = 'completed'
        
        # Save metadata
        self._save_recording_metadata()
        
        # Stop recording
        recording_id = self.current_recording['id']
        self.is_recording = False
        
        # Reload recordings list
        self.recordings = self._load_recordings()
        
        logger.info(f"Recording stopped with ID: {recording_id}")
        
        return {
            'success': True,
            'recording_id': recording_id,
            'message': 'Recording stopped',
            'metadata': self.current_recording['metadata']
        }
    
    def delete_recording(self, recording_id):
        """
        Delete a recording.
        
        Args:
            recording_id: The ID of the recording to delete.
            
        Returns:
            dict: Result of the operation.
        """
        recording_path = os.path.join(self.recordings_dir, f"recording_{recording_id}")
        
        if not os.path.exists(recording_path):
            logger.warning(f"Recording {recording_id} not found")
            return {
                'success': False,
                'error': f'Recording {recording_id} not found'
            }
        
        logger.info(f"Deleting recording {recording_id}...")
        
        try:
            # Delete all files in the recording directory
            for filename in os.listdir(recording_path):
                file_path = os.path.join(recording_path, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            
            # Delete the directory
            os.rmdir(recording_path)
            
            # Reload recordings list
            self.recordings = self._load_recordings()
            
            logger.info(f"Recording {recording_id} deleted")
            
            return {
                'success': True,
                'message': f'Recording {recording_id} deleted'
            }
        except Exception as e:
            logger.error(f"Error deleting recording {recording_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Error deleting recording: {str(e)}'
            }
    
    def get_recordings(self):
        """
        Get a list of available recordings.
        
        Returns:
            list: A list of recording information.
        """
        # Reload recordings list
        self.recordings = self._load_recordings()
        return self.recordings
    
    def get_recording_frames(self, recording_id, start_frame=0, end_frame=None):
        """
        Get frames from a recording.
        
        Args:
            recording_id: The ID of the recording.
            start_frame: The first frame to get.
            end_frame: The last frame to get.
            
        Returns:
            dict: The frames and metadata.
        """
        recording_path = os.path.join(self.recordings_dir, f"recording_{recording_id}")
        
        if not os.path.exists(recording_path):
            logger.warning(f"Recording {recording_id} not found")
            return {
                'success': False,
                'error': f'Recording {recording_id} not found'
            }
        
        try:
            # Load metadata
            metadata_path = os.path.join(recording_path, 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            # Get frame files
            frame_files = [f for f in os.listdir(recording_path) if f.startswith('frame_') and f.endswith('.png')]
            frame_files.sort(key=lambda f: int(f.split('_')[1].split('.')[0]))
            
            # Apply start and end frame limits
            if end_frame is None:
                end_frame = len(frame_files)
            
            frame_files = frame_files[start_frame:end_frame]
            
            # Load frames
            frames = []
            for frame_file in frame_files:
                frame_path = os.path.join(recording_path, frame_file)
                with open(frame_path, 'rb') as f:
                    frame_data = f.read()
                    frames.append({
                        'data': base64.b64encode(frame_data).decode('utf-8'),
                        'timestamp': int(frame_file.split('_')[1].split('.')[0])
                    })
            
            return {
                'success': True,
                'recording_id': recording_id,
                'metadata': metadata,
                'frames': frames,
                'total_frames': len(frame_files),
                'start_frame': start_frame,
                'end_frame': start_frame + len(frames)
            }
        except Exception as e:
            logger.error(f"Error getting recording frames: {str(e)}")
            return {
                'success': False,
                'error': f'Error getting recording frames: {str(e)}'
            }
    
    def _capture_loop(self):
        """
        Main loop for capturing screenshots.
        """
        while self.is_running:
            try:
                # Check if browser is running
                if not self.live_browser.is_running or not self.live_browser.driver:
                    time.sleep(0.5)
                    continue
                
                # Take screenshot
                screenshot = self._take_screenshot()
                
                if screenshot:
                    # Save screenshot if recording
                    if self.is_recording:
                        self._save_screenshot(screenshot)
                    
                    # Broadcast screenshot to clients
                    self._broadcast_screenshot(screenshot)
                
                # Sleep for the specified interval
                time.sleep(self.screenshot_interval / 1000)
            except Exception as e:
                logger.error(f"Error in capture loop: {str(e)}")
                time.sleep(0.5)
    
    def _take_screenshot(self):
        """
        Take a screenshot of the browser.
        
        Returns:
            bytes: The screenshot as PNG data.
        """
        try:
            # Get screenshot from browser
            screenshot = self.live_browser.driver.get_screenshot_as_png()
            
            # Update last screenshot info
            self.last_screenshot = screenshot
            self.last_screenshot_time = time.time()
            
            return screenshot
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return None
    
    def _save_screenshot(self, screenshot):
        """
        Save a screenshot to the current recording.
        
        Args:
            screenshot: The screenshot data.
        """
        try:
            if not self.is_recording or not self.current_recording['path']:
                return
            
            # Generate frame filename
            frame_number = self.current_recording['frames']
            frame_path = os.path.join(self.current_recording['path'], f"frame_{frame_number}.png")
            
            # Save frame
            with open(frame_path, 'wb') as f:
                f.write(screenshot)
            
            # Update frame count
            self.current_recording['frames'] += 1
            
            # Update metadata periodically
            if self.current_recording['frames'] % 10 == 0:
                self._save_recording_metadata()
        except Exception as e:
            logger.error(f"Error saving screenshot: {str(e)}")
    
    def _save_recording_metadata(self):
        """
        Save metadata for the current recording.
        """
        try:
            if not self.current_recording['path']:
                return
            
            # Update metadata
            self.current_recording['metadata']['frames'] = self.current_recording['frames']
            self.current_recording['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Save metadata
            metadata_path = os.path.join(self.current_recording['path'], 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(self.current_recording['metadata'], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving recording metadata: {str(e)}")
    
    def _broadcast_screenshot(self, screenshot):
        """
        Broadcast a screenshot to all connected clients.
        
        Args:
            screenshot: The screenshot data.
        """
        try:
            if not websocket_clients:
                return
            
            # Convert screenshot to base64
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            
            # Create message
            message = {
                'type': 'screenshot',
                'data': screenshot_base64,
                'timestamp': self.last_screenshot_time,
                'url': self.live_browser.current_url
            }
            
            # Broadcast to all clients
            asyncio.run(self._broadcast_message(message))
        except Exception as e:
            logger.error(f"Error broadcasting screenshot: {str(e)}")
    
    async def _broadcast_message(self, message):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast.
        """
        if not websocket_clients:
            return
        
        # Convert message to JSON
        message_json = json.dumps(message)
        
        # Send to all clients
        for client in list(websocket_clients):
            try:
                await client.send(message_json)
            except Exception as e:
                logger.error(f"Error sending message to client: {str(e)}")
                # Remove client if there was an error
                websocket_clients.discard(client)
    
    def _load_recordings(self):
        """
        Load the list of available recordings.
        
        Returns:
            list: A list of recording information.
        """
        recordings = []
        
        try:
            # Get all recording directories
            for item in os.listdir(self.recordings_dir):
                if item.startswith('recording_'):
                    recording_path = os.path.join(self.recordings_dir, item)
                    if os.path.isdir(recording_path):
                        # Extract recording ID
                        recording_id = int(item.split('_')[1])
                        
                        # Load metadata
                        metadata_path = os.path.join(recording_path, 'metadata.json')
                        if os.path.exists(metadata_path):
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                        else:
                            metadata = {}
                        
                        # Count frames
                        frame_count = len([f for f in os.listdir(recording_path) 
                                          if f.startswith('frame_') and f.endswith('.png')])
                        
                        # Calculate size
                        size_bytes = sum(os.path.getsize(os.path.join(recording_path, f)) 
                                        for f in os.listdir(recording_path) if os.path.isfile(os.path.join(recording_path, f)))
                        
                        # Add recording info
                        recordings.append({
                            'id': recording_id,
                            'path': recording_path,
                            'metadata': metadata,
                            'frames': frame_count,
                            'size_bytes': size_bytes,
                            'size_mb': round(size_bytes / (1024 * 1024), 2),
                            'created': datetime.fromtimestamp(recording_id).isoformat()
                        })
        except Exception as e:
            logger.error(f"Error loading recordings: {str(e)}")
        
        # Sort by ID (newest first)
        recordings.sort(key=lambda r: r['id'], reverse=True)
        
        return recordings

# Create a global instance
screen_recorder = None

def init_screen_recorder(live_browser):
    """
    Initialize the Screen Recorder.
    
    Args:
        live_browser: The Live Browser instance.
    
    Returns:
        ScreenRecorder: The Screen Recorder instance.
    """
    global screen_recorder
    if screen_recorder is None:
        screen_recorder = ScreenRecorder(live_browser)
    return screen_recorder

def get_screen_recorder():
    """
    Get the Screen Recorder instance.
    
    Returns:
        ScreenRecorder: The Screen Recorder instance.
    """
    global screen_recorder
    return screen_recorder

# WebSocket handler
async def websocket_handler(websocket, path):
    """
    Handle WebSocket connections.
    
    Args:
        websocket: The WebSocket connection.
        path: The connection path.
    """
    # Register client
    websocket_clients.add(websocket)
    logger.info(f"WebSocket client connected, total clients: {len(websocket_clients)}")
    
    try:
        # Send initial message
        await websocket.send(json.dumps({
            'type': 'connected',
            'message': 'Connected to screen recorder'
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Handle commands
                if data.get('type') == 'command':
                    command = data.get('command')
                    
                    if command == 'start_recording':
                        result = screen_recorder.start_recording()
                        await websocket.send(json.dumps({
                            'type': 'command_result',
                            'command': 'start_recording',
                            'result': result
                        }))
                    
                    elif command == 'stop_recording':
                        result = screen_recorder.stop_recording()
                        await websocket.send(json.dumps({
                            'type': 'command_result',
                            'command': 'stop_recording',
                            'result': result
                        }))
                    
                    elif command == 'get_recordings':
                        recordings = screen_recorder.get_recordings()
                        await websocket.send(json.dumps({
                            'type': 'command_result',
                            'command': 'get_recordings',
                            'result': {
                                'success': True,
                                'recordings': recordings
                            }
                        }))
                    
                    elif command == 'delete_recording':
                        recording_id = data.get('recording_id')
                        if recording_id:
                            result = screen_recorder.delete_recording(recording_id)
                            await websocket.send(json.dumps({
                                'type': 'command_result',
                                'command': 'delete_recording',
                                'result': result
                            }))
                        else:
                            await websocket.send(json.dumps({
                                'type': 'command_result',
                                'command': 'delete_recording',
                                'result': {
                                    'success': False,
                                    'error': 'Recording ID is required'
                                }
                            }))
                    
                    elif command == 'get_recording_frames':
                        recording_id = data.get('recording_id')
                        start_frame = data.get('start_frame', 0)
                        end_frame = data.get('end_frame')
                        
                        if recording_id:
                            result = screen_recorder.get_recording_frames(
                                recording_id, start_frame, end_frame)
                            await websocket.send(json.dumps({
                                'type': 'command_result',
                                'command': 'get_recording_frames',
                                'result': result
                            }))
                        else:
                            await websocket.send(json.dumps({
                                'type': 'command_result',
                                'command': 'get_recording_frames',
                                'result': {
                                    'success': False,
                                    'error': 'Recording ID is required'
                                }
                            }))
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': f'Error handling message: {str(e)}'
                }))
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Unregister client
        websocket_clients.discard(websocket)
        logger.info(f"WebSocket client disconnected, total clients: {len(websocket_clients)}")

# TODO: When implementing database integration, recordings should be stored in the database
# with metadata and references to the frame files. This will allow for better organization,
# searching, and management of recordings. The database should store:
# - Recording ID
# - Start time
# - End time
# - Duration
# - Number of frames
# - Start URL
# - End URL
# - User ID (if applicable)
# - Tags/labels
# - Path to recording files
# - Status (recording, completed, deleted)
