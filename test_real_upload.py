#!/usr/bin/env python3
"""
Test script for the real upload processing system
Tests the complete flow from file upload to processing completion
"""

import requests
import time
import json
import base64

# Configuration
API_URL = "http://localhost:8000/api"
USERNAME = "demo"
PASSWORD = "demo123"

def login():
    """Login and get JWT token"""
    response = requests.post(f"http://localhost:8000/auth/login", data={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful, token: {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def get_personas(token):
    """Get list of personas"""
    response = requests.get(f"http://localhost:8000/persona/list", headers={
        "Authorization": f"Bearer {token}"
    })
    
    if response.status_code == 200:
        personas = response.json()["personas"]
        print(f"✅ Found {len(personas)} personas")
        return personas
    else:
        print(f"❌ Failed to get personas: {response.status_code}")
        return []

def test_real_upload(token, persona_id):
    """Test real file upload with processing"""
    print(f"\n🚀 Testing real upload for persona: {persona_id}")
    
    # Create test file content
    test_content = """
    This is a test document for Clone Advisor.
    
    Clone Advisor is an AI-powered system that allows users to create personalized AI assistants.
    The system processes uploaded documents, extracts knowledge, and creates embeddings for retrieval.
    
    Key features:
    1. Document upload and processing
    2. Text chunking and embedding generation
    3. Vector storage in Pinecone
    4. RAG (Retrieval-Augmented Generation) for chat responses
    5. Real-time progress tracking
    
    This test document will be processed through the complete pipeline:
    - Text extraction
    - Chunking into segments
    - Embedding generation
    - Vector storage
    - Persona knowledge base update
    
    Test completed successfully if this content appears in chat responses.
    """
    
    # Prepare multipart form data
    files = {
        'files': ('test_real_upload.txt', test_content.encode('utf-8'), 'text/plain')
    }
    
    # Upload the file
    print("📤 Uploading test file...")
    response = requests.post(
        f"http://localhost:8000/api/personas/{persona_id}/files",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code != 201:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return False
    
    upload_result = response.json()
    job_id = upload_result["id"]
    print(f"✅ Upload successful, job ID: {job_id}")
    print(f"   Status: {upload_result['status']}")
    print(f"   Message: {upload_result['message']}")
    
    # Poll for processing status
    print("\n⏳ Polling processing status...")
    max_attempts = 60  # 1 minute timeout
    
    for attempt in range(max_attempts):
        time.sleep(1)
        
        # Check job status
        status_response = requests.get(
            f"http://localhost:8000/api/personas/{persona_id}/files/{job_id}/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if status_response.status_code != 200:
            print(f"❌ Status check failed: {status_response.status_code}")
            continue
        
        status_data = status_response.json()
        status = status_data["status"]
        progress = status_data["progress"]
        message = status_data["message"]
        
        print(f"   [{attempt+1:02d}] {status} - {progress}% - {message}")
        
        if status == "completed":
            chunks = status_data.get("chunks", 0)
            print(f"\n🎉 Processing completed successfully!")
            print(f"   Created {chunks} knowledge chunks")
            return True
        elif status == "failed":
            print(f"\n❌ Processing failed: {message}")
            return False
    
    print(f"\n⏱️ Timeout after {max_attempts} seconds")
    return False

def test_chat_with_knowledge(token, persona_id):
    """Test chat to verify knowledge is available"""
    print(f"\n💬 Testing chat with new knowledge...")
    
    response = requests.post(f"http://localhost:8000/api/chat", headers={
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream"
    }, json={
        "persona_id": persona_id,
        "question": "What is Clone Advisor and what are its key features?",
        "model": "gpt-4o"
    }, stream=True)
    
    if response.status_code != 200:
        print(f"❌ Chat failed: {response.status_code}")
        return False
    
    print("✅ Chat response (streaming):")
    citations_found = False
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get("event") == "token":
                        print(data["data"]["token"], end="", flush=True)
                    elif data.get("event") == "citations":
                        citations_found = True
                        print(f"\n\n📚 Citations found: {len(data['data'])} sources")
                    elif data.get("event") == "done":
                        break
                except json.JSONDecodeError:
                    continue
    
    print(f"\n\n{'✅' if citations_found else '❌'} Citations {'found' if citations_found else 'not found'}")
    return citations_found

def main():
    """Main test function"""
    print("🧪 Clone Advisor Real Upload Processing Test")
    print("=" * 50)
    
    # Login
    token = login()
    if not token:
        return
    
    # Get personas
    personas = get_personas(token)
    if not personas:
        return
    
    # Use first persona for testing
    persona = personas[0]
    persona_id = persona["id"]
    print(f"🎭 Using persona: {persona['name']} ({persona_id})")
    
    # Test real upload
    upload_success = test_real_upload(token, persona_id)
    if not upload_success:
        print("\n❌ Upload test failed")
        return
    
    # Test chat with new knowledge
    chat_success = test_chat_with_knowledge(token, persona_id)
    
    # Final result
    print("\n" + "=" * 50)
    if upload_success and chat_success:
        print("🎉 ALL TESTS PASSED! Real upload processing is working correctly.")
        print("   ✅ File upload and processing completed")
        print("   ✅ Knowledge integrated into chat system")
    else:
        print("❌ Some tests failed:")
        print(f"   Upload: {'✅' if upload_success else '❌'}")
        print(f"   Chat Integration: {'✅' if chat_success else '❌'}")

if __name__ == "__main__":
    main() 