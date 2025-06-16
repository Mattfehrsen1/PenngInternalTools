#!/usr/bin/env python3
"""
Test script for the new bulletproof upload system.
This script tests the direct upload endpoints without using the broken queue system.
"""

import requests
import time
import os
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"

# Test files content
TEST_TXT_CONTENT = """This is a test document for the new upload system.
It contains some sample text that will be chunked and embedded.
The new system processes files directly without using queues.
This ensures reliability and immediate feedback."""

TEST_PDF_PATH = None  # We'll use text files for testing

def login():
    """Login and get auth token"""
    print("🔐 Logging in...")
    response = requests.post(f"{API_URL}/auth/login", data={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None
    
    token = response.json()["access_token"]
    print("✅ Login successful")
    return token

def create_test_persona(token):
    """Create a test persona"""
    print("\n📚 Creating test persona...")
    
    response = requests.post(
        f"{API_URL}/persona/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "name": "Test Upload System",
            "description": "Testing the new bulletproof upload system",
            "text": "Initial content for the test persona"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create persona: {response.status_code}")
        print(response.text)
        return None
    
    persona_data = response.json()
    print(f"✅ Created persona: {persona_data['name']} (ID: {persona_data['persona_id']})")
    return persona_data['persona_id']

def test_direct_upload(token, persona_id):
    """Test the new direct upload endpoint"""
    print(f"\n📤 Testing direct upload to persona {persona_id}...")
    
    # Create a test file
    test_file = ("test_document.txt", TEST_TXT_CONTENT, "text/plain")
    
    response = requests.post(
        f"{API_URL}/persona/{persona_id}/upload-direct",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": test_file}
    )
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return None
    
    upload_data = response.json()
    print(f"✅ Upload started: {upload_data['message']}")
    print(f"   Job ID: {upload_data['job_id']}")
    return upload_data['job_id']

def check_upload_progress(token, job_id):
    """Poll for upload progress"""
    print(f"\n📊 Checking progress for job {job_id}...")
    
    max_attempts = 30  # 30 seconds timeout
    for i in range(max_attempts):
        response = requests.get(
            f"{API_URL}/persona/upload-progress/{job_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get progress: {response.status_code}")
            return False
        
        progress_data = response.json()
        status = progress_data['status']
        progress = progress_data['progress']
        
        print(f"   Status: {status} | Progress: {progress}%", end="")
        
        if status == 'completed':
            print(f"\n✅ Upload completed! Created {progress_data.get('chunks', 'N/A')} chunks")
            return True
        elif status == 'failed':
            print(f"\n❌ Upload failed: {progress_data.get('error', 'Unknown error')}")
            return False
        
        print(" (checking again...)", end="\r")
        time.sleep(1)
    
    print("\n⏱️ Upload timed out")
    return False

def test_multiple_files(token, persona_id):
    """Test uploading multiple files sequentially"""
    print(f"\n📤 Testing multiple file uploads...")
    
    test_files = [
        ("document1.txt", "This is the first test document with some content.", "text/plain"),
        ("document2.txt", "This is the second test document with different content.", "text/plain"),
        ("document3.txt", "This is the third test document with even more content.", "text/plain"),
    ]
    
    for filename, content, content_type in test_files:
        print(f"\n   Uploading {filename}...")
        
        response = requests.post(
            f"{API_URL}/persona/{persona_id}/upload-direct",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (filename, content, content_type)}
        )
        
        if response.status_code == 200:
            job_id = response.json()['job_id']
            success = check_upload_progress(token, job_id)
            if not success:
                print(f"   ❌ Failed to upload {filename}")
        else:
            print(f"   ❌ Upload request failed for {filename}: {response.status_code}")

def main():
    """Run all tests"""
    print("🚀 Testing New Bulletproof Upload System")
    print("=" * 50)
    
    # Login
    token = login()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    # Create test persona
    persona_id = create_test_persona(token)
    if not persona_id:
        print("\n❌ Cannot proceed without a persona")
        return
    
    # Test single file upload
    job_id = test_direct_upload(token, persona_id)
    if job_id:
        check_upload_progress(token, job_id)
    
    # Test multiple files
    test_multiple_files(token, persona_id)
    
    print("\n✨ Test completed!")
    print(f"   Visit http://localhost:3000/upload to test the UI")
    print(f"   Or go to http://localhost:3000/fullchat to chat with the uploaded content")

if __name__ == "__main__":
    main() 