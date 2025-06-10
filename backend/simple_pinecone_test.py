import os
import pinecone
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("PINECONE_API_KEY")
print(f"API Key: {api_key[:10]}...{api_key[-4:]}")

try:
    # Initialize Pinecone
    pc = pinecone.Pinecone(api_key=api_key)
    print("✅ Pinecone client initialized")
    
    # Get index
    index = pc.Index("clone-advisor")
    print("✅ Connected to index: clone-advisor")
    
    # Check stats
    stats = index.describe_index_stats()
    print(f"\n📊 Index stats:")
    print(f"  Total vectors: {stats.total_vector_count}")
    print(f"  Dimension: {stats.dimension}")
    print(f"  Namespaces: {list(stats.namespaces.keys())}")
    
    # Check if our namespace exists
    namespace = "persona_550e8400-e29b-41d4-a716-446655440001"
    if namespace in stats.namespaces:
        print(f"\n✅ Namespace '{namespace}' exists!")
        print(f"   Vector count: {stats.namespaces[namespace]['vector_count']}")
    else:
        print(f"\n❌ Namespace '{namespace}' not found")
        
        # Try to create some test data
        print("\n📤 Uploading test vector...")
        test_vector = [0.1] * 1536  # Create a 1536-dim vector
        
        response = index.upsert(
            vectors=[{
                "id": "test_vector_1",
                "values": test_vector,
                "metadata": {
                    "text": "This is a test document for the Clone Advisor system.",
                    "source": "test.txt",
                    "chunk_id": 0
                }
            }],
            namespace=namespace
        )
        print(f"   Upserted: {response}")
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
