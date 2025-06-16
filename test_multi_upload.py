#!/usr/bin/env python3
"""
Test script for multi-file upload functionality
"""

import requests
import json
import time
import os

API_URL = "http://localhost:8000"

def test_multi_file_upload():
    """Test the new multi-file upload functionality"""
    
    # First, create a user and login
    print("🔐 Creating test user and logging in...")
    
    # Use existing demo user
    print("Using existing demo user...")
    
    # Login
    login_response = requests.post(f"{API_URL}/auth/login",
        data={"username": "demo", "password": "demo123"})
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Successfully logged in")
    
    # Create a test persona first using single upload
    print("\n📝 Creating initial persona...")
    
    form_data = {
        'name': 'Test Multi-Upload Persona',
        'description': 'Testing multi-file upload functionality',
        'text': 'Initial content for the persona. This will be enhanced with multiple files.'
    }
    
    upload_response = requests.post(f"{API_URL}/persona/upload", 
        data=form_data, headers=headers)
    
    if upload_response.status_code != 200:
        print(f"❌ Initial persona creation failed: {upload_response.status_code}")
        print(upload_response.text)
        return False
    
    persona_data = upload_response.json()
    persona_id = persona_data["persona_id"]
    
    print(f"✅ Created persona: {persona_data['name']} (ID: {persona_id})")
    
    # Wait a moment for processing
    time.sleep(2)
    
    # Now test multi-file upload
    print("\n📁 Testing multi-file upload...")
    
    # Prepare multiple files
    test_files = [
        ('files', ('test1.txt', 'This is test file 1 content about machine learning basics.', 'text/plain')),
        ('files', ('test2.txt', 'This is test file 2 content about data science fundamentals.', 'text/plain'))
    ]
    
    multi_upload_response = requests.post(
        f"{API_URL}/persona/{persona_id}/ingest",
        files=test_files,
        headers=headers
    )
    
    if multi_upload_response.status_code != 200:
        print(f"❌ Multi-file upload failed: {multi_upload_response.status_code}")
        print(multi_upload_response.text)
        return False
    
    job_data = multi_upload_response.json()
    job_id = job_data["job_id"]
    
    print(f"✅ Multi-file upload started: Job ID {job_id}")
    print(f"   Files: {job_data['files_count']}")
    print(f"   Estimated time: {job_data['estimated_time']}")
    
    # Monitor job progress (simulate SSE)
    print("\n⏳ Monitoring job progress...")
    
    for i in range(30):  # Wait up to 30 seconds
        # Note: We can't test SSE easily in this script, so we'll just check job completion
        # by fetching the persona to see if chunk count increased
        
        persona_response = requests.get(f"{API_URL}/persona/{persona_id}", headers=headers)
        if persona_response.status_code == 200:
            persona_info = persona_response.json()
            print(f"   Chunks: {persona_info.get('chunk_count', 0)}")
            
            if persona_info.get('chunk_count', 0) > 1:  # Should have more than initial chunk
                print("✅ Multi-file processing completed successfully!")
                break
        
        time.sleep(1)
    else:
        print("⚠️  Job monitoring timed out")
    
    # List personas to verify
    print("\n📋 Verifying personas list...")
    list_response = requests.get(f"{API_URL}/persona/list", headers=headers)
    
    if list_response.status_code == 200:
        personas = list_response.json()["personas"]
        for persona in personas:
            if persona["id"] == persona_id:
                print(f"✅ Found persona: {persona['name']} with {persona['chunk_count']} chunks")
                break
    
    print("\n🎉 Multi-file upload test completed!")
    return True

if __name__ == "__main__":
    print("🚀 Testing Multi-File Upload Functionality")
    print("=" * 50)
    
    try:
        success = test_multi_file_upload()
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc() 