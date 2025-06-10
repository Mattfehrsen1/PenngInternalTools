import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_upload_flow():
    """Test the upload flow without Pinecone"""
    
    # Read test content
    with open("../test_upload.txt", "r") as f:
        content = f.read()
    
    print(f"1. Content loaded: {len(content)} characters")
    
    # Test chunking
    from services.chunker import TextChunker
    chunker = TextChunker(chunk_size=800, chunk_overlap=200)
    chunks = chunker.chunk_text(content, source="test.txt")
    print(f"2. Chunking: Created {len(chunks)} chunks")
    
    # Test embedding
    from services.embedder import Embedder
    embedder = Embedder()
    texts = [chunk["text"] for chunk in chunks]
    embeddings = await embedder.embed_documents(texts)
    print(f"3. Embeddings: Created {len(embeddings)} embeddings")
    print(f"   Embedding dimension: {len(embeddings[0])}")
    
    # Test database update (mock)
    print(f"4. Database: Would update persona with {len(chunks)} chunks")
    total_tokens = sum(chunk.get("token_count", 0) for chunk in chunks)
    print(f"   Total tokens: {total_tokens}")
    
    print("\n✅ All steps except Pinecone working correctly!")
    return chunks, embeddings

if __name__ == "__main__":
    chunks, embeddings = asyncio.run(test_upload_flow())
