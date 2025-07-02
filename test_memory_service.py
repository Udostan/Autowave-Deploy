#!/usr/bin/env python3
"""
Test memory service directly.
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Add the app directory to the path
sys.path.append('.')

print("=== Memory Service Test ===")

try:
    from app.services.memory_service import memory_service
    print("✅ Memory service imported successfully")
    
    print(f"Memory available: {memory_service.is_available()}")
    print(f"Client: {memory_service.client}")
    print(f"Encoder: {memory_service.encoder}")
    
    if memory_service.is_available():
        print("✅ Memory service is fully functional!")
        
        # Test storing a memory
        success = memory_service.store_memory(
            agent_type='prime_agent',
            user_id='test_user',
            content='Test memory content for verification',
            metadata={'test': True}
        )
        print(f"Store test: {'✅ Success' if success else '❌ Failed'}")
        
        # Test retrieving memories
        memories = memory_service.retrieve_memories(
            agent_type='prime_agent',
            user_id='test_user',
            query='test memory',
            limit=1
        )
        print(f"Retrieve test: {'✅ Success' if len(memories) > 0 else '❌ No memories found'}")
        
    else:
        print("❌ Memory service not available")
        print("Checking individual components...")
        
        # Test imports directly
        try:
            from qdrant_client import QdrantClient
            print("✅ QdrantClient import works")
        except ImportError as e:
            print(f"❌ QdrantClient import failed: {e}")
        
        try:
            from sentence_transformers import SentenceTransformer
            print("✅ SentenceTransformer import works")
        except ImportError as e:
            print(f"❌ SentenceTransformer import failed: {e}")
        
        # Check environment variables
        qdrant_url = os.getenv('QDRANT_URL')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        print(f"QDRANT_URL: {qdrant_url}")
        print(f"QDRANT_API_KEY: {'***' + qdrant_api_key[-10:] if qdrant_api_key else 'Not set'}")

except Exception as e:
    print(f"❌ Error testing memory service: {e}")
    import traceback
    traceback.print_exc()
