"""
Queue Manager for handling async file processing jobs
Implements RQ (Redis Queue) for reliable background job processing
"""
import os
import redis
from rq import Queue, Worker, Connection
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def get_redis_connection():
    """Get Redis connection instance"""
    try:
        # Use standard Redis connection for RQ
        return redis.from_url(REDIS_URL)
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

def get_queue(name: str = "default") -> Queue:
    """Get RQ queue instance"""
    redis_conn = get_redis_connection()
    return Queue(name, connection=redis_conn)

def enqueue_job(
    func, 
    *args, 
    queue_name: str = "default",
    job_timeout: str = "10m",
    **kwargs
) -> str:
    """
    Enqueue a background job
    
    Args:
        func: Function to execute
        *args: Function arguments
        queue_name: Queue name (default: "default")
        job_timeout: Job timeout (default: "10m")
        **kwargs: Function keyword arguments
    
    Returns:
        Job ID string
    """
    queue = get_queue(queue_name)
    job = queue.enqueue(func, *args, job_timeout=job_timeout, **kwargs)
    logger.info(f"Enqueued job {job.id} to queue {queue_name}")
    return job.id

def get_job_status(job_id: str, queue_name: str = "default") -> Dict[str, Any]:
    """
    Get job status and progress
    
    Args:
        job_id: Job ID
        queue_name: Queue name
    
    Returns:
        Dict with job status information
    """
    queue = get_queue(queue_name)
    
    try:
        job = queue.fetch_job(job_id)
        if not job:
            return {"status": "not_found", "progress": 0}
        
        # Handle job status safely
        status = job.get_status()
        
        # Get metadata safely
        progress = 0
        current_file = None
        total_chunks = 0
        
        if hasattr(job, 'meta') and job.meta:
            progress = job.meta.get("progress", 0)
            current_file = job.meta.get("current_file")
            total_chunks = job.meta.get("total_chunks", 0)
        
        # Get error info safely
        error_info = None
        if job.exc_info:
            try:
                error_info = str(job.exc_info)
            except:
                error_info = "Job failed with unknown error"
        
        return {
            "id": job.id,
            "status": status,
            "progress": progress,
            "current_file": current_file,
            "total_chunks": total_chunks,
            "result": job.result if hasattr(job, 'result') else None,
            "error": error_info,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
        }
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {e}")
        return {"status": "error", "progress": 0, "error": str(e)}

def cancel_job(job_id: str, queue_name: str = "default") -> bool:
    """Cancel a job"""
    queue = get_queue(queue_name)
    try:
        job = queue.fetch_job(job_id)
        if job:
            job.cancel()
            return True
        return False
    except Exception as e:
        logger.error(f"Error canceling job {job_id}: {e}")
        return False

def start_worker(queue_names: list = None):
    """
    Start RQ worker (for development/testing)
    In production, workers should be started as separate processes
    """
    if queue_names is None:
        queue_names = ["default"]
    
    redis_conn = get_redis_connection()
    queues = [Queue(name, connection=redis_conn) for name in queue_names]
    
    worker = Worker(queues, connection=redis_conn)
    logger.info(f"Starting worker for queues: {queue_names}")
    
    worker.work()

# Test function to verify queue is working
def test_job(message: str) -> str:
    """Simple test job for queue verification"""
    import time
    time.sleep(2)  # Simulate work
    return f"Processed: {message}" 