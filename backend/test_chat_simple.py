import requests
import json

# Login first
login_response = requests.post(
    "http://localhost:8000/auth/login",
    data={"username": "demo", "password": "demo123"},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
print("✅ Login successful")

# Test chat
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
chat_request = {
    "persona_id": "550e8400-e29b-41d4-a716-446655440001",
    "question": "What can you tell me about this document?",
    "model": "gpt-4o"
}

print("\n📤 Sending chat request...")
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
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
