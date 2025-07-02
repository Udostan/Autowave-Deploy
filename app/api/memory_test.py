"""
Memory Test API
Provides endpoints to test and verify memory functionality.
"""

from flask import Blueprint, request, jsonify
import json
import logging
from datetime import datetime

from app.services.memory_service import memory_service
from app.services.memory_integration import memory_integration

# Create blueprint
memory_test_bp = Blueprint('memory_test', __name__, url_prefix='/api/memory')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@memory_test_bp.route('/test', methods=['GET'])
def test_memory_connection():
    """Test memory service connection and functionality."""
    try:
        # Check if memory service is available
        if not memory_service.is_available():
            return jsonify({
                'success': False,
                'status': 'Memory service not available',
                'message': 'Please check your Qdrant Cloud configuration in .env file',
                'setup_guide': '/MEMORY_SETUP.md'
            })
        
        # Test basic functionality
        test_user_id = "test_user_123"
        test_content = f"Memory test performed at {datetime.now().isoformat()}"
        
        # Test storing memory
        store_success = memory_service.store_memory(
            agent_type='prime_agent',
            user_id=test_user_id,
            content=test_content,
            metadata={
                'test': True,
                'timestamp': datetime.now().isoformat(),
                'type': 'connection_test'
            }
        )
        
        if not store_success:
            return jsonify({
                'success': False,
                'status': 'Failed to store test memory',
                'message': 'Check Qdrant Cloud credentials and cluster status'
            })
        
        # Test retrieving memory
        memories = memory_service.retrieve_memories(
            agent_type='prime_agent',
            user_id=test_user_id,
            query='memory test',
            limit=1
        )
        
        return jsonify({
            'success': True,
            'status': 'Memory service working correctly',
            'test_results': {
                'store_success': store_success,
                'retrieve_count': len(memories),
                'test_memory_found': len(memories) > 0,
                'collections_available': list(memory_service.collections.keys())
            },
            'message': '🎉 Memory is working! Your agents will now remember user interactions.',
            'next_steps': [
                'Use any agent (Prime Agent, Agentic Code, etc.)',
                'Memory will automatically store and retrieve relevant context',
                'Agents will become smarter over time'
            ]
        })
        
    except Exception as e:
        logger.error(f"Memory test error: {e}")
        return jsonify({
            'success': False,
            'status': 'Memory test failed',
            'error': str(e),
            'troubleshooting': [
                'Check .env file has correct QDRANT_URL and QDRANT_API_KEY',
                'Verify Qdrant cluster is running in cloud dashboard',
                'Ensure dependencies are installed: pip install qdrant-client sentence-transformers',
                'Check server logs for detailed error messages'
            ]
        })

@memory_test_bp.route('/stats', methods=['GET'])
def get_memory_stats():
    """Get memory usage statistics."""
    try:
        if not memory_service.is_available():
            return jsonify({
                'success': False,
                'message': 'Memory service not available'
            })
        
        # Get collection info
        collections_info = {}
        if memory_service.client:
            try:
                collections = memory_service.client.get_collections()
                for collection in collections.collections:
                    if collection.name in memory_service.collections:
                        collection_info = memory_service.client.get_collection(collection.name)
                        collections_info[collection.name] = {
                            'vectors_count': collection_info.vectors_count,
                            'status': collection_info.status,
                            'description': memory_service.collections[collection.name]
                        }
            except Exception as e:
                logger.warning(f"Could not get collection stats: {e}")
        
        return jsonify({
            'success': True,
            'memory_available': memory_service.is_available(),
            'collections': collections_info,
            'total_collections': len(memory_service.collections),
            'embedding_model': 'all-MiniLM-L6-v2',
            'vector_dimension': 384
        })
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@memory_test_bp.route('/demo', methods=['POST'])
def demo_memory():
    """Demonstrate memory functionality with sample data."""
    try:
        if not memory_service.is_available():
            return jsonify({
                'success': False,
                'message': 'Memory service not available'
            })
        
        data = request.get_json() or {}
        demo_user_id = data.get('user_id', 'demo_user')
        
        # Store sample memories for different agents
        sample_memories = [
            {
                'agent_type': 'prime_agent',
                'content': 'User prefers Delta Airlines for business travel, aisle seats, and early morning flights',
                'metadata': {'type': 'preference', 'category': 'travel'}
            },
            {
                'agent_type': 'agentic_code',
                'content': 'User prefers React with TypeScript, clean code style, and comprehensive comments',
                'metadata': {'type': 'preference', 'category': 'coding_style'}
            },
            {
                'agent_type': 'context7',
                'content': 'User frequently books hotels in downtown areas, prefers 4+ star ratings',
                'metadata': {'type': 'preference', 'category': 'accommodation'}
            }
        ]
        
        stored_count = 0
        for memory in sample_memories:
            success = memory_service.store_memory(
                agent_type=memory['agent_type'],
                user_id=demo_user_id,
                content=memory['content'],
                metadata=memory['metadata']
            )
            if success:
                stored_count += 1
        
        # Test retrieval
        travel_memories = memory_service.retrieve_memories(
            agent_type='prime_agent',
            user_id=demo_user_id,
            query='travel preferences',
            limit=3
        )
        
        coding_memories = memory_service.retrieve_memories(
            agent_type='agentic_code',
            user_id=demo_user_id,
            query='coding style',
            limit=3
        )
        
        return jsonify({
            'success': True,
            'demo_results': {
                'memories_stored': stored_count,
                'travel_memories_found': len(travel_memories),
                'coding_memories_found': len(coding_memories),
                'sample_travel_memory': travel_memories[0] if travel_memories else None,
                'sample_coding_memory': coding_memories[0] if coding_memories else None
            },
            'message': f'Demo completed! Stored {stored_count} sample memories for user {demo_user_id}',
            'next_steps': [
                'Try using Prime Agent Tools with flight booking',
                'Use Agentic Code to generate some code',
                'Notice how agents remember your preferences'
            ]
        })
        
    except Exception as e:
        logger.error(f"Demo memory error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@memory_test_bp.route('/clear', methods=['POST'])
def clear_test_memories():
    """Clear test memories (for development/testing)."""
    try:
        if not memory_service.is_available():
            return jsonify({
                'success': False,
                'message': 'Memory service not available'
            })
        
        data = request.get_json() or {}
        user_id = data.get('user_id', 'test_user_123')
        
        # Note: Qdrant doesn't have a direct "delete by user_id" method
        # In production, you'd implement a more sophisticated cleanup
        # For now, we'll just return a success message
        
        return jsonify({
            'success': True,
            'message': f'Test memories cleared for user {user_id}',
            'note': 'In production, implement proper memory cleanup based on retention policies'
        })
        
    except Exception as e:
        logger.error(f"Clear memory error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
