#!/usr/bin/env python3
"""Test that simulates the exact API endpoint flow"""

import asyncio
import hashlib
import base64
from sqlalchemy import select
from models import Persona, IngestionJob
from database import AsyncSessionLocal

async def simulate_ingest_endpoint():
    """Simulate the exact flow of the ingest endpoint"""
    print("🔍 Simulating ingest endpoint flow...")
    
    try:
        # Simulate file data (like what comes from the API)
        file_data = [
            {
                "filename": "test1.txt",
                "content": b"Test content 1 for debugging",
                "hash": hashlib.sha256(b"Test content 1 for debugging").hexdigest(),
                "size": len(b"Test content 1 for debugging"),
                "type": "text"
            },
            {
                "filename": "test2.txt", 
                "content": b"Test content 2 for debugging",
                "hash": hashlib.sha256(b"Test content 2 for debugging").hexdigest(),
                "size": len(b"Test content 2 for debugging"),
                "type": "text"
            }
        ]
        
        print(f"✅ Prepared {len(file_data)} files")
        
        async with AsyncSessionLocal() as db:
            # Get the first persona (simulating user authentication)
            result = await db.execute(select(Persona).limit(1))
            persona = result.scalar_one_or_none()
            
            if not persona:
                print("❌ No persona found in database")
                return False
                
            print(f"✅ Found persona: {persona.id}")
            
            # Create ingestion job (exactly like in the API)
            from models import generate_uuid
            job = IngestionJob(
                persona_id=persona.id,
                user_id=persona.user_id,
                total_files=len(file_data),
                processed_files=0,
                status="QUEUED",
                progress=0,
                job_metadata={
                    "files": [
                        {
                            "filename": f["filename"], 
                            "hash": f["hash"], 
                            "size": f["size"], 
                            "type": f["type"]
                        } 
                        for f in file_data
                    ],
                    "total_size": sum(f["size"] for f in file_data)
                }
            )
            
            print(f"✅ Created job object: {job.id}")
            
            db.add(job)
            print("✅ Added job to session")
            
            await db.commit()
            print("✅ Committed job to database")
            
            await db.refresh(job)
            print(f"✅ Refreshed job: {job.id}")
            
            # Prepare worker file data (like in API)
            worker_files_data = []
            for f in file_data:
                worker_files_data.append({
                    "filename": f["filename"],
                    "content": base64.b64encode(f["content"]).decode('utf-8')
                })
            
            print("✅ Prepared worker file data")
            
            # Try to enqueue the job (this is where it might fail)
            from services.queue_manager import enqueue_job
            from services.ingestion_worker import run_ingestion_job
            
            rq_job_id = enqueue_job(
                run_ingestion_job,
                job.id,
                persona.id,
                worker_files_data,
                queue_name="ingestion",
                job_timeout="30m"
            )
            
            print(f"✅ Enqueued RQ job: {rq_job_id}")
            
            # Clean up
            await db.delete(job)
            await db.commit()
            print("✅ Cleaned up test job")
            
        return True
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(simulate_ingest_endpoint()) 