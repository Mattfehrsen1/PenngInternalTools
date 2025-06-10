import os
import asyncio
import json
from dotenv import load_dotenv
from services.pinecone_client import get_pinecone_client

load_dotenv()

async def add_hormozi_content():
    try:
        # Get Pinecone client
        pinecone_client = get_pinecone_client()
        
        # Our test persona namespace
        namespace = "persona_550e8400-e29b-41d4-a716-446655440001"
        
        # Load the Alex Hormozi content from mock data
        with open("mock_pinecone_data.json", "r") as f:
            mock_data = json.load(f)
        
        # Get the Hormozi content from the first persona
        hormozi_data = mock_data["persona_6025fc73-5182-46e1-9350-a4b4230e784c"]
        
        embeddings = []
        metadata_list = []
        ids = []
        
        for vector_id, vector_info in hormozi_data.items():
            # Use first 1536 values
            embedding = vector_info["values"][:1536]
            
            # Pad with zeros if needed
            if len(embedding) < 1536:
                embedding.extend([0.0] * (1536 - len(embedding)))
            
            # Update metadata to match our persona
            metadata = vector_info["metadata"].copy()
            metadata["persona_id"] = "550e8400-e29b-41d4-a716-446655440001"
            
            embeddings.append(embedding)
            metadata_list.append(metadata)
            # Use new IDs for our namespace
            ids.append(f"hormozi_chunk_{len(ids)}")
        
        print(f"📦 Adding {len(embeddings)} Alex Hormozi content vectors...")
        
        # Upload to Pinecone
        result = await pinecone_client.upsert_vectors(
            namespace=namespace,
            embeddings=embeddings,
            metadata=metadata_list,
            ids=ids
        )
        
        print(f"✅ Uploaded {result['upserted_count']} vectors successfully")
        
        # Wait for consistency
        await asyncio.sleep(2)
        
        # Verify
        exists, count = await pinecone_client.check_namespace_exists(namespace)
        print(f"   Verification: Namespace exists={exists}, Vector count={count}")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_hormozi_content())
