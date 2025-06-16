#!/usr/bin/env python3
"""Check persona status in database and Pinecone"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from models import Persona, IngestionJob
from services.pinecone_client import get_pinecone_client

load_dotenv()

async def check_persona_status(persona_id: str):
    # Setup database
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get persona from database
        result = await session.execute(
            select(Persona).where(Persona.id == persona_id)
        )
        persona = result.scalar_one_or_none()
        
        if not persona:
            print(f"❌ Persona {persona_id} not found in database!")
            return
        
        print(f"📋 Persona Database Status:")
        print(f"   ID: {persona.id}")
        print(f"   Name: {persona.name}")
        print(f"   Namespace: {persona.namespace}")
        print(f"   Chunk count: {persona.chunk_count}")
        print(f"   Total tokens: {persona.total_tokens}")
        print(f"   Created: {persona.created_at}")
        
        # Check ingestion jobs
        job_result = await session.execute(
            select(IngestionJob)
            .where(IngestionJob.persona_id == persona_id)
            .order_by(IngestionJob.created_at.desc())
            .limit(5)
        )
        jobs = job_result.scalars().all()
        
        if jobs:
            print(f"\n📦 Recent Ingestion Jobs:")
            for job in jobs:
                print(f"\n   Job ID: {job.id}")
                print(f"   Status: {job.status}")
                print(f"   Progress: {job.progress}%")
                print(f"   Files: {job.processed_files}/{job.total_files}")
                if job.job_metadata and 'error' in job.job_metadata:
                    print(f"   ❌ Error: {job.job_metadata['error']}")
    
    # Check Pinecone
    print(f"\n🔍 Checking Pinecone...")
    try:
        pinecone_client = get_pinecone_client()
        exists, vector_count = await pinecone_client.check_namespace_exists(persona.namespace)
        
        print(f"   Namespace exists: {exists}")
        print(f"   Vector count: {vector_count}")
        print(f"   Ready status: {'✅ READY' if exists and vector_count > 0 else '❌ NOT READY'}")
        
        if exists and vector_count > 0:
            # Try a test query
            print(f"\n   Testing vector search...")
            test_embedding = [0.1] * 1536
            results = await pinecone_client.similarity_search(
                namespace=persona.namespace,
                query_embedding=test_embedding,
                k=1
            )
            if results:
                print(f"   ✅ Search working! Found {len(results)} results")
            else:
                print(f"   ⚠️ Search returned no results")
                
    except Exception as e:
        print(f"   ❌ Pinecone error: {type(e).__name__}: {e}")
    
    await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_persona_status.py <persona_id>")
        print("Example: python check_persona_status.py 7b36a080-0d6d-40c7-aabd-7e2cc3fa68ed")
        sys.exit(1)
    
    persona_id = sys.argv[1]
    asyncio.run(check_persona_status(persona_id)) 