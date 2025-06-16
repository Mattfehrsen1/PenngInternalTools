#!/usr/bin/env python3
"""
Add more Alex Hormozi content to the existing production persona
"""

import requests
import json

def add_more_content():
    """Add more Alex Hormozi business knowledge"""
    
    # Get auth token
    login_url = "https://clone-api.fly.dev/auth/login"
    response = requests.post(
        login_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="username=demo&password=demo123"
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
        
    token = response.json()["access_token"]
    persona_id = "3bb69586-e59b-43a6-a067-61730d7c0f3a"  # Your Alex Hormozi persona
    
    # More Alex Hormozi content
    business_content = """
    Alex Hormozi's Business Principles:

    1. The Grand Slam Offer Framework:
    - Make your offer so good people feel stupid saying no
    - Stack value until the perceived value far exceeds the price
    - Remove all risk with strong guarantees
    - Create urgency and scarcity

    2. Customer Acquisition:
    - Focus on lifetime value, not just initial purchase
    - Test multiple marketing channels simultaneously
    - Track metrics religiously: CAC, LTV, conversion rates
    - Double down on what works, kill what doesn't

    3. Scaling Businesses:
    - Systemize everything before you scale
    - Hire for character, train for skill
    - Create playbooks for every process
    - Focus on cash flow, not just revenue

    4. Pricing Strategy:
    - Price based on value, not cost
    - Use price anchoring to make offers seem reasonable
    - Bundle complementary services for higher perceived value
    - Test price increases regularly

    5. Sales Psychology:
    - People buy emotionally and justify logically
    - Address objections before they arise
    - Use social proof and testimonials strategically
    - Create a sense of urgency without being pushy
    """
    
    # Upload additional content
    upload_url = f"https://clone-api.fly.dev/api/personas/{persona_id}/upload-direct"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    files = {
        'file': ('hormozi_advanced.txt', business_content, 'text/plain')
    }
    
    print("📤 Uploading additional Alex Hormozi content...")
    response = requests.post(upload_url, headers=headers, files=files)
    
    print(f"📡 Status: {response.status_code}")
    print(f"📋 Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Successfully added more content!")
        print("🔄 The content is processing in the background")
        print("⏱️  Wait 30-60 seconds then test the webhook again")
    else:
        print("❌ Upload failed")

if __name__ == "__main__":
    add_more_content() 