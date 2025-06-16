#!/usr/bin/env python3
"""
Redis Queue Worker for Clone Advisor
Processes ingestion jobs asynchronously

Usage:
    python worker.py [queue_name]
    
Examples:
    python worker.py                    # Process default queue
    python worker.py ingestion          # Process ingestion queue
    python worker.py default ingestion  # Process multiple queues
"""
import os
import sys
import logging
import signal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix for macOS fork() issue with threading
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main worker process"""
    # Import after environment is loaded
    from services.queue_manager import start_worker
    
    # Get queue names from command line args
    queue_names = sys.argv[1:] if len(sys.argv) > 1 else ["default", "ingestion"]
    
    logger.info(f"Starting Clone Advisor Worker")
    logger.info(f"Processing queues: {queue_names}")
    logger.info(f"Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379/0')}")
    
    # Setup graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal, stopping worker...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the worker (this blocks)
        start_worker(queue_names)
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 