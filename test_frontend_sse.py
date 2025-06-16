#!/usr/bin/env python3
import requests
import json

# Test the SSE chat endpoint to verify our frontend fixes will work
def test_sse_chat():
    # First login
    print("🔐 Logging in...")
    login_response = requests.post(
        "http://localhost:8000/auth/login",
        data={"username": "demo", "password": "demo123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print("✅ Login successful!")
    
    # Test chat with streaming
    headers = {"Authorization": f"Bearer {token}"}
    chat_request = {
        "persona_id": "550e8400-e29b-41d4-a716-446655440001",  # Demo persona ID
        "question": "What is the main concept?",
        "model": "gpt-4o",
        "k": 3
    }
    
    print("\n📤 Testing SSE chat...")
    with requests.post(
        "http://localhost:8000/chat",
        json=chat_request,
        headers=headers,
        stream=True
    ) as response:
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Chat failed: {response.text}")
            return
            
        print("\n📥 Raw SSE Response:")
        print("-" * 50)
        
        current_event = ""
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
                
            line = line.strip()
            print(f"[RAW] {line}")
            
            if line.startswith('event: '):
                current_event = line[7:].strip()
                print(f"  → Event: {current_event}")
            elif line.startswith('data: '):
                data_str = line[6:].strip()
                try:
                    data = json.loads(data_str)
                    print(f"  → Data ({current_event}): {data}")
                    
                    if current_event == 'citations':
                        print(f"    📚 Citations received: {len(data)} items")
                    elif current_event == 'token':
                        print(f"    💬 Token: '{data.get('token', '')}'")
                    elif current_event == 'done':
                        print(f"    ✅ Done: {data}")
                        break
                    elif current_event == 'error':
                        print(f"    ❌ Error: {data}")
                        break
                except json.JSONDecodeError as e:
                    print(f"    ⚠️  JSON decode error: {e}")

if __name__ == "__main__":
    test_sse_chat() 