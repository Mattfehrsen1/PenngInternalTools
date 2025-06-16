#!/usr/bin/env python3
"""Minimal test to isolate the ingestion issue"""

import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Persona, IngestionJob
from database import AsyncSessionLocal

async def test_database_operations():
    """Test if database operations work correctly"""
    print("🔍 Testing database operations...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Test basic query
            result = await db.execute(select(Persona).limit(1))
            personas = result.scalars().all()
            print(f"✅ Found {len(personas)} personas in database")
            
            # Test creating an ingestion job
            from models import generate_uuid
            job_id = generate_uuid()
            
            job = IngestionJob(
                id=job_id,
                persona_id="test-persona-id",
                user_id="test-user-id", 
                total_files=2,
                processed_files=0,
                status="QUEUED",
                progress=0,
                job_metadata={"test": True}
            )
            
            db.add(job)
            await db.commit()
            print(f"✅ Created test ingestion job: {job_id}")
            
            # Clean up
            await db.delete(job)
            await db.commit()
            print("✅ Cleaned up test job")
            
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_queue_operations():
    """Test if queue operations work"""
    print("🔍 Testing queue operations...")
    
    try:
        from services.queue_manager import enqueue_job, get_job_status
        from services.ingestion_worker import run_ingestion_job
        
        # Test enqueueing a job
        job_id = enqueue_job(
            run_ingestion_job,
            "test-job-id",
            "test-persona-id",
            [],  # empty files
            queue_name="ingestion"
        )
        
        print(f"✅ Enqueued test job: {job_id}")
        
        # Check status
        status = get_job_status(job_id, "ingestion")
        print(f"✅ Job status: {status.get('status', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Queue test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🧪 Running minimal ingestion tests...")
    
    db_ok = await test_database_operations()
    queue_ok = await test_queue_operations()
    
    if db_ok and queue_ok:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    asyncio.run(main()) 