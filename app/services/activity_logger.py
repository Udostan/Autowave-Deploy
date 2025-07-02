"""
AutoWave Activity Logger
Decorator and utility functions to automatically log user activities across all agents.
"""

import time
import json
import logging
import functools
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from app.services.data_storage_service import data_storage
from app.services.enhanced_history_service import enhanced_history_service
from app.services.file_processor import file_processor

logger = logging.getLogger(__name__)

class ActivityLogger:
    """
    Activity logging service that captures user interactions across all agents.
    """
    
    def __init__(self):
        self.active_sessions = {}  # Track active user sessions
    
    def start_session(self, user_id: str, agent_type: str, session_id: str = None) -> str:
        """
        Start a new user session for an agent.
        
        Args:
            user_id: User identifier
            agent_type: Type of agent
            session_id: Optional session ID, will generate if not provided
            
        Returns:
            str: Session ID
        """
        if not session_id:
            session_id = f"{agent_type}_{user_id}_{int(time.time())}"
        
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'agent_type': agent_type,
            'started_at': datetime.now(),
            'interaction_count': 0
        }
        
        logger.info(f"Started session {session_id} for user {user_id} on {agent_type}")
        return session_id
    
    def end_session(self, session_id: str):
        """End a user session."""
        if session_id in self.active_sessions:
            session_data = self.active_sessions.pop(session_id)
            logger.info(f"Ended session {session_id} with {session_data['interaction_count']} interactions")
    
    def log_activity(self, 
                    user_id: str,
                    agent_type: str,
                    activity_type: str,
                    input_data: Dict[str, Any],
                    output_data: Dict[str, Any] = None,
                    processing_time_ms: int = None,
                    success: bool = True,
                    error_message: str = None,
                    session_id: str = None,
                    metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Log a user activity.
        
        Returns:
            str: Activity ID if successful
        """
        try:
            # Store activity using enhanced history service for proper session management
            activity_id = enhanced_history_service.log_activity(
                user_id=user_id,
                agent_type=agent_type,
                activity_type=activity_type,
                input_data=input_data,
                output_data=output_data,
                session_id=session_id,
                processing_time_ms=processing_time_ms,
                success=success,
                error_message=error_message
            )
            
            # Update session interaction count
            if session_id and session_id in self.active_sessions:
                self.active_sessions[session_id]['interaction_count'] += 1
            
            return activity_id
            
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            return None
    
    def _extract_file_uploads(self, content: str) -> List[Dict[str, Any]]:
        """Extract file upload information from content."""
        file_uploads = []
        
        if not content or not isinstance(content, str):
            return file_uploads
        
        try:
            # Check for file markers
            if "--- File:" in content or "--- Image:" in content:
                # Parse file information
                processed_files = file_processor.parse_files_from_content(content)
                
                for file_info in processed_files.get('processed_files', []):
                    file_uploads.append({
                        'filename': file_info.get('filename', 'unknown'),
                        'file_type': file_info.get('type', 'unknown'),
                        'mime_type': file_info.get('mime_type', ''),
                        'size': len(file_info.get('content', '')),
                        'analysis': file_info.get('analysis', {})
                    })
        
        except Exception as e:
            logger.error(f"Error extracting file uploads: {e}")
        
        return file_uploads

def log_agent_activity(agent_type: str, activity_type: str = None):
    """
    Decorator to automatically log agent activities.
    
    Args:
        agent_type: Type of agent ('autowave_chat', 'prime_agent', etc.)
        activity_type: Type of activity (will infer from function name if not provided)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            user_id = None
            session_id = None
            input_data = {}
            output_data = {}
            success = True
            error_message = None
            
            try:
                # Extract user_id and input data from arguments
                if args:
                    # For functions with positional arguments
                    if isinstance(args[0], str):
                        # First argument might be user input
                        input_data = {'input': args[0]}
                    elif isinstance(args[0], dict):
                        # First argument might be request data
                        input_data = args[0]
                        user_id = input_data.get('user_id')
                
                # Extract from kwargs
                if 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                if 'session_id' in kwargs:
                    session_id = kwargs['session_id']
                
                # Merge kwargs into input_data
                input_data.update({k: v for k, v in kwargs.items() 
                                 if k not in ['user_id', 'session_id']})
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Extract output data
                if isinstance(result, dict):
                    output_data = result
                elif isinstance(result, str):
                    output_data = {'response': result}
                else:
                    output_data = {'result': str(result)}
                
                return result
                
            except Exception as e:
                success = False
                error_message = str(e)
                logger.error(f"Error in {func.__name__}: {e}")
                raise
                
            finally:
                # Log the activity
                processing_time = int((time.time() - start_time) * 1000)
                
                # Determine activity type
                final_activity_type = activity_type or func.__name__.replace('_', ' ').title()
                
                # Only log if we have a user_id (authenticated user)
                if user_id:
                    activity_logger.log_activity(
                        user_id=user_id,
                        agent_type=agent_type,
                        activity_type=final_activity_type,
                        input_data=input_data,
                        output_data=output_data,
                        processing_time_ms=processing_time,
                        success=success,
                        error_message=error_message,
                        session_id=session_id
                    )
        
        return wrapper
    return decorator

# Specific logging functions for each agent

def log_chat_activity(user_id: str, message: str, response: str, 
                     model_used: str = None, tokens_used: int = None,
                     processing_time_ms: int = None, session_id: str = None) -> Optional[str]:
    """Log AutoWave Chat activity."""
    activity_id = activity_logger.log_activity(
        user_id=user_id,
        agent_type='autowave_chat',
        activity_type='chat',
        input_data={'message': message},
        output_data={'response': response, 'model_used': model_used, 'tokens_used': tokens_used},
        processing_time_ms=processing_time_ms,
        session_id=session_id
    )
    
    # Store detailed chat conversation
    if activity_id:
        data_storage.store_chat_conversation(
            user_id=user_id,
            activity_id=activity_id,
            message=message,
            response=response,
            model_used=model_used,
            tokens_used=tokens_used
        )
    
    return activity_id

def log_prime_agent_activity(user_id: str, task: str, result: Dict[str, Any],
                            use_visual_browser: bool = False, processing_time_ms: int = None,
                            session_id: str = None) -> Optional[str]:
    """Log Prime Agent activity."""
    activity_id = activity_logger.log_activity(
        user_id=user_id,
        agent_type='prime_agent',
        activity_type='task_execution',
        input_data={'task': task, 'use_visual_browser': use_visual_browser},
        output_data=result,
        processing_time_ms=processing_time_ms,
        session_id=session_id
    )
    
    # Store detailed task information
    if activity_id:
        data_storage.store_prime_agent_task(
            user_id=user_id,
            activity_id=activity_id,
            task_description=task,
            use_visual_browser=use_visual_browser,
            steps_completed=result.get('steps', []),
            final_result=result.get('result', ''),
            execution_time_ms=processing_time_ms
        )
    
    return activity_id

def log_agentic_code_activity(user_id: str, message: str, result: Dict[str, Any],
                             current_code: str = '', processing_time_ms: int = None,
                             session_id: str = None) -> Optional[str]:
    """Log Agentic Code activity."""
    activity_id = activity_logger.log_activity(
        user_id=user_id,
        agent_type='agentic_code',
        activity_type='code_generation',
        input_data={'message': message, 'current_code': current_code},
        output_data=result,
        processing_time_ms=processing_time_ms,
        session_id=session_id
    )
    
    # Store detailed code project information
    if activity_id:
        data_storage.store_code_project(
            user_id=user_id,
            activity_id=activity_id,
            description=message,
            programming_language=result.get('language'),
            framework=result.get('framework'),
            generated_files=result.get('files', [])
        )
    
    return activity_id

def log_research_activity(user_id: str, query: str, result: Dict[str, Any],
                         processing_time_ms: int = None, session_id: str = None) -> Optional[str]:
    """Log Research Lab activity."""
    activity_id = activity_logger.log_activity(
        user_id=user_id,
        agent_type='research_lab',
        activity_type='research',
        input_data={'query': query},
        output_data=result,
        processing_time_ms=processing_time_ms,
        session_id=session_id
    )
    
    # Store detailed research information
    if activity_id:
        data_storage.store_research_query(
            user_id=user_id,
            activity_id=activity_id,
            query=query,
            research_questions=result.get('research_questions', []),
            findings=result.get('findings', []),
            final_report=result.get('final_report', ''),
            sources_count=result.get('sources_count', 0)
        )
    
    return activity_id

def log_context7_activity(user_id: str, tool_name: str, request_details: Dict[str, Any],
                         result_data: Dict[str, Any], tool_category: str = None,
                         processing_time_ms: int = None, session_id: str = None) -> Optional[str]:
    """Log Prime Agent Tools activity."""
    activity_id = activity_logger.log_activity(
        user_id=user_id,
        agent_type='context7_tools',
        activity_type='tool_usage',
        input_data={'tool_name': tool_name, 'request_details': request_details},
        output_data=result_data,
        processing_time_ms=processing_time_ms,
        session_id=session_id
    )
    
    # Store detailed tool usage information
    if activity_id:
        data_storage.store_context7_usage(
            user_id=user_id,
            activity_id=activity_id,
            tool_name=tool_name,
            tool_category=tool_category,
            request_details=request_details,
            result_data=result_data,
            screenshots=result_data.get('screenshots', []),
            success=result_data.get('success', True)
        )
    
    return activity_id

# Global activity logger instance
activity_logger = ActivityLogger()
