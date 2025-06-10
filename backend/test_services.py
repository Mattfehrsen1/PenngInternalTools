import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_services():
    try:
        # Test Chunker
        from services.chunker import TextChunker
        chunker = TextChunker(chunk_size=800, chunk_overlap=200)
        test_text = "This is a test. " * 100
        chunks = chunker.chunk_text(test_text)
        print(f"✅ Chunker: Created {len(chunks)} chunks")
        
        # Test Embedder
        from services.embedder import Embedder
        embedder = Embedder()
        test_texts = ["Hello world", "This is a test"]
        embeddings = await embedder.embed_documents(test_texts)
        print(f"✅ Embedder: Created {len(embeddings)} embeddings of dimension {len(embeddings[0])}")
        
        # Test Pinecone
        from services.pinecone_client import get_pinecone_client
        pc_client = get_pinecone_client()
        print(f"✅ Pinecone: Client initialized successfully")
        
        # Test namespace operations
        test_namespace = "test_namespace_delete_me"
        result = await pc_client.upsert_vectors(
            namespace=test_namespace,
            embeddings=embeddings,
            metadata=[{"text": t} for t in test_texts],
            ids=["test1", "test2"]
        )
        print(f"✅ Pinecone Upsert: {result}")
        
        # Test search
        search_results = await pc_client.similarity_search(
            namespace=test_namespace,
            query_vector=embeddings[0],
            k=2
        )
        print(f"✅ Pinecone Search: Found {len(search_results)} results")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_services())
