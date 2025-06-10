import requests
import json
import sys

# Login first
print("🔐 Logging in...")
login_response = requests.post(
    "http://localhost:8000/auth/login",
    data={"username": "demo", "password": "demo123"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
print("✅ Login successful!\n")

# Test chat
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

chat_request = {
    "persona_id": "550e8400-e29b-41d4-a716-446655440001",
    "question": "Tell me about the Value Stack Formula from Alex Hormozi",
    "model": "gpt-4o"
}

print(f"📤 Sending chat request:")
print(f"   Question: {chat_request['question']}")
print(f"   Model: {chat_request['model']}\n")

response = requests.post(
    "http://localhost:8000/chat",
    json=chat_request,
    headers=headers,
    stream=True
)

if response.status_code != 200:
    print(f"❌ Chat failed: {response.text}")
    exit(1)

print("📥 Streaming response:")
print("-" * 60)

event_type = None
citations_shown = False
response_text = []
line_count = 0

try:
    for line in response.iter_lines():
        line_count += 1
        if not line:
            continue
            
        line = line.decode('utf-8').strip()
        
        # Debug: show raw line
        print(f"[DEBUG] Line {line_count}: {line}")
        
        # Handle SSE format
        if line.startswith("event:"):
            event_type = line.split(":", 1)[1].strip()
        elif line.startswith("data:") and event_type:
            data = line.split(":", 1)[1].strip()
            
            try:
                parsed = json.loads(data)
                
                if event_type == "citations" and not citations_shown:
                    citations_shown = True
                    print("\n📚 CITATIONS:")
                    for i, citation in enumerate(parsed):
                        print(f"\n  [{i+1}] Source: {citation['source']}")
                        print(f"      Score: {citation['score']:.4f}")
                        print(f"      Text: \"{citation['text'][:150]}...\"")
                    print("\n💬 RESPONSE:")
                    print("-" * 60)
                    
                elif event_type == "token":
                    token = parsed.get("token", "")
                    response_text.append(token)
                    print(token, end="", flush=True)
                    
                elif event_type == "done":
                    print(f"\n\n✅ COMPLETE!")
                    print(f"   Total tokens: {parsed.get('tokens', 0)}")
                    print("-" * 60)
                    
                    # Show full response
                    print("\n📝 FULL RESPONSE:")
                    print("".join(response_text))
                    
                elif event_type == "error":
                    print(f"\n❌ ERROR: {parsed.get('error', 'Unknown error')}")
                    
            except json.JSONDecodeError as e:
                print(f"\n[DEBUG] JSON decode error on line {line_count}: {e}")
                print(f"[DEBUG] Data was: {data}")

except Exception as e:
    print(f"\n❌ Exception during streaming: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print(f"\n\n[DEBUG] Total lines processed: {line_count}")
print("\n✨ Chat test completed!")
