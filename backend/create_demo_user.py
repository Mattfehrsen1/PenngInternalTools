import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import User
from api.auth import get_password_hash

load_dotenv()

async def create_demo_user():
    # Convert DATABASE_URL to async format
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create demo user
        demo_user = User(
            username="demo",
            email="demo@example.com",
            hashed_password=get_password_hash("demo123")
        )
        
        session.add(demo_user)
        await session.commit()
        
        print(f"✅ Created demo user:")
        print(f"   Username: demo")
        print(f"   Password: demo123")
        print(f"   ID: {demo_user.id}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_demo_user())
