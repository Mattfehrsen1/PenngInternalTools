#!/usr/bin/env python3
import asyncio
import asyncpg
import os
from urllib.parse import urlparse

async def check_jobs():
    # Connect to database
    url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/cloneadvisor')
    parsed = urlparse(url)
    
    conn = await asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:]
    )
    
    # Check recent ingestion jobs
    jobs = await conn.fetch('''
        SELECT id, status, progress, processed_files, total_files, created_at, job_metadata
        FROM ingestion_jobs 
        ORDER BY created_at DESC 
        LIMIT 5
    ''')
    
    print('Recent Ingestion Jobs:')
    for job in jobs:
        print(f'  ID: {job["id"]}')
        print(f'  Status: {job["status"]}')
        print(f'  Progress: {job["progress"]}%')
        print(f'  Files: {job["processed_files"]}/{job["total_files"]}')
        print(f'  Created: {job["created_at"]}')
        if job["job_metadata"]:
            current_file = job["job_metadata"].get('current_file')
            if current_file:
                print(f'  Current: {current_file}')
            error = job["job_metadata"].get('error')
            if error:
                print(f'  Error: {error}')
        print()
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_jobs()) 