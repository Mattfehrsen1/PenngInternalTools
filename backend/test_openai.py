import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment
load_dotenv()

async def test_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"OpenAI API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"Key length: {len(api_key)}")
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        print("✅ OpenAI client created")
        
        # Test embedding
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=["Hello world"]
        )
        
        embedding = response.data[0].embedding
        print(f"✅ Embedding created! Dimension: {len(embedding)}")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_openai())
