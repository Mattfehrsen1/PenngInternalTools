import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from models import User, Persona

load_dotenv()

async def update_persona_owner():
    # Convert DATABASE_URL to async format
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find demo user
        result = await session.execute(select(User).where(User.username == "demo"))
        demo_user = result.scalar_one()
        
        # Update persona owner
        await session.execute(
            update(Persona)
            .where(Persona.id == "550e8400-e29b-41d4-a716-446655440001")
            .values(user_id=demo_user.id)
        )
        await session.commit()
        
        print(f"✅ Updated persona owner to demo user (ID: {demo_user.id})")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(update_persona_owner())
