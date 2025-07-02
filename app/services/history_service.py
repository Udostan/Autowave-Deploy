"""
AutoWave History Service
Comprehensive service for retrieving user activity history from Supabase across all agents.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase not available. History features will be disabled.")

logger = logging.getLogger(__name__)

class HistoryService:
    """
    Service for retrieving comprehensive user activity history from Supabase.
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
                logger.warning("Supabase credentials not found. History service disabled.")
                return
            
            self.client = create_client(supabase_url, supabase_key)
            logger.info("History service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize history service: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if history service is available."""
        return SUPABASE_AVAILABLE and self.client is not None
    
    def get_user_activities(self, user_id: str, limit: int = 20, agent_type: str = None) -> List[Dict[str, Any]]:
        """
        Get user activities from Supabase (optimized for speed).

        Args:
            user_id: User identifier
            limit: Maximum number of activities to return (reduced default for speed)
            agent_type: Filter by specific agent type (optional)

        Returns:
            List of user activities
        """
        if not self.is_available():
            return []

        try:
            # Optimized query with only essential fields for faster loading
            query = self.client.table('user_activities').select(
                'id, agent_type, activity_type, input_data, success, created_at, processing_time_ms'
            ).eq('user_id', user_id)

            if agent_type:
                query = query.eq('agent_type', agent_type)

            result = query.order('created_at', desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Failed to get user activities: {e}")
            return []
    
    def get_chat_conversations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get chat conversations for a user."""
        if not self.is_available():
            return []
        
        try:
            result = self.client.table('chat_conversations').select(
                'id, message, response, model_used, tokens_used, created_at'
            ).eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get chat conversations: {e}")
            return []
    
    def get_prime_agent_tasks(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get Prime Agent tasks for a user."""
        if not self.is_available():
            return []
        
        try:
            result = self.client.table('prime_agent_tasks').select(
                'id, task_description, task_status, use_visual_browser, '
                'final_result, execution_time_ms, created_at, completed_at'
            ).eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get Prime Agent tasks: {e}")
            return []
    
    def get_code_projects(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get Agentic Code projects for a user."""
        if not self.is_available():
            return []
        
        try:
            result = self.client.table('code_projects').select(
                'id, project_name, description, programming_language, '
                'framework, generated_files, execution_status, created_at'
            ).eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get code projects: {e}")
            return []
    
    def get_research_queries(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get Research Lab queries for a user."""
        if not self.is_available():
            return []
        
        try:
            result = self.client.table('research_queries').select(
                'id, query, research_questions, findings, final_report, '
                'sources_count, research_depth, created_at'
            ).eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get research queries: {e}")
            return []
    
    def get_context7_usage(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get Prime Agent Tools usage for a user."""
        if not self.is_available():
            return []

        try:
            result = self.client.table('context7_usage').select(
                'id, tool_name, tool_category, request_details, result_data, '
                'screenshots, success, created_at'
            ).eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Failed to get Prime Agent Tools usage: {e}")
            return []
    
    def get_file_uploads(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get file uploads for a user."""
        if not self.is_available():
            return []
        
        try:
            result = self.client.table('file_uploads').select(
                'id, filename, file_type, file_size, mime_type, '
                'analysis_result, created_at'
            ).eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get file uploads: {e}")
            return []
    
    def get_usage_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage analytics for a user over the specified number of days."""
        if not self.is_available():
            return {}
        
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            result = self.client.table('usage_analytics').select(
                'date, agent_type, activity_count, total_processing_time_ms, '
                'files_uploaded, tokens_used'
            ).eq('user_id', user_id).gte('date', start_date.isoformat()).lte('date', end_date.isoformat()).execute()
            
            if not result.data:
                return {}
            
            # Process analytics data
            analytics = {
                'total_activities': 0,
                'total_processing_time': 0,
                'total_files_uploaded': 0,
                'total_tokens_used': 0,
                'agent_breakdown': {},
                'daily_activity': {}
            }
            
            for record in result.data:
                agent_type = record['agent_type']
                date = record['date']
                
                # Update totals
                analytics['total_activities'] += record['activity_count']
                analytics['total_processing_time'] += record['total_processing_time_ms']
                analytics['total_files_uploaded'] += record['files_uploaded']
                analytics['total_tokens_used'] += record['tokens_used']
                
                # Update agent breakdown
                if agent_type not in analytics['agent_breakdown']:
                    analytics['agent_breakdown'][agent_type] = {
                        'activities': 0,
                        'processing_time': 0,
                        'files_uploaded': 0,
                        'tokens_used': 0
                    }
                
                analytics['agent_breakdown'][agent_type]['activities'] += record['activity_count']
                analytics['agent_breakdown'][agent_type]['processing_time'] += record['total_processing_time_ms']
                analytics['agent_breakdown'][agent_type]['files_uploaded'] += record['files_uploaded']
                analytics['agent_breakdown'][agent_type]['tokens_used'] += record['tokens_used']
                
                # Update daily activity
                if date not in analytics['daily_activity']:
                    analytics['daily_activity'][date] = 0
                analytics['daily_activity'][date] += record['activity_count']
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get usage analytics: {e}")
            return {}
    
    def get_comprehensive_history(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive history for a user across all agents (optimized for speed).

        Returns:
            Dictionary containing all user history data
        """
        if not self.is_available():
            return {
                'available': False,
                'message': 'History service not available. Check Supabase configuration.'
            }

        try:
            # Load only essential data for faster initial page load
            # Other tabs can load data on-demand via AJAX
            return {
                'available': True,
                'activities': self.get_user_activities(user_id, limit=15),  # Reduced for speed
                'chat_conversations': self.get_chat_conversations(user_id, limit=10),  # Reduced
                'prime_agent_tasks': [],  # Load on-demand
                'code_projects': [],  # Load on-demand
                'research_queries': [],  # Load on-demand
                'context7_usage': [],  # Load on-demand
                'file_uploads': [],  # Load on-demand
                'analytics': self.get_usage_analytics(user_id, days=7)  # Reduced timeframe
            }

        except Exception as e:
            logger.error(f"Failed to get comprehensive history: {e}")
            return {
                'available': False,
                'error': str(e)
            }

# Global history service instance
history_service = HistoryService()
