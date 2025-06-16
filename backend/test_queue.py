#!/usr/bin/env python3
"""
Test script for Redis Queue system
Verifies that jobs can be enqueued and processed
"""
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_queue_system():
    """Test basic queue functionality"""
    from services.queue_manager import enqueue_job, get_job_status, test_job
    
    logger.info("🧪 Testing Redis Queue System")
    
    # Test 1: Simple job enqueue
    logger.info("Test 1: Enqueuing test job...")
    job_id = enqueue_job(test_job, "Hello from test!")
    logger.info(f"✅ Job enqueued with ID: {job_id}")
    
    # Test 2: Check job status
    logger.info("Test 2: Checking job status...")
    status = get_job_status(job_id)
    logger.info(f"📊 Job status: {status}")
    
    # Test 3: Wait for completion
    logger.info("Test 3: Waiting for job completion...")
    max_wait = 30  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status = get_job_status(job_id)
        logger.info(f"⏱️  Status: {status.get('status', 'unknown')}")
        
        if status.get('status') in ['finished', 'failed']:
            break
        
        time.sleep(2)
    
    final_status = get_job_status(job_id)
    logger.info(f"🏁 Final status: {final_status}")
    
    if final_status.get('status') == 'finished':
        logger.info(f"✅ Job completed successfully!")
        logger.info(f"📝 Result: {final_status.get('result')}")
        return True
    else:
        logger.error(f"❌ Job failed or timed out")
        return False

def test_redis_connection():
    """Test Redis connection"""
    try:
        from services.queue_manager import get_redis_connection
        redis_conn = get_redis_connection()
        
        # Test ping
        if redis_conn.ping():
            logger.info("✅ Redis connection successful")
            return True
        else:
            logger.error("❌ Redis ping failed")
            return False
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting Queue System Tests")
    
    # Test Redis connection first
    if not test_redis_connection():
        logger.error("❌ Cannot proceed without Redis connection")
        exit(1)
    
    # Test queue system
    if test_queue_system():
        logger.info("🎉 All tests passed!")
        exit(0)
    else:
        logger.error("💥 Tests failed!")
        exit(1) 