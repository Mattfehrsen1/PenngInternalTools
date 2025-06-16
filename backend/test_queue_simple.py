#!/usr/bin/env python3
"""Simple queue test"""

import logging
logging.basicConfig(level=logging.INFO)

def simple_test():
    """Test basic queue functionality"""
    try:
        from services.queue_manager import enqueue_job, get_job_status
        
        # Test a simple job
        def test_job(message):
            import time
            time.sleep(2)
            return f"Processed: {message}"
        
        # Enqueue test job
        job_id = enqueue_job(test_job, "test message", queue_name="ingestion")
        print(f"✅ Enqueued job: {job_id}")
        
        # Check status
        status = get_job_status(job_id, "ingestion")
        print(f"✅ Job status: {status}")
        
        return True
    except Exception as e:
        print(f"❌ Queue test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Redis Queue...")
    success = simple_test()
    if success:
        print("✅ Queue test passed!")
    else:
        print("❌ Queue test failed!") 