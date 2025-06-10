import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_chat_endpoint():
    # First, login to get a token
    async with httpx.AsyncClient() as client:
        # Login
        login_response = await client.post(
            "http://localhost:8000/auth/login",
            data={"username": "demo", "password": "demo123"}
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        print("✅ Login successful")
        
        # Prepare chat request
        chat_request = {
            "persona_id": "550e8400-e29b-41d4-a716-446655440001",
            "question": "What can you tell me about this document?",
            "model": "gpt-4o",
            "k": 3
        }
        
        # Test chat endpoint with streaming
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\n📤 Sending chat request...")
        print(f"Question: {chat_request['question']}")
        
        async with client.stream(
            "POST",
            "http://localhost:8000/chat",
            json=chat_request,
            headers=headers,
            timeout=30.0
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                print(f"❌ Chat request failed: {error_text.decode()}")
                return
            
            print("\n📥 Streaming response:")
            citations_received = False
            tokens_received = []
            event_type = None
            
            async for line in response.aiter_lines():
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith("event:"):
                    event_type = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    data = line.split(":", 1)[1].strip()
                    try:
                        parsed_data = json.loads(data)
                        
                        if event_type == "citations" and not citations_received:
                            citations_received = True
                            print("\n📚 Citations:")
                            for citation in parsed_data:
                                print(f"  [{citation['id']}] Score: {citation['score']:.3f}")
                                print(f"      Source: {citation['source']}")
                                print(f"      Text: {citation['text'][:100]}...")
                            print("\n💬 Response:")
                        
                        elif event_type == "token":
                            token = parsed_data.get("token", "")
                            tokens_received.append(token)
                            print(token, end="", flush=True)
                        
                        elif event_type == "done":
                            print(f"\n\n✅ Complete! Total tokens: {parsed_data.get('tokens', 0)}")
                        
                        elif event_type == "error":
                            print(f"\n❌ Error: {parsed_data.get('error', 'Unknown error')}")
                            
                    except json.JSONDecodeError as e:
                        print(f"\n⚠️  Failed to parse JSON: {e}")
                        print(f"    Data: {data}")

if __name__ == "__main__":
    asyncio.run(test_chat_endpoint())
