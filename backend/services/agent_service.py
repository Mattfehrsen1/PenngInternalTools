"""
ElevenLabs Agent Management Service
Implements Sprint 7 Phase 2: Automatic Agent Creation

This service handles the complete lifecycle of ElevenLabs agents:
- Create agents automatically when personas are created
- Update agents when persona prompts/settings change
- Delete agents when personas are deleted
- Manage agent configuration templates
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from elevenlabs.client import ElevenLabs
from elevenlabs import ConversationalConfig
from elevenlabs.types import (
    TtsConversationalConfigOutput, 
    AgentConfig, 
    PromptAgentDbModelToolsItem_Webhook,
    PromptAgentDbModel,
    WebhookToolApiSchemaConfigInput,
    ObjectJsonSchemaPropertyInput,
    ArrayJsonSchemaPropertyInput,
    LiteralJsonSchemaProperty
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models import Persona, PersonaSettings
from fastapi import HTTPException
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Fix Pydantic model rebuild issue
def rebuild_elevenlabs_models():
    """Rebuild ElevenLabs Pydantic models to resolve circular dependencies"""
    try:
        # Import all the models first
        from elevenlabs.types import (
            LiteralJsonSchemaProperty,
            ArrayJsonSchemaPropertyInput,
            ObjectJsonSchemaPropertyInput,
            WebhookToolApiSchemaConfigInput,
            PromptAgentDbModelToolsItem_Webhook,
            PromptAgentDbModel,
            AgentConfig,
            ConversationalConfig
        )
        
        # Rebuild in dependency order
        models_to_rebuild = [
            LiteralJsonSchemaProperty,
            ArrayJsonSchemaPropertyInput,
            ObjectJsonSchemaPropertyInput,
            WebhookToolApiSchemaConfigInput,
            PromptAgentDbModelToolsItem_Webhook,
            PromptAgentDbModel,
            AgentConfig,
            ConversationalConfig
        ]
        
        for model in models_to_rebuild:
            try:
                model.model_rebuild()
                logger.debug(f"Successfully rebuilt {model.__name__}")
            except Exception as e:
                logger.warning(f"Failed to rebuild {model.__name__}: {e}")
        
        logger.info("ElevenLabs Pydantic models rebuilt successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to rebuild ElevenLabs models: {e}")
        return False

class AgentService:
    """ElevenLabs Agent Management Service for automatic agent creation"""
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY') or 'sk_b9ba5630e7081c14af2585afd43087e2a4675ce7dabaea22'
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not found - agent management disabled")
            self.client = None
        else:
            logger.info(f"Initializing ElevenLabs client with API key: {self.api_key[:10]}...")
            self.client = ElevenLabs(api_key=self.api_key)
            
            # Rebuild Pydantic models to fix circular dependencies
            rebuild_elevenlabs_models()
        
        # Base webhook URL for dynamic routing
        self.webhook_base_url = os.getenv('WEBHOOK_BASE_URL', 'https://clone-api.fly.dev')
        
    async def create_agent_for_persona(
        self, 
        persona_id: str, 
        persona_name: str,
        voice_id: str = None,
        system_prompt: str = None,
        db: AsyncSession = None
    ) -> Optional[str]:
        """
        Create ElevenLabs agent for a persona
        TEMPORARILY DISABLED: Pydantic model circular dependency issues
        Returns None to indicate manual configuration needed
        """
        logger.warning(f"Agent creation temporarily disabled due to Pydantic issues. Please manually configure agent for persona {persona_id}")
        logger.info(f"Manual configuration needed for {persona_name}:")
        logger.info(f"  1. Go to https://elevenlabs.io/app/conversational-ai")
        logger.info(f"  2. Create agent manually with webhook: https://clone-api.fly.dev/elevenlabs/function-call")
        logger.info(f"  3. Use persona_id: {persona_id}")
        logger.info(f"  4. Add function calling for knowledge base access")
        
        return None  # Temporarily return None instead of creating agent
    
    async def update_agent_for_persona(
        self, 
        persona_id: str, 
        agent_id: str,
        persona_name: str = None,
        voice_id: str = None,
        system_prompt: str = None
    ) -> bool:
        """
        Update existing ElevenLabs agent configuration
        Returns True if successful, False if failed
        """
        if not self.client:
            logger.error("ElevenLabs client not available - cannot update agent")
            return False
            
        try:
            # Build updated configuration
            update_config = {}
            
            if persona_name:
                update_config['name'] = f"{persona_name} Voice Clone"
            
            if voice_id:
                update_config['voice_id'] = voice_id
                
            if system_prompt:
                update_config['prompt'] = {
                    'prompt': system_prompt
                }
            
            if not update_config:
                logger.info(f"No updates needed for agent {agent_id}")
                return True
            
            logger.info(f"Updating ElevenLabs agent {agent_id} for persona {persona_id}")
            
            # Update agent via ElevenLabs API
            updated_agent = self.client.conversational_ai.agents.update(
                agent_id=agent_id,
                **update_config
            )
            
            if updated_agent:
                logger.info(f"✅ Updated ElevenLabs agent {agent_id}")
                return True
            else:
                logger.error(f"Agent update failed for {agent_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {str(e)}")
            return False
    
    async def delete_agent_for_persona(self, agent_id: str, persona_id: str = None) -> bool:
        """
        Delete ElevenLabs agent
        Returns True if successful, False if failed
        """
        if not self.client:
            logger.error("ElevenLabs client not available - cannot delete agent")
            return False
            
        try:
            logger.info(f"Deleting ElevenLabs agent {agent_id}")
            
            # Delete agent via ElevenLabs API
            self.client.conversational_ai.agents.delete(agent_id=agent_id)
            
            logger.info(f"✅ Deleted ElevenLabs agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
            return False
    
    async def verify_agent_exists(self, agent_id: str) -> bool:
        """
        Verify that an ElevenLabs agent exists
        Returns True if exists, False if not found
        """
        if not self.client:
            return False
            
        try:
            agent = self.client.conversational_ai.agents.get(agent_id=agent_id)
            return agent is not None
        except Exception as e:
            logger.error(f"Failed to verify agent {agent_id}: {str(e)}")
            return False
    
    async def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """
        Get detailed status information about an agent
        Returns dict with agent status and configuration
        """
        if not self.client:
            return {"status": "unavailable", "error": "API client not configured"}
            
        try:
            agent = self.client.conversational_ai.agents.get(agent_id=agent_id)
            
            if agent:
                return {
                    "status": "active",
                    "agent_id": agent_id,
                    "name": getattr(agent, 'name', 'Unknown'),
                    "voice_id": getattr(agent, 'voice_id', None),
                    "created_at": getattr(agent, 'created_at', None)
                }
            else:
                return {"status": "not_found", "agent_id": agent_id}
                
        except Exception as e:
            logger.error(f"Failed to get agent status {agent_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _build_conversation_config(
        self, 
        persona_id: str, 
        persona_name: str, 
        voice_id: str,
        system_prompt: str = None
    ) -> ConversationalConfig:
        """
        Build ConversationalConfig for ElevenLabs API using new structure
        Returns ConversationalConfig object ready for API call
        """
        # Default system prompt if none provided
        if not system_prompt:
            system_prompt = f"""You are {persona_name}, a knowledgeable AI assistant. 
