import os
import asyncio
import json
from dotenv import load_dotenv
from services.pinecone_client import get_pinecone_client

load_dotenv()

async def upload_mock_data():
    try:
        # Load mock data
        with open("mock_pinecone_data.json", "r") as f:
            mock_data = json.load(f)
        
        # Get Pinecone client
        pinecone_client = get_pinecone_client()
        
        # Look for our test persona namespace
        namespace = "persona_550e8400-e29b-41d4-a716-446655440001"
        
        if namespace in mock_data:
            print(f"📦 Found mock data for namespace: {namespace}")
            
            vectors_data = mock_data[namespace]
            embeddings = []
            metadata_list = []
            ids = []
            
            for vector_id, vector_info in vectors_data.items():
                # Only use first 1536 values (OpenAI embedding dimension)
                embedding = vector_info["values"][:1536]
                
                # Pad with zeros if needed
                if len(embedding) < 1536:
                    embedding.extend([0.0] * (1536 - len(embedding)))
                
                embeddings.append(embedding)
                metadata_list.append(vector_info["metadata"])
                ids.append(vector_id)
            
            print(f"   Found {len(embeddings)} vectors to upload")
            
            # Upload to Pinecone
            result = await pinecone_client.upsert_vectors(
                namespace=namespace,
                embeddings=embeddings,
                metadata=metadata_list,
                ids=ids
            )
            
            print(f"✅ Uploaded {result['upserted_count']} vectors successfully")
            
            # Verify
            exists, count = await pinecone_client.check_namespace_exists(namespace)
            print(f"   Verification: Namespace exists={exists}, Vector count={count}")
        else:
            print(f"❌ No mock data found for namespace: {namespace}")
            print(f"   Available namespaces: {list(mock_data.keys())}")
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(upload_mock_data())
