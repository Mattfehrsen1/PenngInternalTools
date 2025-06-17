#!/usr/bin/env python3
"""
Manual Agent Setup Helper
Generates configuration instructions for manually setting up ElevenLabs agents
"""

import asyncio
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

def generate_agent_config_instructions():
    """Generate manual configuration instructions for all personas"""
    
    print("🎯 MANUAL ELEVENLABS AGENT CONFIGURATION GUIDE")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Database connection
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ No DATABASE_URL found in environment")
        return
    
    # Convert postgres:// to postgresql:// if needed
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get all personas that need agents
        result = session.execute(text("""
            SELECT id, name, description 
            FROM personas 
            WHERE user_id = 'demo-user-id'
            ORDER BY name
        """))
        
        personas = result.fetchall()
        
        print(f"Found {len(personas)} personas that need agent configuration")
        print()
        
        # Configuration template
        webhook_config = {
            "name": "query_persona_knowledge",
            "description": "Search the persona's knowledge base for relevant information to answer user questions",
            "url": "https://clone-api.fly.dev/elevenlabs/function-call",
            "method": "POST",
            "headers": {
                "X-Service-Token": "NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0",
                "Content-Type": "application/json"
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {
                        "type": "string",
                        "enum": ["query_persona_knowledge"]
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
                                "description": "The persona ID to search knowledge for"
                            }
                        },
                        "required": ["query", "persona_id"]
                    }
                },
                "required": ["function_name", "parameters"]
            }
        }
        
        for i, persona in enumerate(personas, 1):
            persona_id, name, description = persona
            
            print(f"📋 {i}. {name}")
            print(f"   Persona ID: {persona_id}")
            print("   ⚠️ No agent configured - needs manual setup")
            print()
            
            print("   🔧 MANUAL SETUP INSTRUCTIONS:")
            print("   1. Go to: https://elevenlabs.io/app/conversational-ai")
            print("   2. Click 'Create Agent' (or edit existing)")
            print(f"   3. Name: '{name} Voice Clone'")
            print("   4. Voice: Choose any voice you prefer")
            print("   5. System Prompt:")
            print(f"      ```")
            print(f"      You are {name}, a knowledgeable AI assistant.")
            if description:
                print(f"      {description}")
            print(f"      ")
            print(f"      You have access to a comprehensive knowledge base through the query_persona_knowledge function.")
            print(f"      When users ask questions, ALWAYS search your knowledge base first for relevant information.")
            print(f"      Provide detailed, accurate responses with proper citations when available.")
            print(f"      ")
            print(f"      Use query_persona_knowledge for ANY question that might be answered by your documents.")
            print(f"      Keep responses conversational and under 200 words for voice delivery.")
            print(f"      ```")
            print()
            print("   6. Tools Configuration:")
            print("      - Click 'Add Tool' → 'Webhook'")
            print(f"      - Name: query_persona_knowledge")
            print(f"      - Description: Search {name}'s knowledge base")
            print(f"      - URL: https://clone-api.fly.dev/elevenlabs/function-call")
            print(f"      - Method: POST")
            print(f"      - Headers:")
            print(f"        X-Service-Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0")
            print(f"        Content-Type: application/json")
            print()
            print("      - Parameters Schema:")
            print("        ```json")
            print(json.dumps({
                "type": "object", 
                "properties": {
                    "function_name": {"type": "string", "enum": ["query_persona_knowledge"]},
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The user's question"},
                            "persona_id": {"type": "string", "description": "Persona ID", "default": persona_id}
                        },
                        "required": ["query", "persona_id"]
                    }
                },
                "required": ["function_name", "parameters"]
            }, indent=8))
            print("        ```")
            print()
            print("   7. Save the agent and copy the Agent ID")
            print("   8. Test by asking about the persona's knowledge")
            print()
            print("   🧪 TEST WEBHOOK:")
            print(f"   curl -X POST https://clone-api.fly.dev/elevenlabs/function-call \\")
            print(f"     -H 'X-Service-Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfLD0' \\")
            print(f"     -H 'Content-Type: application/json' \\")
            print(f"     -d '{{\"function_name\": \"query_persona_knowledge\", \"parameters\": {{\"query\": \"test\", \"persona_id\": \"{persona_id}\"}}}}'")
            print()
            print("-" * 60)
            print()
        
        print("🎉 COMPLETION CHECKLIST:")
        print("- [ ] All agents created in ElevenLabs dashboard")
        print("- [ ] Webhook tools configured for each agent") 
        print("- [ ] System prompts include knowledge base instructions")
        print("- [ ] Each persona_id correctly set in webhook parameters")
        print("- [ ] Test webhook endpoints return knowledge content")
        print("- [ ] Voice chat tests show knowledge-based responses")
        print()
        print("💡 TIP: Start with 1-2 agents to test the process, then apply to all")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")

if __name__ == "__main__":
    generate_agent_config_instructions() 