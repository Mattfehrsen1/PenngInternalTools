#!/usr/bin/env python3
"""
Script to create ElevenLabs agents for existing personas
Run this after implementing the ElevenLabs integration to set up voice agents
"""

import asyncio
import sys
import os
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DATABASE_URL
from models import Persona
from services.agent_manager import AgentManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_agents_for_personas():
    """Create ElevenLabs agents for all personas that don't have one"""
    
    # Create synchronous database session for this script
    engine = create_engine(
        DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    )
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    agent_manager = AgentManager()
    
    try:
        # Get all personas
        personas = db.query(Persona).all()
        logger.info(f"Found {len(personas)} personas in database")
        
        for persona in personas:
            if persona.elevenlabs_agent_id:
                logger.info(f"Persona '{persona.name}' already has agent ID: {persona.elevenlabs_agent_id}")
                continue
            
            logger.info(f"Creating agent for persona: {persona.name}")
            
            # Create system prompt from persona description
            system_prompt = f"""You are {persona.name}, an AI assistant specializing in the knowledge contained in your uploaded documents.

{persona.description or "You are helpful, knowledgeable, and provide accurate information based on your knowledge base."}

Your responses should be:
- Accurate and based on your knowledge base when possible
- Helpful and informative
- Professional yet approachable
- Include proper citations when referencing specific sources

Always search your knowledge base when users ask questions that might be covered in your documents."""

            # Get voice ID from persona settings if available
            voice_id = "EXAVITQu4vr4xnSDxMaL"  # Default Sarah voice
            if persona.settings and persona.settings.voice_id:
                voice_id = persona.settings.voice_id
            
            # Create agent configuration
            config = agent_manager.get_agent_config_template(
                persona_name=persona.name,
                persona_prompt=system_prompt,
                persona_id=persona.id,
                voice_id=voice_id
            )
            
            try:
                # Create the agent
                agent_id = await agent_manager.create_agent(config)
                
                # Update persona with agent ID
                persona.elevenlabs_agent_id = agent_id
                db.commit()
                
                logger.info(f"✅ Created agent {agent_id} for persona '{persona.name}'")
                
            except Exception as e:
                logger.error(f"❌ Failed to create agent for persona '{persona.name}': {str(e)}")
                db.rollback()
                continue
        
        logger.info("Agent creation process completed!")
        
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        db.rollback()
        
    finally:
        db.close()

def main():
    """Main entry point"""
    print("🎙️  ElevenLabs Agent Setup Script")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("❌ ELEVENLABS_API_KEY not found in environment")
        print("Please add your ElevenLabs API key to your .env file")
        return 1
    
    if not os.getenv("ELEVENLABS_SERVICE_TOKEN"):
        print("⚠️  ELEVENLABS_SERVICE_TOKEN not found")
        print("Agents will be created but won't be able to call functions")
        print("Please add ELEVENLABS_SERVICE_TOKEN to your .env file")
    
    try:
        asyncio.run(create_agents_for_personas())
        print("\n✅ Script completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Script failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main()) 