You have access to a specialized knowledge base and can answer questions using that information.
Always provide helpful, accurate responses based on your knowledge."""
        
        # Build webhook URL for this specific persona
        webhook_url = f"{self.webhook_base_url}/elevenlabs/function-call/{persona_id}"
        
        # Configure TTS settings
        tts_config = TtsConversationalConfigOutput(
            model_id="eleven_turbo_v2",
            voice_id=voice_id,
            stability=0.5,
            similarity_boost=0.75,
            speed=1.0
        )
        
        # Create webhook API schema for knowledge base queries
        webhook_api_schema = WebhookToolApiSchemaConfigInput(
            url=webhook_url,
            method="POST",
            request_headers={
                "X-Service-Token": os.getenv('SERVICE_TOKEN', 'default-token'),
                "Content-Type": "application/json"
            },
            request_body_schema=ObjectJsonSchemaPropertyInput(
                type="object",
                properties={
                    "query": LiteralJsonSchemaProperty(
                        type="string",
                        description="The question or topic to search for in the knowledge base"
                    )
                },
                required=["query"]
            )
        )
        
        # Create webhook tool for knowledge base queries
        query_tool = PromptAgentDbModelToolsItem_Webhook(
            type="webhook",
            name="query_persona_knowledge",
            description=f"Query {persona_name}'s knowledge base for specific information",
            api_schema=webhook_api_schema,
            response_timeout_secs=30
        )
        
        # Configure Prompt settings
        prompt_config = PromptAgentDbModel(
            prompt=system_prompt,
            llm="gemini-2.0-flash",
            temperature=0.1,
            tools=[query_tool]
        )
        
        # Configure Agent settings
        agent_config = AgentConfig(
            prompt=prompt_config,
            language="en",
            first_message=f"Hello! I'm {persona_name}. How can I help you today?"
        )
        
        # Build complete ConversationalConfig
        conversation_config = ConversationalConfig(
            tts=tts_config,
            agent=agent_config
        )
        
        return conversation_config

    def _build_agent_config(
        self, 
        persona_id: str, 
        persona_name: str, 
        voice_id: str,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Legacy method for backward compatibility
        Use _build_conversation_config instead
        """
        logger.warning("_build_agent_config is deprecated, use _build_conversation_config")
        return self._build_conversation_config(persona_id, persona_name, voice_id, system_prompt)
    
    async def _update_persona_agent_id(
        self, 
        persona_id: str, 
        agent_id: str, 
        db: AsyncSession
    ) -> bool:
        """
        Update persona with the created agent_id
        Returns True if successful, False if failed
        """
        try:
            await db.execute(
                update(Persona)
                .where(Persona.id == persona_id)
                .values(elevenlabs_agent_id=agent_id)
            )
            await db.commit()
            logger.info(f"Updated persona {persona_id} with agent_id {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update persona {persona_id} with agent_id: {str(e)}")
            await db.rollback()
            return False
    
    async def _get_persona_voice_id(self, persona_id: str, db: AsyncSession) -> Optional[str]:
        """
        Get voice_id from PersonaSettings for a persona
        Returns voice_id if found, None if not found
        """
        try:
            settings_result = await db.execute(
                select(PersonaSettings).where(PersonaSettings.persona_id == persona_id)
            )
            settings = settings_result.scalar_one_or_none()
            
            if settings and settings.voice_id:
                logger.info(f"Found voice_id {settings.voice_id} for persona {persona_id}")
                return settings.voice_id
            else:
                logger.info(f"No voice_id found for persona {persona_id}, will use default")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get voice_id for persona {persona_id}: {str(e)}")
            return None

    async def update_agent_voice_when_settings_change(
        self, 
        persona_id: str, 
        new_voice_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Update ElevenLabs agent voice when persona voice settings change
        This should be called when voice settings are updated in the voice section
        Returns True if successful, False if failed
        """
        try:
            # Get current agent_id from database
            result = await db.execute(
                select(Persona.elevenlabs_agent_id, Persona.name)
                .where(Persona.id == persona_id)
            )
            persona_data = result.first()
            
            if not persona_data or not persona_data.elevenlabs_agent_id:
                logger.info(f"No agent found for persona {persona_id}, voice change will apply to future agent creation")
                return True
            
            agent_id = persona_data.elevenlabs_agent_id
            persona_name = persona_data.name
            
            logger.info(f"Updating agent {agent_id} voice to {new_voice_id} for persona '{persona_name}'")
            
            # Recreate agent with new voice (ElevenLabs doesn't support voice updates)
            # First delete old agent
            await self.delete_agent_for_persona(agent_id, persona_id)
            
            # Create new agent with new voice
            new_agent_id = await self.create_agent_for_persona(
                persona_id=persona_id,
                persona_name=persona_name,
                voice_id=new_voice_id,
                system_prompt=None,
                db=db
            )
            
            if new_agent_id:
                logger.info(f"✅ Successfully updated agent voice for persona '{persona_name}' (old: {agent_id}, new: {new_agent_id})")
                return True
            else:
                logger.error(f"Failed to create new agent with updated voice for persona {persona_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update agent voice for persona {persona_id}: {str(e)}")
            return False
    
    async def recreate_agent_if_needed(
        self, 
        persona_id: str, 
        persona_name: str,
        db: AsyncSession
    ) -> Optional[str]:
        """
        Check if agent exists and recreate if missing
        Returns agent_id if exists or successfully recreated, None if failed
        """
        try:
            # Get current agent_id from database
            result = await db.execute(
                select(Persona.elevenlabs_agent_id)
                .where(Persona.id == persona_id)
            )
            current_agent_id = result.scalar_one_or_none()
            
            if current_agent_id:
                # Verify agent still exists in ElevenLabs
                if await self.verify_agent_exists(current_agent_id):
                    logger.info(f"Agent {current_agent_id} verified for persona {persona_id}")
                    return current_agent_id
                else:
                    logger.warning(f"Agent {current_agent_id} not found, recreating...")
            
            # Get persona voice settings for agent creation
            voice_id = None
            system_prompt = None
            
            settings_result = await db.execute(
                select(PersonaSettings).where(PersonaSettings.persona_id == persona_id)
            )
            settings = settings_result.scalar_one_or_none()
            
            if settings and settings.voice_id:
                voice_id = settings.voice_id
            
            # Create new agent
            new_agent_id = await self.create_agent_for_persona(
                persona_id=persona_id,
                persona_name=persona_name,
                voice_id=voice_id,
                system_prompt=system_prompt,
                db=db
            )
            
            return new_agent_id
            
        except Exception as e:
            logger.error(f"Failed to recreate agent for persona {persona_id}: {str(e)}")
            return None

    async def update_agent_voice(
        self, 
        agent_id: str, 
        voice_id: str
    ) -> bool:
        """
        Update the voice of an existing ElevenLabs agent
        Returns True if successful, False if failed
        """
        if not self.client:
            logger.error("ElevenLabs client not available - cannot update agent voice")
            return False
            
        if not agent_id or not voice_id:
            logger.error(f"Missing required parameters: agent_id={agent_id}, voice_id={voice_id}")
            return False
            
        try:
            # Ensure Pydantic models are rebuilt before updating agent
            rebuild_elevenlabs_models()
            
            # Get current agent configuration
            try:
                current_agent = self.client.conversational_ai.agents.get(agent_id=agent_id)
                logger.info(f"Retrieved current agent configuration for {agent_id}")
            except Exception as e:
                logger.error(f"Failed to get current agent {agent_id}: {str(e)}")
                return False
            
            # Update only the voice_id in the conversation_config
            update_data = {
                "conversation_config": {
                    "tts": {
                        "voice_id": voice_id
                    }
                }
            }
            
            # Update the agent
            updated_agent = self.client.conversational_ai.agents.update(
                agent_id=agent_id,
                **update_data
            )
            
            logger.info(f"Successfully updated agent {agent_id} voice to {voice_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id} voice: {str(e)}")
            return False

# Singleton instance
agent_service = AgentService() 