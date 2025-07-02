#!/usr/bin/env python3
"""
Simple memory test script to debug Qdrant connection issues.
"""

import os
import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print("=== AutoWave Memory Test ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Test 1: Check environment variables
print("\n1. Environment Variables:")
qdrant_url = os.getenv('QDRANT_URL')
qdrant_api_key = os.getenv('QDRANT_API_KEY')
print(f"QDRANT_URL: {qdrant_url}")
print(f"QDRANT_API_KEY: {'***' + qdrant_api_key[-10:] if qdrant_api_key else 'Not set'}")

# Test 2: Check imports
print("\n2. Import Tests:")
try:
    import qdrant_client
    print("✅ qdrant_client imported successfully")
except ImportError as e:
    print(f"❌ qdrant_client import failed: {e}")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence_transformers imported successfully")
except ImportError as e:
    print(f"❌ sentence_transformers import failed: {e}")
    sys.exit(1)

# Test 3: Test Qdrant connection
print("\n3. Qdrant Connection Test:")
if not qdrant_url or not qdrant_api_key:
    print("❌ Missing Qdrant credentials")
    sys.exit(1)

try:
    from qdrant_client import QdrantClient
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    # Test connection
    collections = client.get_collections()
    print(f"✅ Connected to Qdrant Cloud successfully")
    print(f"Existing collections: {[col.name for col in collections.collections]}")

except Exception as e:
    print(f"❌ Qdrant connection failed: {e}")
    sys.exit(1)

# Test 4: Test sentence transformer
print("\n4. Sentence Transformer Test:")
try:
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    test_embedding = encoder.encode("test sentence")
    print(f"✅ Sentence transformer working (embedding size: {len(test_embedding)})")
except Exception as e:
    print(f"❌ Sentence transformer failed: {e}")
    sys.exit(1)

print("\n🎉 All memory tests passed! Memory system is ready.")
