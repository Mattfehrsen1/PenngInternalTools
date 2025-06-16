#!/usr/bin/env python3
"""
Debug script to check failed jobs in Redis queue
"""

import sys
import os
sys.path.append('backend')

from services.queue_manager import get_redis_connection
from rq import Queue
from rq.registry import FailedJobRegistry
import json

def check_failed_jobs():
    """Check failed jobs in the ingestion queue"""
    
    redis_conn = get_redis_connection()
    ingestion_queue = Queue('ingestion', connection=redis_conn)
    
    print('=== INGESTION QUEUE STATUS ===')
    print(f'Queue length: {len(ingestion_queue)}')
    print(f'Jobs: {ingestion_queue.count}')
    
    failed_registry = FailedJobRegistry(queue=ingestion_queue)
    print(f'Failed jobs: {len(failed_registry)}')
    
    if failed_registry:
        print('\n=== FAILED JOB DETAILS ===')
        for job_id in failed_registry.get_job_ids()[:5]:  # Show last 5
            try:
                job = ingestion_queue.fetch_job(job_id)
                if job:
                    print(f'\nJob ID: {job_id}')
                    print(f'Status: {job.get_status()}')
                    print(f'Exception: {job.exc_info}')
                    if hasattr(job, 'result') and job.result:
                        print(f'Result: {job.result}')
            except Exception as e:
                print(f'Error reading job {job_id}: {e}')

if __name__ == "__main__":
    check_failed_jobs() 