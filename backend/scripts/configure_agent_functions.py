#!/usr/bin/env python3
"""
Script to configure ElevenLabs agents with function calling capabilities
Adds the query_persona_knowledge function to existing agents
"""

import asyncio
import sys
import os
import logging
from typing import Dict, Any
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_agent_function_config(persona_id: str) -> Dict[str, Any]:
    """
    Generate the function configuration for an agent
    
    Args:
        persona_id: UUID of the persona
        
    Returns:
        Function configuration dictionary
    """
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    service_token = os.getenv("ELEVENLABS_SERVICE_TOKEN", "NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0")
    
    return {
        "name": "query_persona_knowledge",
        "description": "Search the persona's knowledge base for relevant information to answer user questions",
        "url": f"{backend_url}/elevenlabs/function-call",
        "method": "POST",
        "headers": {
            "X-Service-Token": service_token,
            "Content-Type": "application/json"
        },
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
            "required": ["query", "persona_id"]
        }
    }

def update_agent_prompt(current_prompt: str) -> str:
    """
    Update agent prompt to include function calling instructions
    
    Args:
        current_prompt: Current system prompt
        
    Returns:
        Updated prompt with function calling instructions
    """
    function_instructions = """

You have access to a comprehensive knowledge base through the query_persona_knowledge function. When users ask questions, you should search your knowledge base for relevant information and provide detailed, accurate responses with proper citations.

Always use the query_persona_knowledge function when users ask questions that might be answered by your knowledge base. This includes questions about topics, concepts, processes, or any subject matter you might have documents about.

When you receive information from your knowledge base, incorporate it naturally into your response and mention the sources when appropriate."""
    
    # Check if function instructions are already present
    if "query_persona_knowledge" in current_prompt:
        logger.info("Function calling instructions already present in prompt")
        return current_prompt
    
    return current_prompt + function_instructions

async def configure_agent_functions():
    """Configure the existing agent with function calling capabilities"""
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("ELEVENLABS_API_KEY not found in environment variables")
        return False
    
    # The specific agent ID that needs configuration
    agent_id = "agent_01jxmeyxz2fh0v3cqx848qk1e0"
    
    # For now, we'll use a default persona ID - in production this would be dynamic
    default_persona_id = "cd35a4a9-31ad-44f5-9de7-cc7dc3196541"  # Alex Hormozi persona from logs
    
    try:
        logger.info(f"Configuring agent {agent_id} with function calling...")
        
        # Note: The actual ElevenLabs API methods for updating agents may differ
        # This is a template showing the expected structure
        
        function_config = get_agent_function_config(default_persona_id)
        
        logger.info("Function configuration:")
        logger.info(json.dumps(function_config, indent=2))
        
        # Manual configuration guide
        logger.info("\n" + "="*60)
        logger.info("MANUAL CONFIGURATION REQUIRED")
        logger.info("="*60)
        logger.info("To configure the agent, follow these steps:")
        logger.info("1. Go to https://elevenlabs.io/app/conversational-ai")
        logger.info(f"2. Find and edit agent: {agent_id}")
        logger.info("3. Go to Tools section and add a new Webhook tool:")
        logger.info(f"   - Name: {function_config['name']}")
        logger.info(f"   - Description: {function_config['description']}")
        logger.info(f"   - URL: {function_config['url']}")
        logger.info(f"   - Method: {function_config['method']}")
        logger.info("   - Headers:")
        for key, value in function_config['headers'].items():
            logger.info(f"     {key}: {value}")
        logger.info("   - Parameters: query (string, required), persona_id (string, required)")
        logger.info("4. Update system prompt to include function calling instructions")
        logger.info("5. Save the agent configuration")
        
        # Test the backend endpoint
        logger.info("\n" + "="*60)
        logger.info("TESTING BACKEND ENDPOINT")
        logger.info("="*60)
        
        test_url = function_config['url']
        test_headers = function_config['headers']
        test_payload = {
            "function_name": "query_persona_knowledge",
            "parameters": {
                "query": "What is Alex Hormozi's approach to business?",
                "persona_id": default_persona_id
            }
        }
        
        try:
            response = requests.post(test_url, headers=test_headers, json=test_payload, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Backend endpoint is working correctly")
                result = response.json()
                if result.get('success'):
                    logger.info("✅ Function call successful")
                    content = result.get('result', {}).get('content', '')
                    logger.info(f"✅ Response preview: {content[:100]}...")
                else:
                    logger.warning(f"⚠️ Function call returned error: {result}")
            else:
                logger.error(f"❌ Backend endpoint returned {response.status_code}: {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"❌ Failed to test backend endpoint: {str(e)}")
        
        logger.info("\n" + "="*60)
        logger.info("NEXT STEPS")
        logger.info("="*60)
        logger.info("1. Complete the manual configuration in ElevenLabs dashboard")
        logger.info("2. Test voice chat with specific questions about persona knowledge")
        logger.info("3. Monitor backend logs for function call attempts")
        logger.info("4. Verify responses include citations from knowledge base")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure agent functions: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Configuring ElevenLabs Agent with Function Calling...")
    success = asyncio.run(configure_agent_functions())
    
    if success:
        print("\n🎉 Configuration guide generated successfully!")
        print("💡 Follow the manual steps above to complete the setup")
    else:
        print("\n❌ Configuration failed. Check the error above.") 