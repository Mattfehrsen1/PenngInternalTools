"""Test database update function directly"""
import asyncio
import os
from dotenv import load_dotenv
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import database models
from database import AsyncSessionLocal
from models import Persona
from sqlalchemy import select

async def test_update_persona():
    """Test updating persona chunk count directly"""
    # Create test persona if needed
    persona_id = "test-persona-id"
    
    # First check if persona exists
    async with AsyncSessionLocal() as db:
        stmt = select(Persona).where(Persona.id == persona_id)
        result = await db.execute(stmt)
        persona = result.scalar_one_or_none()
        
        if not persona:
            # Create test persona
            logger.info("Creating test persona")
            persona = Persona(
                id=persona_id,
                name="Test DB Update",
                namespace="test_namespace",
                source_type="text",
                chunk_count=0
            )
            db.add(persona)
            await db.commit()
            logger.info(f"Created test persona with id {persona_id}")
    
    # Now update the chunk count
    try:
        logger.info("Updating persona chunk count")
        async with AsyncSessionLocal() as db:
            stmt = select(Persona).where(Persona.id == persona_id)
            result = await db.execute(stmt)
            persona = result.scalar_one_or_none()
            
            if persona:
                # Update chunk count
                persona.chunk_count = 5
                persona.total_tokens = 1000
                await db.commit()
                logger.info(f"Updated persona {persona_id} with chunk_count=5")
            else:
                logger.error(f"Persona {persona_id} not found")
    except Exception as e:
        logger.error(f"Error updating persona: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Verify the update
    async with AsyncSessionLocal() as db:
        stmt = select(Persona).where(Persona.id == persona_id)
        result = await db.execute(stmt)
        persona = result.scalar_one_or_none()
        
        if persona:
            logger.info(f"Persona {persona_id} has chunk_count={persona.chunk_count}")
        else:
            logger.error(f"Persona {persona_id} not found")

if __name__ == "__main__":
    asyncio.run(test_update_persona())
