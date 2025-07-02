"""
Memory Integration for AutoWave Agents
Provides memory-enhanced functionality for all agents.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .memory_service import memory_service

class MemoryIntegration:
    """
    Integration layer for adding memory capabilities to agents.
    """
    
    @staticmethod
    def get_user_id(request) -> str:
        """
        Extract or generate user ID from request.
        For now, using session-based identification with fallback.
        """
        try:
            # Try to get user ID from session (authenticated users)
            if hasattr(request, 'session') and request.session:
                session_id = request.session.get('user_id')
                if session_id:
                    return session_id

                # Generate new session ID for authenticated but new users
                import uuid
                session_id = str(uuid.uuid4())
                request.session['user_id'] = session_id
                return session_id

            # Fallback for non-authenticated requests (testing, etc.)
            import uuid
            return f"anonymous_{str(uuid.uuid4())[:8]}"

        except Exception as e:
            # Ultimate fallback
            import uuid
            return f"fallback_{str(uuid.uuid4())[:8]}"
    
    @staticmethod
    def enhance_prime_agent_task(user_id: str, task: str) -> Dict[str, Any]:
        """
        Enhance Prime Agent task with memory context.
        
        Args:
            user_id: User identifier
            task: Task description
            
        Returns:
            Enhanced context with memory insights
        """
        if not memory_service.is_available():
            return {'memory_available': False, 'context': ''}
        
        try:
            # Retrieve relevant memories
            memories = memory_service.retrieve_memories(
                agent_type='prime_agent',
                user_id=user_id,
                query=task,
                limit=3
            )
            
            # Get user preferences
            preferences = memory_service.get_user_preferences(user_id, 'prime_agent')
            
            # Build context
            context_parts = []
            
            if preferences:
                context_parts.append("User Preferences:")
                for key, value in preferences.items():
                    context_parts.append(f"- {key}: {value}")
                context_parts.append("")
            
            if memories:
                context_parts.append("Relevant Past Interactions:")
                for i, memory in enumerate(memories, 1):
                    context_parts.append(f"{i}. {memory['content'][:200]}...")
                    if memory['metadata'].get('outcome'):
                        context_parts.append(f"   Outcome: {memory['metadata']['outcome']}")
                context_parts.append("")
            
            return {
                'memory_available': True,
                'context': '\n'.join(context_parts),
                'memories_count': len(memories),
                'preferences_count': len(preferences)
            }
            
        except Exception as e:
            logging.error(f"Error enhancing Prime Agent task: {e}")
            return {'memory_available': False, 'context': ''}
    
    @staticmethod
    def store_prime_agent_result(user_id: str, task: str, result: str, metadata: Dict[str, Any] = None):
        """
        Store Prime Agent task result in memory.
        """
        if not memory_service.is_available():
            return
        
        try:
            content = f"Task: {task}\nResult: {result}"
            
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'type': 'task_execution',
                'task': task,
                'result_preview': result[:200] + '...' if len(result) > 200 else result,
                'success': metadata.get('success', True)
            })
            
            memory_service.store_memory(
                agent_type='prime_agent',
                user_id=user_id,
                content=content,
                metadata=metadata
            )
            
        except Exception as e:
            logging.error(f"Error storing Prime Agent result: {e}")
    
    @staticmethod
    def enhance_agentic_code_request(user_id: str, prompt: str) -> Dict[str, Any]:
        """
        Enhance Agentic Code request with coding patterns and preferences.
        """
        if not memory_service.is_available():
            return {'memory_available': False, 'context': ''}
        
        try:
            # Retrieve coding memories
            memories = memory_service.retrieve_memories(
                agent_type='agentic_code',
                user_id=user_id,
                query=prompt,
                limit=3
            )
            
            # Get coding preferences
            preferences = memory_service.get_user_preferences(user_id, 'agentic_code')
            
            context_parts = []
            
            if preferences:
                context_parts.append("Coding Preferences:")
                for key, value in preferences.items():
                    context_parts.append(f"- {key}: {value}")
                context_parts.append("")
            
            if memories:
                context_parts.append("Similar Past Projects:")
                for i, memory in enumerate(memories, 1):
                    context_parts.append(f"{i}. {memory['content'][:150]}...")
                context_parts.append("")
            
            return {
                'memory_available': True,
                'context': '\n'.join(context_parts),
                'memories_count': len(memories)
            }
            
        except Exception as e:
            logging.error(f"Error enhancing Agentic Code request: {e}")
            return {'memory_available': False, 'context': ''}
    
    @staticmethod
    def store_agentic_code_result(user_id: str, prompt: str, code: str, language: str):
        """
        Store Agentic Code generation result in memory.
        """
        if not memory_service.is_available():
            return
        
        try:
            content = f"Prompt: {prompt}\nLanguage: {language}\nCode: {code[:500]}..."
            
            metadata = {
                'type': 'code_generation',
                'language': language,
                'prompt': prompt,
                'code_length': len(code)
            }
            
            memory_service.store_memory(
                agent_type='agentic_code',
                user_id=user_id,
                content=content,
                metadata=metadata
            )
            
        except Exception as e:
            logging.error(f"Error storing Agentic Code result: {e}")
    
    @staticmethod
    def enhance_context7_tool_request(user_id: str, tool_name: str, request: str) -> Dict[str, Any]:
        """
        Enhance Context7 tool request with usage patterns and preferences.
        """
        if not memory_service.is_available():
            return {'memory_available': False, 'context': ''}
        
        try:
            # Retrieve tool-specific memories
            memories = memory_service.retrieve_memories(
                agent_type='context7',
                user_id=user_id,
                query=f"{tool_name} {request}",
                limit=3
            )
            
            # Get tool preferences
            preferences = memory_service.get_user_preferences(user_id, 'context7')
            
            context_parts = []
            
            # Filter preferences for this tool
            tool_preferences = {k: v for k, v in preferences.items() if tool_name.lower() in k.lower()}
            
            if tool_preferences:
                context_parts.append(f"{tool_name} Preferences:")
                for key, value in tool_preferences.items():
                    context_parts.append(f"- {key}: {value}")
                context_parts.append("")
            
            if memories:
                context_parts.append(f"Previous {tool_name} Usage:")
                for i, memory in enumerate(memories, 1):
                    context_parts.append(f"{i}. {memory['content'][:150]}...")
                context_parts.append("")
            
            return {
                'memory_available': True,
                'context': '\n'.join(context_parts),
                'memories_count': len(memories),
                'tool_preferences': tool_preferences
            }
            
        except Exception as e:
            logging.error(f"Error enhancing Context7 tool request: {e}")
            return {'memory_available': False, 'context': ''}
    
    @staticmethod
    def store_context7_tool_result(user_id: str, tool_name: str, request: str, result: str, preferences: Dict[str, Any] = None):
        """
        Store Context7 tool usage result and learn preferences.
        """
        if not memory_service.is_available():
            return
        
        try:
            content = f"Tool: {tool_name}\nRequest: {request}\nResult: {result[:300]}..."
            
            metadata = {
                'type': 'tool_usage',
                'tool_name': tool_name,
                'request': request,
                'result_preview': result[:200] + '...' if len(result) > 200 else result
            }
            
            memory_service.store_memory(
                agent_type='context7',
                user_id=user_id,
                content=content,
                metadata=metadata
            )
            
            # Store preferences if provided
            if preferences:
                for key, value in preferences.items():
                    preference_content = f"User prefers {key}: {value} for {tool_name}"
                    preference_metadata = {
                        'type': 'preference',
                        'tool_name': tool_name,
                        'preference_key': f"{tool_name}_{key}",
                        'preference_value': value
                    }
                    
                    memory_service.store_memory(
                        agent_type='context7',
                        user_id=user_id,
                        content=preference_content,
                        metadata=preference_metadata
                    )
            
        except Exception as e:
            logging.error(f"Error storing Context7 tool result: {e}")


# Global memory integration instance
memory_integration = MemoryIntegration()
