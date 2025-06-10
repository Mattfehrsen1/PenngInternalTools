import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from models import User

load_dotenv()

async def check_users():
    # Convert DATABASE_URL to async format
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print("\nFound users:")
        for u in users:
            print(f"  ID: {u.id}")
            print(f"  Username: {u.username}")
            print(f"  Email: {u.email}")
            print(f"  Created: {u.created_at}")
            print()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_users())
