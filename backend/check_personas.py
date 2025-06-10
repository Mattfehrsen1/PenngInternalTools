import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from models import Persona

load_dotenv()

async def check_personas():
    # Convert DATABASE_URL to async format
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Persona))
        personas = result.scalars().all()
        
        print("\nFound personas:")
        for p in personas:
            print(f"  ID: {p.id}")
            print(f"  Name: {p.name}")
            print(f"  Namespace: {p.namespace}")
            print(f"  Chunk count: {p.chunk_count}")
            print(f"  Created: {p.created_at}")
            print()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_personas())
