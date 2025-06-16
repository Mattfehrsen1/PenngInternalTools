#!/usr/bin/env python3
"""
Export Alex Hormozi persona data for recreation in production
"""

import asyncio
import json
import os
from database import AsyncSessionLocal
from models import Persona, IngestionJob
from sqlalchemy import select, text

async def export_persona_data():
    """Export persona data that can be manually recreated in production"""
    async with AsyncSessionLocal() as db:
        try:
            # Find persona with most completed files
            result = await db.execute(text("""
                SELECT p.id, p.name, p.namespace, p.description, p.user_id, p.source_type,
                       COUNT(ij.id) as job_count
                FROM personas p 
                LEFT JOIN ingestion_jobs ij ON p.id = ij.persona_id 
                WHERE ij.status IN ('COMPLETED', 'ready')
                GROUP BY p.id, p.name, p.namespace, p.description, p.user_id, p.source_type
                HAVING COUNT(ij.id) > 0
                ORDER BY job_count DESC
                LIMIT 1;
            """))
            
            persona_row = result.fetchone()
            if not persona_row:
                print("❌ No persona found with completed files")
                return
                
            # Get job metadata which might contain file information
            jobs_result = await db.execute(text("""
                SELECT id, total_files, processed_files, status, job_metadata, created_at
                FROM ingestion_jobs 
                WHERE persona_id = :persona_id AND status IN ('COMPLETED', 'ready')
                ORDER BY created_at DESC;
            """), {"persona_id": persona_row.id})
            
            jobs = jobs_result.fetchall()
            
            # Export data
            export_data = {
                "persona": {
                    "original_id": persona_row.id,
                    "name": persona_row.name,
                    "description": persona_row.description,
                    "namespace": persona_row.namespace,
                    "user_id": persona_row.user_id,
                    "source_type": persona_row.source_type,
                    "total_jobs": len(jobs)
                },
                "jobs": [
                    {
                        "id": job.id,
                        "total_files": job.total_files,
                        "processed_files": job.processed_files,
                        "status": job.status,
                        "metadata": job.job_metadata,
                        "created_at": str(job.created_at)
                    }
                    for job in jobs
                ],
                "instructions": {
                    "step1": "Create persona in production with this data",
                    "step2": "Upload documents via UI or API",
                    "step3": "Update ElevenLabs webhook to production URL",
                    "step4": "Test with webhook"
                },
                "webhook_config": {
                    "url": "https://clone-api.fly.dev/elevenlabs/function-call",
                    "service_token": "NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0",
                    "test_payload": {
                        "function_name": "query_persona_knowledge",
                        "parameters": {
                            "query": "how to get rich",
                            "persona_id": "REPLACE_WITH_PRODUCTION_PERSONA_ID"
                        }
                    }
                }
            }
            
            # Save export
            with open("persona_export.json", "w") as f:
                json.dump(export_data, f, indent=2, default=str)
                
            print("✅ PERSONA EXPORT COMPLETE")
            print(f"📋 Persona: {persona_row.name}")
            print(f"📊 Jobs: {len(jobs)}")
            print(f"💾 Saved to: persona_export.json")
            
            # Show summary
            total_files = sum(job.total_files for job in jobs)
            processed_files = sum(job.processed_files for job in jobs)
            
            print(f"\n📈 Summary:")
            print(f"   Total Files: {total_files}")
            print(f"   Processed Files: {processed_files}")
            print(f"   Success Rate: {processed_files/total_files*100:.1f}%" if total_files > 0 else "   No files")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(export_persona_data()) 