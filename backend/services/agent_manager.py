import os
import logging
from elevenlabs import ElevenLabs
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AgentManager:
    """
    Manages ElevenLabs agents for personas
    Creates and configures agents with function calling capabilities
    """
    
    def __init__(self):
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
        
        self.client = ElevenLabs(api_key=api_key)
        self.service_token = os.getenv("ELEVENLABS_SERVICE_TOKEN")
        if not self.service_token:
            logger.warning("ELEVENLABS_SERVICE_TOKEN not set - agents won't be able to call functions")
    
    def get_agent_config_template(
        self, 
        persona_name: str, 
        persona_prompt: str,
        persona_id: str,
        voice_id: str = "EXAVITQu4vr4xnSDxMaL"
    ) -> Dict[str, Any]:
        """
        Create agent configuration template for a persona
        
        Args:
            persona_name: Name of the persona
            persona_prompt: System prompt for the persona
            persona_id: UUID of the persona for function calls
            voice_id: ElevenLabs voice ID (defaults to Sarah)
            
        Returns:
            Agent configuration dictionary
        """
        # Get the backend URL for function calls
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        
        return {
            "name": f"{persona_name} Voice Agent",
            "prompt": f"""{persona_prompt}

You have access to a comprehensive knowledge base through function calls. When users ask questions, you should search your knowledge base for relevant information and provide detailed, accurate responses with proper citations.

Always use the query_persona_knowledge function when users ask questions that might be answered by your knowledge base. This includes questions about topics, concepts, processes, or any subject matter you might have documents about.

When you receive information from your knowledge base, incorporate it naturally into your response and mention the sources when appropriate.""",
            
            "voice": {"voice_id": voice_id},
            
            "tools": [{
                "type": "function",
                "function": {
                    "name": "query_persona_knowledge",
                    "description": "Search the persona's knowledge base for relevant information to answer user questions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The user's question or search query"
                            },
                            "persona_id": {
                                "type": "string", 
                                "description": "The persona ID to search knowledge for",
                                "default": persona_id
                            }
                        },
                        "required": ["query"]
                    }
                }
            }],
            
            "webhook": {
                "url": f"{backend_url}/elevenlabs/function-call",
                "headers": {
                    "X-Service-Token": self.service_token
                }
            } if self.service_token else None
        }
    
    async def create_agent(self, config: Dict[str, Any]) -> str:
        """
        Create a new ElevenLabs agent
        
        Args:
            config: Agent configuration dictionary
            
        Returns:
            Agent ID string
            
        Raises:
            Exception: If agent creation fails
        """
        try:
            # Note: The actual API method may differ based on ElevenLabs SDK version
            # This is based on the conversational AI API structure
            response = self.client.conversational_ai.create_agent(**config)
            agent_id = response.agent_id if hasattr(response, 'agent_id') else response.id
            
            logger.info(f"Created ElevenLabs agent: {agent_id} for {config['name']}")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create ElevenLabs agent: {str(e)}")
            raise Exception(f"Failed to create agent: {str(e)}")
    
    async def update_agent(self, agent_id: str, config: Dict[str, Any]) -> bool:
        """
        Update an existing ElevenLabs agent
        
        Args:
            agent_id: ID of the agent to update
            config: Updated agent configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.conversational_ai.update_agent(agent_id, **config)
            logger.info(f"Updated ElevenLabs agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update ElevenLabs agent {agent_id}: {str(e)}")
            return False
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an ElevenLabs agent
        
        Args:
            agent_id: ID of the agent to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.conversational_ai.delete_agent(agent_id)
            logger.info(f"Deleted ElevenLabs agent: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete ElevenLabs agent {agent_id}: {str(e)}")
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent details
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent details dictionary or None if not found
        """
        try:
            agent = self.client.conversational_ai.get_agent(agent_id)
            return agent
            
        except Exception as e:
            logger.error(f"Failed to get ElevenLabs agent {agent_id}: {str(e)}")
            return None 