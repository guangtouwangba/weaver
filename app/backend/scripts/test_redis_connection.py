#!/usr/bin/env python
"""
Test script for Redis connection and ARQ configuration.

Usage:
    cd app/backend
    python scripts/test_redis_connection.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_redis_connection():
    """Test Redis connection."""
    from research_agent.config import get_settings
    from research_agent.worker.arq_config import get_redis_settings, get_redis_pool
    
    settings = get_settings()
    
    print("=" * 60)
    print("Redis Connection Test")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print(f"Redis URL: {settings.redis_url[:30] if settings.redis_url else 'NOT SET'}...")
    print()
    
    if not settings.redis_url:
        print("❌ REDIS_URL is not set!")
        print("   Set REDIS_URL in .env file:")
        print("   REDIS_URL=redis://default:xxx@xxx.upstash.io:6379")
        return False
    
    # Test Redis settings parsing
    redis_settings = get_redis_settings()
    print(f"Parsed Redis Settings:")
    print(f"  Host: {redis_settings.host}")
    print(f"  Port: {redis_settings.port}")
    print(f"  SSL: {redis_settings.ssl}")
    print()
    
    # Test Redis connection
    print("Testing Redis connection...")
    try:
        pool = await get_redis_pool()
        # Test basic operations
        test_key = f"test:arq:{settings.environment}"
        await pool.redis.set(test_key, "hello", ex=10)
        value = await pool.redis.get(test_key)
        await pool.redis.delete(test_key)
        await pool.close()
        
        if value == b"hello":
            print("✅ Redis connection successful!")
            print(f"   Set and retrieved test value: {value}")
            return True
        else:
            print(f"❌ Redis test failed: unexpected value {value}")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


async def test_task_enqueue():
    """Test task enqueueing (without actually processing)."""
    from research_agent.config import get_settings
    from research_agent.worker.arq_config import get_redis_pool
    
    settings = get_settings()
    
    if not settings.redis_url:
        print("\n⚠️  Skipping enqueue test (no Redis URL)")
        return
    
    print()
    print("=" * 60)
    print("Task Enqueue Test")
    print("=" * 60)
    
    try:
        pool = await get_redis_pool()
        
        # Enqueue a test job
        job = await pool.enqueue_job(
            "process_document",
            {"document_id": "test-123", "project_id": "test-456", "file_path": "test.pdf"},
            _queue_name=f"arq:queue:{settings.environment}",
            _defer_by=3600,  # Defer by 1 hour so it won't be processed
        )
        
        if job:
            print(f"✅ Test job enqueued successfully!")
            print(f"   Job ID: {job.job_id}")
            
            # Get job info
            info = await job.info()
            print(f"   Job function: {info.function if info else 'unknown'}")
            print(f"   Job status: {await job.status()}")
            
            # Abort the test job
            await job.abort()
            print(f"   Job aborted (was just a test)")
        else:
            print("⚠️  Job may already exist with same ID")
            
        await pool.close()
        
    except Exception as e:
        print(f"❌ Enqueue test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    success = await test_redis_connection()
    
    if success:
        await test_task_enqueue()
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    if success:
        print("✅ Redis configuration is working!")
        print()
        print("Next steps:")
        print("  1. Start the API server: ./start.sh --api")
        print("  2. Start the worker: ./start.sh --worker")
        print("  3. Or start both: ./start.sh")
    else:
        print("❌ Redis configuration needs attention")
        print()
        print("To fix:")
        print("  1. Create a free Redis instance at https://upstash.com/")
        print("  2. Add REDIS_URL to your .env file")


if __name__ == "__main__":
    asyncio.run(main())





