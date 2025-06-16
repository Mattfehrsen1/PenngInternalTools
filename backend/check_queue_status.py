#!/usr/bin/env python3
"""Check Redis queue and job status"""
import os
from dotenv import load_dotenv
from rq import Queue
from redis import Redis
import json

load_dotenv()

# Connect to Redis
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_conn = Redis.from_url(redis_url)

# Check queues
for queue_name in ['default', 'ingestion']:
    q = Queue(queue_name, connection=redis_conn)
    print(f"\n📦 Queue: {queue_name}")
    print(f"   Jobs: {len(q)}")
    print(f"   Failed: {q.failed_job_registry.count}")
    
    # Show recent jobs
    jobs = q.get_jobs()[:5]  # Last 5 jobs
    for job in jobs:
        print(f"\n   Job: {job.id}")
        print(f"   Status: {job.get_status()}")
        print(f"   Function: {job.func_name}")
        if job.meta:
            print(f"   Meta: {json.dumps(job.meta, indent=2)}")
        if job.exc_info:
            print(f"   Error: {job.exc_info}")

# Check failed jobs
from rq import get_failed_queue
failed_q = get_failed_queue(connection=redis_conn)
if failed_q.count > 0:
    print(f"\n❌ Failed jobs: {failed_q.count}")
    for job in failed_q.get_jobs()[:3]:
        print(f"\n   Job: {job.id}")
        print(f"   Error: {job.exc_info}") 