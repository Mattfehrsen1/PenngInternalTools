#!/usr/bin/env python3
"""
Debug script to test upload processing step by step
"""

import asyncio
import base64
from services.ingestion_worker import process_ingestion_job
from services.chunker import TextChunker
from services.embedder import Embedder

async def debug_upload_processing():
    """Debug the upload processing pipeline"""
    
    print("🔍 Debug: Testing upload processing pipeline")
    
    # Test data
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
    """
    
    # Encode as base64 like the real system
    encoded_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
    
    files_data = [{
        'filename': 'debug_test.txt',
        'content': encoded_content,
        'type': 'text',
        'size': len(test_content)
    }]
    
    # Test parameters
    job_id = "debug-job-123"
    persona_id = "cd35a4a9-31ad-44f5-9de7-cc7dc3196541"  # Alex Hormozi
    
    print(f"📝 Test content length: {len(test_content)} chars")
    print(f"📦 Encoded content length: {len(encoded_content)} chars")
    
    # Test chunker directly
    print("\n🔧 Testing chunker...")
    chunker = TextChunker()
    chunks = chunker.chunk_text(test_content, source="debug_test.txt")
    print(f"✅ Chunker created {len(chunks)} chunks")
    if chunks:
        print(f"   First chunk: {chunks[0]['text'][:100]}...")
    
    # Test embedder directly
    print("\n🔧 Testing embedder...")
    try:
        embedder = Embedder()
        if chunks:
            texts = [chunk['text'] for chunk in chunks[:1]]  # Test just first chunk
            embeddings = await embedder.embed_documents(texts)
            print(f"✅ Embedder created {len(embeddings)} embeddings")
            print(f"   Embedding dimension: {len(embeddings[0])}")
        else:
            print("❌ No chunks to embed")
    except Exception as e:
        print(f"❌ Embedder error: {e}")
    
    # Test full processing pipeline
    print("\n🔧 Testing full processing pipeline...")
    try:
        result = await process_ingestion_job(job_id, persona_id, files_data)
        print(f"✅ Processing result: {result}")
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_upload_processing()) 