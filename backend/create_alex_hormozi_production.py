#!/usr/bin/env python3
"""
Create Alex Hormozi persona in production using authenticated API calls
"""

import requests
import json
import sys

def get_auth_token():
    """Get authentication token from production"""
    login_url = "https://clone-api.fly.dev/auth/login"
    response = requests.post(
        login_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="username=demo&password=demo123"
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None

def create_alex_hormozi_persona(token):
    """Create Alex Hormozi persona in production"""
    
    # Check if we can find a persona creation endpoint
    personas_url = "https://clone-api.fly.dev/api/personas"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Alex Hormozi persona data (based on our local data)
    persona_data = {
        "name": "Alex Hormozi",
        "description": "Business mentor and entrepreneur focused on helping people get rich through proven business strategies. Expert in gym ownership, customer acquisition, and scaling businesses.",
        "source_type": "business_mentor"
    }
    
    print("🎯 Creating Alex Hormozi persona in production...")
    print(f"📊 Data: {json.dumps(persona_data, indent=2)}")
    
    # Try to create persona
    response = requests.post(personas_url, headers=headers, json=persona_data)
    
    print(f"📡 Response Status: {response.status_code}")
    print(f"📋 Response: {response.text}")
    
    if response.status_code == 201:
        persona = response.json()
        print(f"✅ Created persona: {persona['id']}")
        print(f"🎭 Name: {persona['name']}")
        return persona['id']
    else:
        print(f"❌ Failed to create persona")
        print(f"   Status: {response.status_code}")
        print(f"   Error: {response.text}")
        
        # Try to understand the API structure
        print(f"\n🔍 Let's check what endpoints are available...")
        
        # Test different endpoints
        test_endpoints = [
            "/api/personas/create",
            "/api/create-persona", 
            "/api/personas/new"
        ]
        
        for endpoint in test_endpoints:
            test_url = f"https://clone-api.fly.dev{endpoint}"
            test_response = requests.post(test_url, headers=headers, json=persona_data)
            print(f"   {endpoint}: {test_response.status_code}")
            
        return None

def main():
    print("🚀 CREATING ALEX HORMOZI PERSONA IN PRODUCTION")
    print("=" * 50)
    
    # Step 1: Get authentication token
    print("🔐 Authenticating...")
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return
        
    print("✅ Authentication successful")
    
    # Step 2: Create persona
    persona_id = create_alex_hormozi_persona(token)
    
    if persona_id:
        print(f"\n🎉 SUCCESS!")
        print(f"📋 Persona ID: {persona_id}")
        print(f"🔗 Next steps:")
        print(f"   1. Upload documents to this persona")
        print(f"   2. Test webhook with: persona_id=\"{persona_id}\"")
        print(f"   3. Update ElevenLabs agent")
        
        # Test webhook with new persona
        webhook_test = {
            "function_name": "query_persona_knowledge",
            "parameters": {
                "query": "how to get rich",
                "persona_id": persona_id
            }
        }
        
        print(f"\n🧪 Webhook test command:")
        print(f'curl -X POST https://clone-api.fly.dev/elevenlabs/function-call \\')
        print(f'  -H "Content-Type: application/json" \\')
        print(f'  -H "X-Service-Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0" \\')
        print(f'  -d \'{json.dumps(webhook_test, indent=2)}\'')
        
    else:
        print(f"\n❌ Failed to create persona")
        print(f"💡 The API might not support persona creation yet")
        print(f"🔧 Alternative solutions:")
        print(f"   1. Use ngrok tunnel to local system")
        print(f"   2. Add persona creation endpoint to production")
        print(f"   3. Direct database insertion")

if __name__ == "__main__":
    main() 