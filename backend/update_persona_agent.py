#!/usr/bin/env python3
"""
Script to update persona with ElevenLabs agent ID
Usage: python update_persona_agent.py <persona_id> <agent_id>
"""

import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from models import Persona
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def update_persona_agent_id(persona_id: str, agent_id: str):
    """Update persona with ElevenLabs agent ID"""
    
    # Create async database engine
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    
    # Convert to async URL if needed
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Check if persona exists
            result = await session.execute(
                select(Persona).filter(Persona.id == persona_id)
            )
            persona = result.scalar_one_or_none()
            
            if not persona:
                print(f"❌ Persona with ID {persona_id} not found")
                return False
            
            print(f"✅ Found persona: {persona.name}")
            
            # Update the agent ID
            await session.execute(
                update(Persona)
                .where(Persona.id == persona_id)
                .values(elevenlabs_agent_id=agent_id)
            )
            
            await session.commit()
            print(f"✅ Updated persona {persona.name} with agent ID: {agent_id}")
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error updating persona: {str(e)}")
            return False

async def main():
    if len(sys.argv) != 3:
        print("Usage: python update_persona_agent.py <persona_id> <agent_id>")
        print("\nExample:")
        print("python update_persona_agent.py e250046f-b3c3-4d9e-993e-ed790f7d1e73 your_agent_id_here")
        sys.exit(1)
    
    persona_id = sys.argv[1]
    agent_id = sys.argv[2]
    
    print(f"🔄 Updating persona {persona_id} with agent ID {agent_id}...")
    
    success = await update_persona_agent_id(persona_id, agent_id)
    
    if success:
        print("🎉 Update completed successfully!")
    else:
        print("💥 Update failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 