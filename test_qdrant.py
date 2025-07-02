#!/usr/bin/env python3
"""
Simple Qdrant connection test.
"""

import os
from dotenv import load_dotenv
load_dotenv()

print("=== Qdrant Connection Test ===")

# Check environment variables
qdrant_url = os.getenv('QDRANT_URL')
qdrant_api_key = os.getenv('QDRANT_API_KEY')
print(f"QDRANT_URL: {qdrant_url}")
print(f"QDRANT_API_KEY: {'***' + qdrant_api_key[-10:] if qdrant_api_key else 'Not set'}")

if not qdrant_url or not qdrant_api_key:
    print("❌ Missing Qdrant credentials")
    exit(1)

try:
    from qdrant_client import QdrantClient
    print("✅ qdrant_client imported successfully")
    
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    print("✅ Qdrant client created")
    
    # Test connection
    collections = client.get_collections()
    print(f"✅ Connected to Qdrant Cloud successfully!")
    print(f"Existing collections: {[col.name for col in collections.collections]}")
    
except Exception as e:
    print(f"❌ Qdrant connection failed: {e}")
    exit(1)

print("\n🎉 Qdrant connection test passed!")
