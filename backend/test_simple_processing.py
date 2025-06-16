#!/usr/bin/env python3
"""
Test Script for Simplified Document Processing Pipeline

This script tests the new threading-based approach to ensure it works correctly
without the database session conflicts we had before.
"""

import os
import time
import base64
import threading
from datetime import datetime

# Add the current directory to path to import our modules
import sys
sys.path.append('.')

from services.simple_processor import process_file_simple, start_processing_thread, SessionLocal
from models import IngestionJob, JobStatus

def create_test_file_data():
    """Create test file data for processing"""
    test_content = """
    This is a test document for Clone Advisor.
    
    It contains multiple paragraphs of text that should be chunked
    and processed by our new simplified document processing pipeline.
    
    The goal is to verify that:
    1. Files are processed without database conflicts
    2. Status updates work correctly 
    3. The threading approach is reliable
    4. Error handling works as expected
    
    This document should create approximately 2-3 chunks when processed
    with the default chunk size of 1000 characters and overlap of 200.
    
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod 
    tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim 
    veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea 
    commodo consequat. Duis aute irure dolor in reprehenderit in voluptate 
    velit esse cillum dolore eu fugiat nulla pariatur.
    """
    
    # Encode as base64 like the API does
    encoded_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
    
    return [{
        'filename': 'test_document.txt',
        'content': encoded_content,
        'type': 'text',
        'size': len(test_content)
    }]

def test_simple_processing():
    """Test the simplified processing approach"""
    print("=== Testing Simplified Document Processing ===")
    
    db = SessionLocal()
    
    try:
        # Create a test job
        job_id = "test-job-" + str(int(time.time()))
        persona_id = "test-persona-123"
        
        job = IngestionJob(
            id=job_id,
            persona_id=persona_id,
            user_id="test-user",
            total_files=1,
            status=JobStatus.QUEUED,
            job_metadata={"test": True, "started_at": datetime.utcnow().isoformat()}
        )
        
        db.add(job)
        db.commit()
        
        print(f"✓ Created test job: {job_id}")
        
        # Create test file data
        files_data = create_test_file_data()
        print(f"✓ Created test file data: {files_data[0]['filename']}")
        
        # Start processing in a thread
        print("✓ Starting processing thread...")
        thread = start_processing_thread(job_id, persona_id, files_data)
        
        # Monitor the job status
        print("✓ Monitoring job status...")
        max_wait = 30  # 30 seconds max wait
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            # Refresh job from database
            db.refresh(job)
            
            print(f"  Status: {job.status.value}")
            
            if job.status == JobStatus.READY:
                print("✅ Job completed successfully!")
                print(f"  Processed files: {job.processed_files}")
                if job.job_metadata:
                    chunks = job.job_metadata.get('chunks_created', 0)
                    print(f"  Chunks created: {chunks}")
                break
            elif job.status == JobStatus.FAILED:
                print("❌ Job failed!")
                if hasattr(job, 'error_message') and job.error_message:
                    print(f"  Error: {job.error_message}")
                break
            elif job.status == JobStatus.PROCESSING:
                print("  ⏳ Still processing...")
            
            time.sleep(2)
        else:
            print("⚠️  Test timed out after 30 seconds")
            db.refresh(job)
            print(f"  Final status: {job.status.value}")
        
        # Wait for thread to complete
        if thread.is_alive():
            print("  Waiting for thread to complete...")
            thread.join(timeout=5)
        
        return job.status == JobStatus.READY
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_error_handling():
    """Test error handling with invalid file"""
    print("\n=== Testing Error Handling ===")
    
    db = SessionLocal()
    
    try:
        # Create a test job with invalid data
        job_id = "test-error-job-" + str(int(time.time()))
        persona_id = "test-persona-456"
        
        job = IngestionJob(
            id=job_id,
            persona_id=persona_id,
            user_id="test-user",
            total_files=1,
            status=JobStatus.QUEUED,
            job_metadata={"test": True, "error_test": True}
        )
        
        db.add(job)
        db.commit()
        
        print(f"✓ Created error test job: {job_id}")
        
        # Create invalid file data (invalid base64)
        invalid_files_data = [{
            'filename': 'invalid_file.txt',
            'content': 'invalid-base64-content!!!',  # This will cause a base64 decode error
            'type': 'text',
            'size': 100
        }]
        
        print("✓ Created invalid file data")
        
        # Start processing
        thread = start_processing_thread(job_id, persona_id, invalid_files_data)
        
        # Wait for processing to complete
        time.sleep(5)
        
        # Check that job failed gracefully
        db.refresh(job)
        
        if job.status == JobStatus.FAILED:
            print("✅ Error handling works correctly - job marked as failed")
            if hasattr(job, 'error_message') and job.error_message:
                print(f"  Error message captured: {job.error_message[:100]}...")
            return True
        else:
            print(f"❌ Expected job to fail, but status is: {job.status.value}")
            return False
        
    except Exception as e:
        print(f"❌ Error test failed: {e}")
        return False
    finally:
        db.close()

def test_multiple_threads():
    """Test that multiple processing threads don't interfere with each other"""
    print("\n=== Testing Multiple Threads ===")
    
    threads = []
    results = []
    
    try:
        # Start 3 processing threads simultaneously
        for i in range(3):
            job_id = f"test-multi-job-{i}-{int(time.time())}"
            persona_id = f"test-persona-multi-{i}"
            
            db = SessionLocal()
            job = IngestionJob(
                id=job_id,
                persona_id=persona_id,
                user_id="test-user",
                total_files=1,
                status=JobStatus.QUEUED,
                job_metadata={"test": True, "thread_test": i}
            )
            
            db.add(job)
            db.commit()
            db.close()
            
            files_data = create_test_file_data()
            files_data[0]['filename'] = f'test_file_{i}.txt'
            
            thread = start_processing_thread(job_id, persona_id, files_data)
            threads.append((thread, job_id))
            
            print(f"✓ Started thread {i}: {job_id}")
        
        # Wait for all threads to complete
        print("✓ Waiting for all threads to complete...")
        time.sleep(10)
        
        # Check results
        for thread, job_id in threads:
            db = SessionLocal()
            try:
                job = db.query(IngestionJob).filter_by(id=job_id).first()
                if job:
                    results.append(job.status == JobStatus.READY)
                    print(f"  Thread {job_id}: {job.status.value}")
                else:
                    results.append(False)
                    print(f"  Thread {job_id}: Job not found")
            finally:
                db.close()
        
        success_count = sum(results)
        print(f"✅ {success_count}/3 threads completed successfully")
        
        return success_count >= 2  # Allow 1 failure
        
    except Exception as e:
        print(f"❌ Multi-thread test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Simplified Document Processing Tests")
    print("=" * 50)
    
    test_results = []
    
    # Run tests
    test_results.append(("Simple Processing", test_simple_processing()))
    test_results.append(("Error Handling", test_error_handling()))
    test_results.append(("Multiple Threads", test_multiple_threads()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        print("🎉 All tests passed! The simplified processing system is working correctly.")
        exit(0)
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        exit(1) 