import asyncio
from database import AsyncSessionLocal
from sqlalchemy import text

async def quick_check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT p.id, p.name, p.namespace, COUNT(ij.id) as job_count
            FROM personas p 
            LEFT JOIN ingestion_jobs ij ON p.id = ij.persona_id 
            WHERE ij.status = 'COMPLETED'
            GROUP BY p.id, p.name, p.namespace
            HAVING COUNT(ij.id) > 0
            ORDER BY job_count DESC;
        """))
        
        print('=== PERSONAS WITH COMPLETED JOBS ===')
        for row in result.fetchall():
            print(f'Name: {row.name}')
            print(f'ID: {row.id}')
            print(f'Namespace: {row.namespace}')
            print(f'Jobs: {row.job_count}')
            print('-' * 40)

if __name__ == "__main__":
    asyncio.run(quick_check()) 