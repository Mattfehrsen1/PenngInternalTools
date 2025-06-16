#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_chat():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vIiwidXNlcl9pZCI6ImVhNmU4YjNjLWZlOTYtNDBmYi1iODhlLTkxYTg0OWUzZTlmZCIsImV4cCI6MTc0OTY1MDU4NH0.9rsAv8iVBxdOs6X1st6i_BNNroveQhvIBQWsQU2DIYY"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "persona_id": "550e8400-e29b-41d4-a716-446655440001",
        "question": "What is this about?",
        "model": "gpt-4o"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post("http://127.0.0.1:8000/chat", 
                               headers=headers, 
                               json=data) as response:
            print(f"Status: {response.status}")
            print(f"Headers: {response.headers}")
            
            if response.status == 200:
                async for line in response.content:
                    decoded = line.decode('utf-8').strip()
                    if decoded:
                        print(f"Received line: {decoded}")

if __name__ == "__main__":
    asyncio.run(test_chat())
