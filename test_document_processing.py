#!/usr/bin/env python3
"""
Test script for document processing pipeline
Tests upload, chunking, embedding, and storage
"""
import asyncio
import httpx
import time
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

async def test_document_processing():
    """Test the complete document processing pipeline"""
    
    print("🧪 Testing Document Processing Pipeline")
    print("=" * 50)
    
    # API configuration
    base_url = "http://localhost:8000"
    
    # Test credentials
    username = "demo"
    password = "demo123"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login
        print("\n1. Logging in...")
        login_response = await client.post(
            f"{base_url}/auth/login",
            data={"username": username, "password": password}  # Form data, not JSON
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        auth_data = login_response.json()
        token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Logged in successfully")
        
        # 2. Get personas
        print("\n2. Getting personas...")
        personas_response = await client.get(
            f"{base_url}/personas/list",
            headers=headers
        )
        
        if personas_response.status_code != 200:
            print(f"❌ Failed to get personas: {personas_response.status_code}")
            return
        
        personas = personas_response.json()
        if not personas.get("personas"):
            print("❌ No personas found")
            return
        
        persona_list = personas["personas"]
        persona_id = persona_list[0]["id"]
        persona_name = persona_list[0]["name"]
        print(f"✅ Using persona: {persona_name} (ID: {persona_id})")
        
        # 3. Create test file
        print("\n3. Creating test file...")
        test_content = """
        This is a comprehensive test document for the Clone Advisor system.
        
        Chapter 1: Introduction
        The Clone Advisor system is designed to help users create AI clones of themselves or other personas.
        This involves uploading documents that contain knowledge and expertise that the AI should embody.
        
        Chapter 2: Document Processing
        When documents are uploaded, they go through several processing stages:
        - Text extraction from various file formats
        - Chunking into manageable segments
        - Generating embeddings using OpenAI's API
        - Storing embeddings in Pinecone vector database
        
        Chapter 3: Knowledge Retrieval
        Once processed, the knowledge becomes available for retrieval during chat conversations.
        The system uses semantic search to find relevant chunks based on user queries.
        
        Chapter 4: Testing
        This document serves as a test to ensure all parts of the pipeline are working correctly.
        We expect this to be chunked into multiple segments and stored successfully.
        
        Chapter 5: Conclusion
        A properly functioning document processing pipeline is essential for the Clone Advisor system.
        """
        
        # 4. Upload file
        print("\n4. Uploading test document...")
        files = [
            ("files", ("test_document.txt", test_content.encode(), "text/plain"))
        ]
        
        upload_response = await client.post(
            f"{base_url}/personas/{persona_id}/files",
            headers=headers,
            files=files
        )
        
        if upload_response.status_code != 201:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            return
        
        upload_data = upload_response.json()
        job_id = upload_data["id"]
        print(f"✅ Upload successful, job ID: {job_id}")
        
        # 5. Poll for completion
        print("\n5. Monitoring processing status...")
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            await asyncio.sleep(2)  # Wait 2 seconds between polls
            
            status_response = await client.get(
                f"{base_url}/personas/{persona_id}/files/{job_id}/status",
                headers=headers
            )
            
            if status_response.status_code != 200:
                print(f"❌ Status check failed: {status_response.status_code}")
                return
            
            status_data = status_response.json()
            progress = status_data.get("progress", 0)
            status = status_data.get("status", "unknown")
            message = status_data.get("message", "")
            
            print(f"   Progress: {progress}% - {message}")
            
            if status == "completed":
                chunks = status_data.get("chunks", 0)
                print(f"\n✅ Processing completed successfully!")
                print(f"   Created {chunks} chunks from the document")
                
                if chunks == 0:
                    print("\n⚠️  WARNING: 0 chunks created - processing may have failed")
                else:
                    print("\n🎉 SUCCESS: Document processed and chunks created!")
                
                return
            
            elif status == "failed":
                print(f"\n❌ Processing failed: {message}")
                return
            
            attempt += 1
        
        print("\n❌ Timeout: Processing did not complete within expected time")
        
        # 6. Check logs for debugging
        print("\n6. Checking backend logs for errors...")
        print("   (Check backend/server.log for detailed information)")

if __name__ == "__main__":
    asyncio.run(test_document_processing()) 