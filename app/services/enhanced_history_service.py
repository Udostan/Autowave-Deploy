"""
Enhanced History Service for AutoWave

This service provides comprehensive activity tracking and history management
across all AutoWave agents with real-time session management and unified tracking.

Features:
- Unified history tracking across all agents
- Session-based activity management
- Real-time activity logging
- Clickable session restoration
- Supabase integration with optimized queries
"""

import logging
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase not available. Enhanced history features will be disabled.")

logger = logging.getLogger(__name__)

class EnhancedHistoryService:
    """
    Enhanced service for comprehensive activity tracking and history management.
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        
        if SUPABASE_AVAILABLE:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client."""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if not supabase_url or not supabase_key:
                logger.warning("Supabase credentials not found. Enhanced history service disabled.")
                return
            
            self.client = create_client(supabase_url, supabase_key)
            logger.info("Enhanced history service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced history service: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if enhanced history service is available."""
        return SUPABASE_AVAILABLE and self.client is not None and self._check_tables_exist()

    def _check_tables_exist(self) -> bool:
        """Check if the required database tables exist."""
        try:
            # Try to query the tables to see if they exist
            self.client.table('agent_sessions').select('id').limit(1).execute()
            self.client.table('user_activities').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.warning(f"History tables not available: {e}")
            return False
    
    def log_activity(self, user_id: str, agent_type: str, activity_type: str,
                    input_data: Dict[str, Any], output_data: Optional[Dict[str, Any]] = None,
                    session_id: Optional[str] = None, processing_time_ms: Optional[int] = None,
                    success: bool = True, error_message: Optional[str] = None,
                     continuation_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a new activity to the history.
        
        Args:
            user_id: User identifier
            agent_type: Type of agent (autowave_chat, prime_agent, agentic_code, etc.)
            activity_type: Type of activity (chat, task_execution, code_generation, etc.)
            input_data: Input data for the activity
            output_data: Output data from the activity
            session_id: Session identifier (optional)
            processing_time_ms: Processing time in milliseconds
            success: Whether the activity was successful
            error_message: Error message if activity failed
            
        Returns:
            Activity ID
        """
        if not self.is_available():
            return str(uuid.uuid4())  # Return dummy ID if service unavailable
        
        try:
            activity_id = str(uuid.uuid4())
            
            # Create session if not provided
            if not session_id:
                session_id = self._create_session(user_id, agent_type)
            
            # Prepare continuation data for activity restoration
            continuation_context = continuation_data or {}
            continuation_context.update({
                'agent_type': agent_type,
                'activity_type': activity_type,
                'timestamp': datetime.now().isoformat(),
                'can_continue': True
            })

            activity_data = {
                'id': activity_id,
                'user_id': user_id,
                'session_id': session_id,
                'agent_type': agent_type,
                'activity_type': activity_type,
                'input_data': input_data,
                'output_data': output_data,
                'processing_time_ms': processing_time_ms,
                'success': success,
                'error_message': error_message,
                'created_at': datetime.now().isoformat(),
                'metadata': {
                    'continuation_data': continuation_context
                }
            }

            # Try to insert activity, handle file_uploads column error gracefully
            try:
                result = self.client.table('user_activities').insert(activity_data).execute()
            except Exception as e:
                # Check if it's a file_uploads column error
                if "file_uploads" in str(e) and ("column" in str(e).lower() or "PGRST204" in str(e)):
                    logger.warning(f"file_uploads column not found in enhanced_history_service, continuing without it: {e}")
                    # The insert should work since we're not including file_uploads field
                    result = self.client.table('user_activities').insert(activity_data).execute()
                else:
                    raise e
            
            # Update session with latest activity
            self._update_session(session_id, activity_id)
            
            logger.info(f"Activity logged: {activity_id} for user {user_id}")
            return activity_id
            
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            return str(uuid.uuid4())  # Return dummy ID on error
    
    def _create_session(self, user_id: str, agent_type: str) -> str:
        """Create a new session."""
        try:
            session_id = str(uuid.uuid4())
            session_data = {
                'id': session_id,
                'user_id': user_id,
                'agent_type': agent_type,
                'session_name': f"{agent_type.replace('_', ' ').title()} Session",
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_active': True
            }
            
            self.client.table('agent_sessions').insert(session_data).execute()
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return str(uuid.uuid4())
    
    def _update_session(self, session_id: str, latest_activity_id: str):
        """Update session with latest activity."""
        try:
            self.client.table('agent_sessions').update({
                'latest_activity_id': latest_activity_id,
                'updated_at': datetime.now().isoformat()
            }).eq('id', session_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
    
    def get_unified_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get unified history across all agents, grouped by sessions.

        Returns:
            List of session-based history items
        """
        if not self.is_available():
            # Return sample data if database is not available
            return self._get_fallback_history()

        try:
            # First check if tables exist
            try:
                self.client.table('agent_sessions').select('id').limit(1).execute()
                self.client.table('user_activities').select('id').limit(1).execute()
            except Exception as table_error:
                logger.warning(f"Database tables not found: {table_error}")
                return self._get_setup_required_fallback()

            # Get recent sessions with their latest activities
            sessions_result = self.client.table('agent_sessions').select(
                'id, agent_type, session_name, created_at, updated_at, '
                'latest_activity_id, is_active'
            ).eq('user_id', user_id).order('updated_at', desc=True).limit(limit).execute()

            if not sessions_result.data:
                return self._get_demo_history()

            history_items = []

            for session in sessions_result.data:
                # Get the latest activity for this session to show as preview
                if session.get('latest_activity_id'):
                    activity_result = self.client.table('user_activities').select(
                        'input_data, output_data, activity_type, success, created_at'
                    ).eq('id', session['latest_activity_id']).execute()

                    if activity_result.data:
                        activity = activity_result.data[0]

                        # Create a unified history item with continuation support
                        history_item = {
                            'session_id': session['id'],
                            'agent_type': session['agent_type'],
                            'session_name': session['session_name'],
                            'activity_type': activity['activity_type'],
                            'preview_text': self._generate_preview_text(activity['input_data'], session['agent_type']),
                            'success': activity['success'],
                            'created_at': session['created_at'],
                            'updated_at': session['updated_at'],
                            'is_active': session.get('is_active', False),
                            'can_continue': True,
                            'continuation_url': self._generate_continuation_url(session['agent_type'], session['id']),
                            'agent_display_name': self._get_agent_display_name(session['agent_type'])
                        }

                        history_items.append(history_item)

            return history_items if history_items else self._get_demo_history()

        except Exception as e:
            logger.error(f"Failed to get unified history: {e}")
            return self._get_demo_history()

    def _get_setup_required_fallback(self) -> List[Dict[str, Any]]:
        """Return setup message when database tables don't exist."""
        return [
            {
                'session_id': 'setup-required',
                'agent_type': 'system',
                'session_name': 'Database Setup Required',
                'activity_type': 'setup_message',
                'preview_text': 'Database tables not yet created. Please run the SQL setup script.',
                'success': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_active': False,
                'can_continue': False,
                'continuation_url': '#',
                'agent_display_name': 'System'
            },
            {
                'session_id': 'setup-info',
                'agent_type': 'system',
                'session_name': 'Setup Instructions',
                'activity_type': 'setup_info',
                'preview_text': 'To enable history tracking, create the database tables using create_history_tables.sql',
                'success': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_active': False,
                'can_continue': False,
                'continuation_url': '#',
                'agent_display_name': 'System'
            }
        ]

    def _get_demo_history(self) -> List[Dict[str, Any]]:
        """Return demo history data when no real data exists."""
        return [
            {
                'session_id': 'demo-1',
                'agent_type': 'autowave_chat',
                'session_name': 'Welcome Chat',
                'activity_type': 'chat_message',
                'preview_text': 'Welcome to AutoWave! Start using any agent to see your activity history here.',
                'success': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_active': False,
                'can_continue': True,
                'continuation_url': '/autowave-chat',
                'agent_display_name': 'AutoWave Chat'
            },
            {
                'session_id': 'demo-2',
                'agent_type': 'agentic_code',
                'session_name': 'Code Generation Demo',
                'activity_type': 'code_generation',
                'preview_text': 'Try Agent Alpha to generate professional code and see your activities tracked here.',
                'success': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_active': False,
                'can_continue': True,
                'continuation_url': '/agentic-code',
                'agent_display_name': 'Agent Alpha'
            },
            {
                'session_id': 'demo-3',
                'agent_type': 'prime_agent',
                'session_name': 'Prime Agent Demo',
                'activity_type': 'task_execution',
                'preview_text': 'Use Prime Agent Tools for advanced tasks and workflow automation.',
                'success': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_active': False,
                'can_continue': True,
                'continuation_url': '/prime-agent-tools',
                'agent_display_name': 'Prime Agent'
            }
        ]
    
    def _generate_preview_text(self, input_data: Dict[str, Any], agent_type: str) -> str:
        """Generate preview text for history items."""
        try:
            if agent_type == 'autowave_chat':
                return input_data.get('message', 'Chat conversation')[:100]
            elif agent_type == 'prime_agent':
                return input_data.get('task', 'Prime Agent task')[:100]
            elif agent_type == 'agentic_code':
                return input_data.get('message', 'Code generation')[:100]
            elif agent_type == 'research_lab':
                return input_data.get('query', 'Research query')[:100]
            elif agent_type == 'document_generator':
                return input_data.get('content', 'Document generation')[:100]
            else:
                return f"{agent_type.replace('_', ' ').title()} activity"
        except:
            return f"{agent_type.replace('_', ' ').title()} activity"
    
    def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific session.
        
        Returns:
            Session details with all activities
        """
        if not self.is_available():
            return {}
        
        try:
            # Get session info
            session_result = self.client.table('agent_sessions').select('*').eq('id', session_id).execute()
            
            if not session_result.data:
                return {}
            
            session = session_result.data[0]
            
            # Get all activities for this session
            activities_result = self.client.table('user_activities').select(
                'id, activity_type, input_data, output_data, success, '
                'error_message, processing_time_ms, created_at'
            ).eq('session_id', session_id).order('created_at', asc=True).execute()
            
            return {
                'session': session,
                'activities': activities_result.data if activities_result.data else []
            }
            
        except Exception as e:
            logger.error(f"Failed to get session details: {e}")
            return {}

    def get_activity_continuation_data(self, session_id: str) -> Dict[str, Any]:
        """
        Get continuation data for a specific session to restore activity state.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary containing continuation data
        """
        if not self.is_available():
            return {}

        try:
            # Get session info
            session_result = self.client.table('agent_sessions').select('*').eq('id', session_id).execute()

            if not session_result.data:
                return {}

            session = session_result.data[0]

            # Get the latest activity for continuation context
            latest_activity_result = self.client.table('user_activities').select(
                'id, agent_type, activity_type, input_data, output_data, metadata, created_at'
            ).eq('session_id', session_id).order('created_at', desc=True).limit(1).execute()

            continuation_data = {
                'session_id': session_id,
                'agent_type': session['agent_type'],
                'session_name': session['session_name'],
                'can_continue': True,
                'continuation_url': self._generate_continuation_url(session['agent_type'], session_id),
                'last_activity': None
            }

            if latest_activity_result.data:
                latest_activity = latest_activity_result.data[0]
                continuation_data['last_activity'] = {
                    'id': latest_activity['id'],
                    'activity_type': latest_activity['activity_type'],
                    'input_data': latest_activity['input_data'],
                    'output_data': latest_activity['output_data'],
                    'metadata': latest_activity.get('metadata', {}),
                    'created_at': latest_activity['created_at']
                }

            return continuation_data

        except Exception as e:
            logger.error(f"Failed to get activity continuation data: {e}")
            return {}

    def _generate_continuation_url(self, agent_type: str, session_id: str) -> str:
        """Generate continuation URL for different agent types."""
        base_urls = {
            'autowave_chat': f'/autowave-chat?session_id={session_id}',
            'prime_agent': f'/prime-agent-tools?session_id={session_id}',
            'agentic_code': f'/agentic-code?session_id={session_id}',
            'research_lab': f'/research-lab?session_id={session_id}',
            'agent_wave': f'/agent-wave?session_id={session_id}',
            'context7_tools': f'/prime-agent-tools?session_id={session_id}'
        }

        return base_urls.get(agent_type, f'/?session_id={session_id}')

    def _get_agent_display_name(self, agent_type: str) -> str:
        """Get user-friendly display name for agent types."""
        display_names = {
            'autowave_chat': 'AutoWave Chat',
            'prime_agent': 'Prime Agent',
            'agentic_code': 'Agent Alpha',
            'research_lab': 'Research Lab',
            'agent_wave': 'Super Agent',
            'context7_tools': 'Prime Agent Tools'
        }

        return display_names.get(agent_type, agent_type.replace('_', ' ').title())

# Global enhanced history service instance
enhanced_history_service = EnhancedHistoryService()
