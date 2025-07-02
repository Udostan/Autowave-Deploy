"""
AutoWave Memory Service using Qdrant Cloud
Provides persistent memory capabilities for all agents in the platform.
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from sentence_transformers import SentenceTransformer
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    logging.warning("Memory dependencies not installed. Memory features will be disabled.")

class MemoryService:
    """
    Centralized memory service for all AutoWave agents.
    Uses Qdrant Cloud for vector storage and retrieval.
    """
    
    def __init__(self):
        self.client = None
        self.encoder = None
        self.collections = {
            'prime_agent_memory': 'Prime Agent task execution and user preferences',
            'agentic_code_memory': 'Code generation patterns and user coding style',
            'agent_wave_memory': 'Design preferences and campaign history',
            'context7_memory': 'Tool usage patterns and booking preferences',
            'global_user_memory': 'Cross-agent user profile and preferences'
        }
        
        if MEMORY_AVAILABLE:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Qdrant client and embedding model."""
        try:
            # Get Qdrant Cloud credentials from environment
            qdrant_url = os.getenv('QDRANT_URL')
            qdrant_api_key = os.getenv('QDRANT_API_KEY')
            
            if not qdrant_url or not qdrant_api_key:
                logging.warning("Qdrant credentials not found. Memory features disabled.")
                return
            
            # Initialize Qdrant client
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
            )
            
            # Initialize sentence transformer for embeddings
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create collections if they don't exist
            self._create_collections()
            
            logging.info("Memory service initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize memory service: {e}")
            self.client = None
            self.encoder = None
    
    def _create_collections(self):
        """Create memory collections for each agent."""
        if not self.client:
            return
        
        try:
            existing_collections = [col.name for col in self.client.get_collections().collections]
            
            for collection_name, description in self.collections.items():
                if collection_name not in existing_collections:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=384,  # all-MiniLM-L6-v2 embedding size
                            distance=models.Distance.COSINE
                        )
                    )
                    logging.info(f"Created collection: {collection_name}")
        
        except Exception as e:
            logging.error(f"Failed to create collections: {e}")
    
    def is_available(self) -> bool:
        """Check if memory service is available."""
        return MEMORY_AVAILABLE and self.client is not None and self.encoder is not None
    
    def store_memory(self, 
                    agent_type: str, 
                    user_id: str, 
                    content: str, 
                    metadata: Dict[str, Any] = None) -> bool:
        """
        Store a memory entry for an agent.
        
        Args:
            agent_type: Type of agent (prime_agent, agentic_code, agent_wave, context7)
            user_id: User identifier
            content: Text content to store
            metadata: Additional metadata
        
        Returns:
            bool: Success status
        """
        if not self.is_available():
            return False
        
        try:
            collection_name = f"{agent_type}_memory"
            if collection_name not in self.collections:
                logging.error(f"Unknown agent type: {agent_type}")
                return False
            
            # Generate embedding
            embedding = self.encoder.encode(content).tolist()
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'user_id': user_id,
                'agent_type': agent_type,
                'timestamp': datetime.now().isoformat(),
                'content_preview': content[:100] + '...' if len(content) > 100 else content
            })
            
            # Store in Qdrant
            point_id = str(uuid.uuid4())
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            'content': content,
                            **metadata
                        }
                    )
                ]
            )
            
            logging.info(f"Stored memory for {agent_type} user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to store memory: {e}")
            return False
    
    def retrieve_memories(self, 
                         agent_type: str, 
                         user_id: str, 
                         query: str, 
                         limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for an agent and user.
        
        Args:
            agent_type: Type of agent
            user_id: User identifier
            query: Search query
            limit: Maximum number of results
        
        Returns:
            List of memory entries
        """
        if not self.is_available():
            return []
        
        try:
            collection_name = f"{agent_type}_memory"
            if collection_name not in self.collections:
                return []
            
            # Generate query embedding
            query_embedding = self.encoder.encode(query).tolist()
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=limit
            )
            
            # Format results
            memories = []
            for result in search_results:
                memories.append({
                    'content': result.payload.get('content', ''),
                    'metadata': {k: v for k, v in result.payload.items() if k != 'content'},
                    'score': result.score
                })
            
            return memories
            
        except Exception as e:
            logging.error(f"Failed to retrieve memories: {e}")
            return []
    
    def get_user_preferences(self, user_id: str, agent_type: str = None) -> Dict[str, Any]:
        """
        Get user preferences for an agent or globally.
        
        Args:
            user_id: User identifier
            agent_type: Specific agent type or None for global preferences
        
        Returns:
            Dictionary of user preferences
        """
        if not self.is_available():
            return {}
        
        try:
            collection_name = f"{agent_type}_memory" if agent_type else "global_user_memory"
            
            # Search for preference entries
            search_results = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        ),
                        models.FieldCondition(
                            key="type",
                            match=models.MatchValue(value="preference")
                        )
                    ]
                ),
                limit=100
            )
            
            preferences = {}
            for point in search_results[0]:
                if 'preference_key' in point.payload and 'preference_value' in point.payload:
                    preferences[point.payload['preference_key']] = point.payload['preference_value']
            
            return preferences
            
        except Exception as e:
            logging.error(f"Failed to get user preferences: {e}")
            return {}


# Global memory service instance
memory_service = MemoryService()
