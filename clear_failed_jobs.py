#!/usr/bin/env python3
"""
Clear failed jobs from Redis queue
"""

import sys
import os
sys.path.append('backend')

from services.queue_manager import get_redis_connection, get_queue
from rq.registry import FailedJobRegistry

def clear_failed_jobs():
    """Clear all failed jobs from the ingestion queue"""
    
    redis_conn = get_redis_connection()
    ingestion_queue = get_queue('ingestion')
    failed_registry = FailedJobRegistry(queue=ingestion_queue)
    
    failed_jobs = failed_registry.get_job_ids()
    for job_id in failed_jobs:
        failed_registry.remove(job_id)
    
    print(f'✅ Cleared {len(failed_jobs)} failed jobs')
    print(f'📦 Queue length after cleanup: {len(ingestion_queue)}')

if __name__ == "__main__":
    clear_failed_jobs() 