"""
AutoWave Data Storage Service
Comprehensive service for storing all user activities in Supabase and integrating with Qdrant memory.
"""

import os
import json
import uuid
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase not available. Data storage features will be disabled.")

from app.services.memory_service import memory_service

logger = logging.getLogger(__name__)

@dataclass
class ActivityData:
    """Data structure for user activities."""
    user_id: str
    agent_type: str
    activity_type: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    file_uploads: List[Dict[str, Any]] = None
    processing_time_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    session_id: Optional[str] = None

class DataStorageService:
    """
    Centralized data storage service for all AutoWave agents.
    Stores activities in Supabase and integrates with Qdrant memory.
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.admin_client: Optional[Client] = None
        
        if SUPABASE_AVAILABLE:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client."""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            if not supabase_url or not supabase_key:
                logger.warning("Supabase credentials not found. Data storage disabled.")
                return
            
            # Public client for user operations
            self.client = create_client(supabase_url, supabase_key)
            
            # Admin client for administrative operations
            if supabase_service_key:
                self.admin_client = create_client(supabase_url, supabase_service_key)
            
            logger.info("Data storage service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize data storage service: {e}")
            self.client = None
            self.admin_client = None
    
    def is_available(self) -> bool:
        """Check if data storage service is available."""
        return SUPABASE_AVAILABLE and self.client is not None
    
    def store_activity(self, activity: ActivityData) -> Optional[str]:
        """
        Store a user activity in Supabase.
        
        Args:
            activity: ActivityData object containing all activity information
            
        Returns:
            str: Activity ID if successful, None otherwise
        """
        if not self.is_available():
            logger.warning("Data storage not available")
            return None
        
        try:
            # Prepare activity data
            activity_data = {
                'user_id': activity.user_id,
                'agent_type': activity.agent_type,
                'activity_type': activity.activity_type,
                'input_data': activity.input_data,
                'output_data': activity.output_data or {},
                'processing_time_ms': activity.processing_time_ms,
                'success': activity.success,
                'error_message': activity.error_message,
                'metadata': activity.metadata or {},
                'session_id': activity.session_id
            }

            # Skip file_uploads for now until database column is added
            # TODO: Re-enable once file_uploads column is added to Supabase
            # if activity.file_uploads:
            #     activity_data['file_uploads'] = activity.file_uploads

            # Insert activity
            result = self.client.table('user_activities').insert(activity_data).execute()
            
            if result.data:
                activity_id = result.data[0]['id']
                logger.info(f"Stored activity {activity_id} for user {activity.user_id}")
                
                # Store in memory if available
                self._store_in_memory(activity, activity_id)
                
                # Update analytics
                self._update_analytics(activity)
                
                return activity_id
            else:
                logger.error("Failed to store activity: No data returned")
                return None
                
        except Exception as e:
            # Check if it's a file_uploads column error and retry without it
            error_str = str(e)
            error_dict = getattr(e, 'details', None) or getattr(e, 'args', [])

            # Check for file_uploads column error in various formats
            is_file_uploads_error = (
                ("file_uploads" in error_str and ("column" in error_str.lower() or "PGRST204" in error_str)) or
                (isinstance(error_dict, (list, tuple)) and len(error_dict) > 0 and
                 isinstance(error_dict[0], dict) and
                 "file_uploads" in str(error_dict[0]).lower() and "column" in str(error_dict[0]).lower()) or
                ("PGRST204" in error_str and "file_uploads" in error_str)
            )

            if is_file_uploads_error:
                logger.warning(f"file_uploads column not found, retrying without it: {e}")
                try:
                    # Remove file_uploads and retry
                    activity_data_retry = {k: v for k, v in activity_data.items() if k != 'file_uploads'}
                    result = self.client.table('user_activities').insert(activity_data_retry).execute()

                    if result.data:
                        activity_id = result.data[0]['id']
                        logger.info(f"Stored activity {activity_id} for user {activity.user_id} (without file_uploads)")

                        # Store in memory if available
                        self._store_in_memory(activity, activity_id)

                        # Update analytics
                        self._update_analytics(activity)

                        return activity_id
                    else:
                        logger.error("Failed to store activity on retry: No data returned")
                        return None
                except Exception as retry_e:
                    logger.error(f"Failed to store activity on retry: {retry_e}")
                    return None
            else:
                logger.error(f"Failed to store activity: {e}")
                return None
    
    def store_chat_conversation(self, user_id: str, activity_id: str, message: str, 
                              response: str, model_used: str = None, tokens_used: int = None) -> bool:
        """Store chat conversation details."""
        if not self.is_available():
            return False
        
        try:
            chat_data = {
                'user_id': user_id,
                'activity_id': activity_id,
                'message': message,
                'response': response,
                'model_used': model_used,
                'tokens_used': tokens_used
            }
            
            result = self.client.table('chat_conversations').insert(chat_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to store chat conversation: {e}")
            return False
    
    def store_prime_agent_task(self, user_id: str, activity_id: str, task_description: str,
                              use_visual_browser: bool = False, steps_completed: List[Dict] = None,
                              final_result: str = None, execution_time_ms: int = None) -> bool:
        """Store Prime Agent task details."""
        if not self.is_available():
            return False
        
        try:
            task_data = {
                'user_id': user_id,
                'activity_id': activity_id,
                'task_description': task_description,
                'use_visual_browser': use_visual_browser,
                'steps_completed': steps_completed or [],
                'final_result': final_result,
                'execution_time_ms': execution_time_ms,
                'task_status': 'completed' if final_result else 'pending'
            }
            
            result = self.client.table('prime_agent_tasks').insert(task_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to store Prime Agent task: {e}")
            return False
    
    def store_code_project(self, user_id: str, activity_id: str, description: str,
                          programming_language: str = None, framework: str = None,
                          generated_files: List[Dict] = None, project_name: str = None) -> bool:
        """Store Agentic Code project details."""
        if not self.is_available():
            return False
        
        try:
            project_data = {
                'user_id': user_id,
                'activity_id': activity_id,
                'project_name': project_name,
                'description': description,
                'programming_language': programming_language,
                'framework': framework,
                'generated_files': generated_files or []
            }
            
            result = self.client.table('code_projects').insert(project_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to store code project: {e}")
            return False
    
    def store_research_query(self, user_id: str, activity_id: str, query: str,
                           research_questions: List[str] = None, findings: List[Dict] = None,
                           final_report: str = None, sources_count: int = 0) -> bool:
        """Store Research Lab query details."""
        if not self.is_available():
            return False
        
        try:
            research_data = {
                'user_id': user_id,
                'activity_id': activity_id,
                'query': query,
                'research_questions': research_questions or [],
                'findings': findings or [],
                'final_report': final_report,
                'sources_count': sources_count
            }
            
            result = self.client.table('research_queries').insert(research_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to store research query: {e}")
            return False
    
    def store_context7_usage(self, user_id: str, activity_id: str, tool_name: str,
                           request_details: Dict[str, Any], result_data: Dict[str, Any] = None,
                           tool_category: str = None, screenshots: List[str] = None,
                           success: bool = True) -> bool:
        """Store Context7 tool usage details."""
        if not self.is_available():
            return False
        
        try:
            usage_data = {
                'user_id': user_id,
                'activity_id': activity_id,
                'tool_name': tool_name,
                'tool_category': tool_category,
                'request_details': request_details,
                'result_data': result_data or {},
                'screenshots': screenshots or [],
                'success': success
            }
            
            result = self.client.table('context7_usage').insert(usage_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to store Context7 usage: {e}")
            return False
    
    def store_file_upload(self, user_id: str, activity_id: str, filename: str,
                         file_type: str, file_size: int = None, mime_type: str = None,
                         file_content: str = None, file_url: str = None,
                         analysis_result: Dict[str, Any] = None) -> bool:
        """Store file upload details."""
        if not self.is_available():
            return False
        
        try:
            file_data = {
                'user_id': user_id,
                'activity_id': activity_id,
                'filename': filename,
                'file_type': file_type,
                'file_size': file_size,
                'mime_type': mime_type,
                'file_content': file_content,
                'file_url': file_url,
                'analysis_result': analysis_result or {}
            }
            
            result = self.client.table('file_uploads').insert(file_data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Failed to store file upload: {e}")
            return False
    
    def _store_in_memory(self, activity: ActivityData, activity_id: str):
        """Store activity in Qdrant memory for enhanced AI capabilities."""
        if not memory_service.is_available():
            return
        
        try:
            # Create memory content
            content_parts = [
                f"Activity: {activity.activity_type}",
                f"Agent: {activity.agent_type}",
                f"Input: {json.dumps(activity.input_data)[:500]}..."
            ]
            
            if activity.output_data:
                content_parts.append(f"Output: {json.dumps(activity.output_data)[:500]}...")
            
            content = "\n".join(content_parts)
            
            # Store in memory
            memory_service.store_memory(
                agent_type=activity.agent_type,
                user_id=activity.user_id,
                content=content,
                metadata={
                    'activity_id': activity_id,
                    'activity_type': activity.activity_type,
                    'success': activity.success,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to store in memory: {e}")
    
    def _update_analytics(self, activity: ActivityData):
        """Update daily analytics for the user."""
        if not self.is_available():
            return
        
        try:
            today = date.today()
            
            # Upsert analytics record
            analytics_data = {
                'user_id': activity.user_id,
                'date': today.isoformat(),
                'agent_type': activity.agent_type,
                'activity_count': 1,
                'total_processing_time_ms': activity.processing_time_ms or 0,
                'files_uploaded': len(activity.file_uploads) if activity.file_uploads else 0
            }
            
            # Try to update existing record, insert if not exists
            result = self.client.table('usage_analytics').upsert(
                analytics_data,
                on_conflict='user_id,date,agent_type'
            ).execute()
            
        except Exception as e:
            logger.error(f"Failed to update analytics: {e}")

# Global data storage service instance
data_storage = DataStorageService()
