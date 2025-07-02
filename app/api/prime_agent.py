"""
API for the Prime Agent.

This module provides API endpoints for interacting with the Prime Agent.
"""

import os
import time
import json
import logging
import traceback
from flask import Blueprint, request, jsonify, Response, stream_with_context

from app.prime_agent.prime_agent import prime_agent
from app.prime_agent.task_manager import task_manager
from app.services.file_processor import file_processor
from app.services.activity_logger import log_prime_agent_activity

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Blueprint
prime_agent_api = Blueprint('prime_agent_api', __name__, url_prefix='/api/prime-agent')

@prime_agent_api.route('/execute-task', methods=['POST'])
def execute_task():
    """
    Execute a task.
    """
    start_time = time.time()
    try:
        data = request.json or {}
        task = data.get('task')
        use_visual_browser = data.get('use_visual_browser', False)
        user_id = data.get('user_id')  # Get user_id from request if available
        session_id = data.get('session_id')  # Get session_id from request if available

        if not task:
            return jsonify({
                'success': False,
                'error': 'Task is required'
            })

        # Check and consume credits before processing
        from flask import session as flask_session
        from app.services.credit_service import credit_service

        # Use user_id from request or session
        if not user_id:
            user_id = flask_session.get('user_id', 'anonymous')

        # Determine credit cost based on task complexity and visual browser usage
        if use_visual_browser:
            task_type = 'prime_agent_visual_browser'
        elif len(task) > 500 or any(keyword in task.lower() for keyword in ['research', 'analyze', 'comprehensive', 'detailed']):
            task_type = 'prime_agent_complex'
        else:
            task_type = 'prime_agent_basic'

        # Consume credits
        credit_result = credit_service.consume_credits(user_id, task_type)

        if not credit_result['success']:
            return jsonify({
                'success': False,
                'error': credit_result['error'],
                'credits_needed': credit_result.get('credits_needed'),
                'credits_available': credit_result.get('credits_available')
            }), 402

        # Process uploaded files if present
        enhanced_task = task
        file_context = ""

        if "--- File:" in task or "--- Image:" in task:
            logger.info("File content detected in Prime Agent task, processing files...")
            try:
                # Extract the original user task (before file content)
                parts = task.split('\n\n--- File:')
                if len(parts) > 1:
                    original_task = parts[0]
                    file_content = '\n\n--- File:' + '\n\n--- File:'.join(parts[1:])
                else:
                    parts = task.split('\n\n--- Image:')
                    if len(parts) > 1:
                        original_task = parts[0]
                        file_content = '\n\n--- Image:' + '\n\n--- Image:'.join(parts[1:])
                    else:
                        original_task = task
                        file_content = ""

                if file_content:
                    # Use the file processor to enhance the task
                    enhanced_task = file_processor.enhance_prompt_with_files(original_task, file_content)
                    file_context = f" (with {file_content.count('--- File:') + file_content.count('--- Image:')} uploaded file(s))"
                    logger.info(f"Enhanced Prime Agent task with file analysis: {len(enhanced_task)} characters")
            except Exception as e:
                logger.error(f"Error processing files in Prime Agent task: {str(e)}")
                # Continue with original task if file processing fails
                enhanced_task = task

        result = prime_agent.execute_task(enhanced_task, use_visual_browser)

        # Calculate processing time and log activity
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Log activity if user_id is available
        if user_id:
            try:
                log_prime_agent_activity(
                    user_id=user_id,
                    task=task,
                    result=result,
                    use_visual_browser=use_visual_browser,
                    processing_time_ms=processing_time_ms,
                    session_id=session_id
                )
            except Exception as e:
                logger.error(f"Failed to log Prime Agent activity: {e}")

        # Add credit consumption info to response
        if 'credit_result' in locals():
            result['credits_consumed'] = credit_result['credits_consumed']
            result['remaining_credits'] = credit_result['remaining_credits']

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in execute-task endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@prime_agent_api.route('/task-status', methods=['GET'])
def task_status():
    """
    Get the status of a task.
    """
    try:
        task_id = request.args.get('task_id')
        
        if not task_id:
            return jsonify({
                'success': False,
                'error': 'Task ID is required'
            })
        
        result = prime_agent.get_task_status(task_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in task-status endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@prime_agent_api.route('/execute-multi-tool-task', methods=['POST'])
def execute_multi_tool_task():
    """
    Execute a multi-tool orchestration task directly.
    This bypasses all other detection logic and goes straight to multi-tool orchestration.
    """
    start_time = time.time()
    try:
        data = request.json or {}
        task = data.get('task')
        user_id = data.get('user_id')
        session_id = data.get('session_id')

        if not task:
            return jsonify({
                'success': False,
                'error': 'Task is required'
            })

        # Check and consume credits
        from flask import session as flask_session
        from app.services.credit_service import credit_service

        if not user_id:
            user_id = flask_session.get('user_id', 'anonymous')

        # Multi-tool tasks cost more credits
        task_type = 'prime_agent_multi_tool'
        credit_result = credit_service.consume_credits(user_id, task_type)

        if not credit_result['success']:
            return jsonify({
                'success': False,
                'error': credit_result['error'],
                'credits_needed': credit_result.get('credits_needed'),
                'credits_available': credit_result.get('credits_available')
            }), 402

        # Execute multi-tool task directly
        result = prime_agent.execute_multi_tool_task_direct(task)

        # Calculate processing time and log activity
        processing_time_ms = int((time.time() - start_time) * 1000)

        if user_id:
            try:
                log_prime_agent_activity(
                    user_id=user_id,
                    task=task,
                    result=result,
                    use_visual_browser=False,
                    processing_time_ms=processing_time_ms,
                    session_id=session_id
                )
            except Exception as e:
                logger.error(f"Failed to log Prime Agent activity: {e}")

        # Add credit consumption info to response
        result['credits_consumed'] = credit_result['credits_consumed']
        result['remaining_credits'] = credit_result['remaining_credits']

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in execute-multi-tool-task endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@prime_agent_api.route('/task-progress', methods=['GET'])
def task_progress():
    """
    Stream the progress of a task using Server-Sent Events (SSE).
    """
    try:
        task_id = request.args.get('task_id')
        
        if not task_id:
            return jsonify({
                'success': False,
                'error': 'Task ID is required'
            })
        
        def generate():
            # Send initial event
            yield f"data: {json.dumps({'status': 'connecting', 'message': 'Connected to server'})}\n\n"
            
            # Get initial progress
            progress = task_manager.get_task_progress(task_id)
            last_progress_index = len(progress) - 1 if progress else -1
            
            # Send initial progress
            if progress:
                for i, p in enumerate(progress):
                    yield f"data: {json.dumps(p)}\n\n"
            
            # Stream new progress
            while True:
                # Get current status
                status = task_manager.get_task_status(task_id)
                
                # If task is complete or failed, send final event and stop
                if status in ['complete', 'error']:
                    result = task_manager.get_task_result(task_id)
                    if result:
                        yield f"data: {json.dumps({'status': status, 'result': result})}\n\n"
                    break
                
                # Get new progress
                progress = task_manager.get_task_progress(task_id)
                
                # Send new progress
                if len(progress) > last_progress_index + 1:
                    for i in range(last_progress_index + 1, len(progress)):
                        yield f"data: {json.dumps(progress[i])}\n\n"
                    last_progress_index = len(progress) - 1
                
                # Wait a bit before checking again
                time.sleep(0.5)
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )
    except Exception as e:
        logger.error(f"Error in task-progress endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })
