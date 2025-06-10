import os
import asyncio
from dotenv import load_dotenv
from services.pinecone_client import get_pinecone_client

load_dotenv()

async def check_pinecone_data():
    try:
        # Get Pinecone client
        pinecone_client = get_pinecone_client()
        
        # Check namespace for our test persona
        namespace = "persona_550e8400-e29b-41d4-a716-446655440001"
        
        # Check if namespace exists
        exists, vector_count = await pinecone_client.check_namespace_exists(namespace)
        
        print(f"✅ Pinecone Status:")
        print(f"   Namespace: {namespace}")
        print(f"   Exists: {exists}")
        print(f"   Vector count: {vector_count}")
        
        if exists and vector_count > 0:
            # Try a sample query
            print("\n📊 Testing similarity search...")
            # Create a dummy embedding (1536 dimensions for OpenAI)
            dummy_embedding = [0.1] * 1536
            
            results = await pinecone_client.similarity_search(
                namespace=namespace,
                query_embedding=dummy_embedding,
                k=3
            )
            
            print(f"   Found {len(results)} results")
            for i, result in enumerate(results):
                print(f"\n   Result {i+1}:")
                print(f"     ID: {result['id']}")
                print(f"     Score: {result['score']:.3f}")
                print(f"     Text preview: {result['metadata'].get('text', '')[:100]}...")
        
        # Check index stats
        print("\n📈 Index stats:")
        stats = pinecone_client.index.describe_index_stats()
        print(f"   Total vectors: {stats.total_vector_count}")
        print(f"   Dimension: {stats.dimension}")
        print(f"   Namespaces: {list(stats.namespaces.keys())}")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(check_pinecone_data())
