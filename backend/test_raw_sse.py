import requests

# Login first
login_response = requests.post(
    "http://localhost:8000/auth/login",
    data={"username": "demo", "password": "demo123"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
print("✅ Login successful!")

# Test chat
headers = {"Authorization": f"Bearer {token}"}
chat_request = {
    "persona_id": "550e8400-e29b-41d4-a716-446655440001",
    "question": "Tell me about the Value Stack Formula",
    "model": "gpt-4o"
}

print("\n📤 Sending chat request...")
with requests.post(
    "http://localhost:8000/chat",
    json=chat_request,
    headers=headers,
    stream=True
) as response:
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print("\n📥 Raw streaming response:")
    print("-" * 60)
    
    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if chunk:
            print(chunk, end="")
