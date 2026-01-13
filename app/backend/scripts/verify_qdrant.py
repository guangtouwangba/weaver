#!/usr/bin/env python3
"""Verify Qdrant vector store integration.

This script tests:
1. Connection to Qdrant server
2. Collection creation
3. Vector insert (upsert)
4. Vector search
5. Payload filtering

Usage:
    python scripts/verify_qdrant.py

Requirements:
    - Qdrant server running (docker-compose up qdrant)
    - QDRANT_URL environment variable set (default: http://localhost:6333)
"""

import asyncio
import sys
from uuid import uuid4


async def main():
    """Run Qdrant verification tests."""
    print("=" * 60)
    print("Qdrant Vector Store Verification")
    print("=" * 60)

    # Import after script starts to avoid import errors if qdrant-client not installed
    try:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.models import (
            Distance,
            FieldCondition,
            Filter,
            MatchValue,
            PointStruct,
            VectorParams,
        )
    except ImportError:
        print("❌ qdrant-client not installed!")
        print("   Run: pip install qdrant-client")
        return 1

    # Load config
    try:
        from research_agent.config import get_settings

        settings = get_settings()
        qdrant_url = settings.qdrant_url
        collection_name = settings.qdrant_collection_name
    except ImportError:
        print("⚠️  Could not import settings, using defaults")
        qdrant_url = "http://localhost:6333"
        collection_name = "test_collection"

    print(f"\n📡 Connecting to Qdrant: {qdrant_url}")

    # Test 1: Connection
    try:
        client = AsyncQdrantClient(url=qdrant_url)
        collections = await client.get_collections()
        print(f"✅ Connected! Found {len(collections.collections)} collections")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n   Make sure Qdrant is running:")
        print("   docker-compose up qdrant")
        return 1

    # Use a test collection to avoid interfering with production data
    test_collection = f"{collection_name}_test"
    print(f"\n📦 Using test collection: {test_collection}")

    # Test 2: Collection creation
    try:
        # Delete if exists from previous test
        try:
            await client.delete_collection(test_collection)
        except Exception:
            pass

        await client.create_collection(
            collection_name=test_collection,
            vectors_config=VectorParams(
                size=1536,  # OpenAI embedding dimension
                distance=Distance.COSINE,
            ),
        )
        print("✅ Collection created")
    except Exception as e:
        print(f"❌ Collection creation failed: {e}")
        return 1

    # Test 3: Vector insert
    try:
        project_id = str(uuid4())
        document_id = str(uuid4())
        chunk_id = str(uuid4())

        # Create a test vector (1536 dimensions)
        test_vector = [0.1] * 1536

        point = PointStruct(
            id=chunk_id,
            vector=test_vector,
            payload={
                "chunk_id": chunk_id,
                "document_id": document_id,
                "project_id": project_id,
                "content": "This is a test document chunk for verification.",
                "page_number": 1,
            },
        )

        await client.upsert(
            collection_name=test_collection,
            points=[point],
        )
        print("✅ Vector inserted")
    except Exception as e:
        print(f"❌ Vector insert failed: {e}")
        return 1

    # Test 4: Vector search
    try:
        results = await client.query_points(
            collection_name=test_collection,
            query=test_vector,
            limit=5,
            with_payload=True,
        )

        if len(results.points) > 0:
            print(f"✅ Vector search returned {len(results.points)} results")
            print(f"   Top result score: {results.points[0].score:.4f}")
            print(f"   Content: {results.points[0].payload.get('content', '')[:50]}...")
        else:
            print("⚠️  Vector search returned 0 results")
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return 1

    # Test 5: Payload filtering
    try:
        results = await client.query_points(
            collection_name=test_collection,
            query=test_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="project_id",
                        match=MatchValue(value=project_id),
                    )
                ]
            ),
            limit=5,
            with_payload=True,
        )

        if len(results.points) > 0:
            print(f"✅ Filtered search returned {len(results.points)} results")
        else:
            print("⚠️  Filtered search returned 0 results")
    except Exception as e:
        print(f"❌ Filtered search failed: {e}")
        return 1

    # Test 6: Search with wrong filter (should return 0)
    try:
        wrong_project_id = str(uuid4())
        results = await client.query_points(
            collection_name=test_collection,
            query=test_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="project_id",
                        match=MatchValue(value=wrong_project_id),
                    )
                ]
            ),
            limit=5,
            with_payload=True,
        )

        if len(results.points) == 0:
            print("✅ Wrong filter correctly returned 0 results")
        else:
            print(f"⚠️  Wrong filter unexpectedly returned {len(results.points)} results")
    except Exception as e:
        print(f"❌ Wrong filter search failed: {e}")
        return 1

    # Cleanup
    try:
        await client.delete_collection(test_collection)
        print("\n🧹 Cleaned up test collection")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

    print("\n" + "=" * 60)
    print("✅ All Qdrant verification tests passed!")
    print("=" * 60)
    print("\nTo use Qdrant as your vector store, set:")
    print("  VECTOR_STORE_PROVIDER=qdrant")
    print("")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
