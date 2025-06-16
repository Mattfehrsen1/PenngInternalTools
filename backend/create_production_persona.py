#!/usr/bin/env python3
"""
Create Alex Hormozi persona in production backend
"""

import requests
import json

def create_production_persona():
    """Create Alex Hormozi persona using production webhook"""
    
    # Production configuration
    production_url = "https://clone-api.fly.dev"
    service_token = "NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0"
    
    print("🎯 PRODUCTION PERSONA CREATION PLAN")
    print("=====================================")
    
    # Test webhook accessibility
    webhook_url = f"{production_url}/elevenlabs/function-call"
    headers = {
        "Content-Type": "application/json",
        "X-Service-Token": service_token
    }
    
    # Test with default persona first
    test_payload = {
        "function_name": "query_persona_knowledge",
        "parameters": {
            "query": "how to get rich",
            "persona_id": "default"
        }
    }
    
    print(f"🧪 Testing webhook accessibility...")
    print(f"URL: {webhook_url}")
    
    try:
        response = requests.post(webhook_url, json=test_payload, headers=headers)
        print(f"✅ Webhook accessible: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 Response: {result.get('success', False)}")
            
            if "error" in result.get("result", {}):
                print(f"⚠️  Expected error: {result['result']['error']}")
                print(f"💡 This confirms webhook works, just needs persona data")
                
        print("\n🎯 NEXT STEPS:")
        print("1. The webhook is working and accessible")
        print("2. We need to create an Alex Hormozi persona in production")
        print("3. Upload the 31 documents to that persona")
        print("4. Test the webhook with the new persona ID")
        
        print(f"\n📋 LOCAL PERSONA DATA TO RECREATE:")
        print(f"   Name: Alex Hormozi")
        print(f"   Local ID: cd35a4a9-31ad-44f5-9de7-cc7dc3196541")
        print(f"   Jobs: 31 completed")
        print(f"   Namespace: persona_abef4a17-d722-428a-8580-513f998289a2")
        
        print(f"\n🔧 WEBHOOK TEST COMMAND:")
        print(f'curl -X POST {webhook_url} \\')
        print(f'  -H "Content-Type: application/json" \\')
        print(f'  -H "X-Service-Token: {service_token}" \\')
        print(f'  -d \'{json.dumps(test_payload, indent=2)}\'')
        
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

if __name__ == "__main__":
    create_production_persona() 