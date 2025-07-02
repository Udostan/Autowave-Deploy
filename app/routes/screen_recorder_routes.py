"""
Screen Recorder Routes

This module provides API routes for the screen recorder functionality.
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify, send_file, Response

from app.visual_browser.live_browser import live_browser
from app.visual_browser.screen_recorder import get_screen_recorder

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
screen_recorder_bp = Blueprint('screen_recorder', __name__)

@screen_recorder_bp.route('/api/screen-recorder/status', methods=['GET'])
def get_status():
    """
    Get the status of the screen recorder.
    
    Returns:
        Response: JSON response with the status.
    """
    try:
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        return jsonify({
            'success': True,
            'is_running': screen_recorder.is_running,
            'is_recording': screen_recorder.is_recording,
            'current_recording': screen_recorder.current_recording['id'] if screen_recorder.is_recording else None
        })
    except Exception as e:
        logger.error(f"Error getting screen recorder status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@screen_recorder_bp.route('/api/screen-recorder/start-capture', methods=['POST'])
def start_capture():
    """
    Start capturing screenshots.
    
    Returns:
        Response: JSON response with the result.
    """
    try:
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        result = screen_recorder.start_capture()
        
        return jsonify({
            'success': result,
            'message': 'Screen capture started' if result else 'Screen capture already running'
        })
    except Exception as e:
        logger.error(f"Error starting screen capture: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@screen_recorder_bp.route('/api/screen-recorder/stop-capture', methods=['POST'])
def stop_capture():
    """
    Stop capturing screenshots.
    
    Returns:
        Response: JSON response with the result.
    """
    try:
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        result = screen_recorder.stop_capture()
        
        return jsonify({
            'success': result,
            'message': 'Screen capture stopped' if result else 'Screen capture not running'
        })
    except Exception as e:
        logger.error(f"Error stopping screen capture: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@screen_recorder_bp.route('/api/screen-recorder/start-recording', methods=['POST'])
def start_recording():
    """
    Start recording screenshots.
    
    Returns:
        Response: JSON response with the result.
    """
    try:
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        # Start the browser if not already running
        if not live_browser.is_running:
            live_browser.start()
        
        # Start capturing if not already capturing
        if not screen_recorder.is_running:
            screen_recorder.start_capture()
        
        # Start recording
        result = screen_recorder.start_recording()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting recording: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@screen_recorder_bp.route('/api/screen-recorder/stop-recording', methods=['POST'])
def stop_recording():
    """
    Stop recording screenshots.
    
    Returns:
        Response: JSON response with the result.
    """
    try:
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        result = screen_recorder.stop_recording()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping recording: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@screen_recorder_bp.route('/api/screen-recorder/recordings', methods=['GET'])
def get_recordings():
    """
    Get a list of available recordings.
    
    Returns:
        Response: JSON response with the recordings.
    """
    try:
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        recordings = screen_recorder.get_recordings()
        
        return jsonify({
            'success': True,
            'recordings': recordings
        })
    except Exception as e:
        logger.error(f"Error getting recordings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@screen_recorder_bp.route('/api/screen-recorder/recordings/<int:recording_id>', methods=['GET'])
def get_recording(recording_id):
    """
    Get information about a specific recording.
    
    Args:
        recording_id: The ID of the recording.
        
    Returns:
        Response: JSON response with the recording information.
    """
    try:
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        recordings = screen_recorder.get_recordings()
        
        for recording in recordings:
            if recording['id'] == recording_id:
                return jsonify({
                    'success': True,
                    'recording': recording
                })
        
        return jsonify({
            'success': False,
            'error': f'Recording {recording_id} not found'
        })
    except Exception as e:
        logger.error(f"Error getting recording {recording_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@screen_recorder_bp.route('/api/screen-recorder/recordings/<int:recording_id>/frames', methods=['GET'])
def get_recording_frames(recording_id):
    """
    Get frames from a recording.
    
    Args:
        recording_id: The ID of the recording.
        
    Returns:
        Response: JSON response with the frames.
    """
    try:
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        # Get query parameters
        start_frame = request.args.get('start_frame', 0, type=int)
        end_frame = request.args.get('end_frame', None, type=int)
        
        result = screen_recorder.get_recording_frames(recording_id, start_frame, end_frame)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting recording frames: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@screen_recorder_bp.route('/api/screen-recorder/recordings/<int:recording_id>', methods=['DELETE'])
def delete_recording(recording_id):
    """
    Delete a recording.
    
    Args:
        recording_id: The ID of the recording.
        
    Returns:
        Response: JSON response with the result.
    """
    try:
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        result = screen_recorder.delete_recording(recording_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error deleting recording {recording_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@screen_recorder_bp.route('/api/screen-recorder/recordings/<int:recording_id>/download', methods=['GET'])
def download_recording(recording_id):
    """
    Download a recording as a ZIP file.
    
    Args:
        recording_id: The ID of the recording.
        
    Returns:
        Response: ZIP file download.
    """
    try:
        import zipfile
        import io
        
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        # Check if recording exists
        recordings = screen_recorder.get_recordings()
        recording = None
        
        for rec in recordings:
            if rec['id'] == recording_id:
                recording = rec
                break
        
        if not recording:
            return jsonify({
                'success': False,
                'error': f'Recording {recording_id} not found'
            })
        
        # Create a ZIP file in memory
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add metadata file
            metadata_path = os.path.join(recording['path'], 'metadata.json')
            if os.path.exists(metadata_path):
                zipf.write(metadata_path, 'metadata.json')
            
            # Add frame files
            for filename in os.listdir(recording['path']):
                if filename.startswith('frame_') and filename.endswith('.png'):
                    file_path = os.path.join(recording['path'], filename)
                    zipf.write(file_path, filename)
        
        # Seek to the beginning of the file
        memory_file.seek(0)
        
        # Return the ZIP file
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'recording_{recording_id}.zip'
        )
    except Exception as e:
        logger.error(f"Error downloading recording {recording_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@screen_recorder_bp.route('/api/screen-recorder/last-screenshot', methods=['GET'])
def get_last_screenshot():
    """
    Get the last screenshot taken by the screen recorder.
    
    Returns:
        Response: PNG image or JSON error.
    """
    try:
        screen_recorder = get_screen_recorder()
        
        if not screen_recorder:
            return jsonify({
                'success': False,
                'error': 'Screen recorder not initialized'
            })
        
        if not screen_recorder.last_screenshot:
            return jsonify({
                'success': False,
                'error': 'No screenshot available'
            })
        
        # Create a response with the PNG data
        return Response(
            screen_recorder.last_screenshot,
            mimetype='image/png'
        )
    except Exception as e:
        logger.error(f"Error getting last screenshot: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
