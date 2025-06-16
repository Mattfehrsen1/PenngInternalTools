#!/usr/bin/env python3

import asyncio
import uuid
import sys
import os

# Add the app directory to Python path
sys.path.append('/app' if os.path.exists('/app') else '.')

from database import AsyncSessionLocal
from models import Persona
from sqlalchemy import select

async def create_demo_persona():
    """Create a demo persona for testing"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if demo persona already exists
            result = await db.execute(select(Persona).where(Persona.name == 'Demo Assistant'))
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f'Demo persona already exists: {existing.id}')
                return existing.id
                
            # Create demo persona
            demo_persona = Persona(
                id=str(uuid.uuid4()),
                name='Demo Assistant',
                description='A helpful AI assistant for testing',
                user_id='demo-user-id',
                source_type='demo',
                namespace='demo',  # Required field
                chunk_count=0,
                total_tokens=0
            )
            
            db.add(demo_persona)
            await db.commit()
            await db.refresh(demo_persona)
            
            print(f'✅ Created demo persona: {demo_persona.id}')
            return demo_persona.id
            
        except Exception as e:
            print(f'❌ Error creating demo persona: {e}')
            await db.rollback()
            raise

if __name__ == '__main__':
    asyncio.run(create_demo_persona()) 