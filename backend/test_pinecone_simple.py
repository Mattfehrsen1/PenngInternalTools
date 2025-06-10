import os
from dotenv import load_dotenv
import pinecone

# Load environment
load_dotenv()

api_key = os.getenv("PINECONE_API_KEY")
print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
print(f"Key length: {len(api_key)}")

try:
    # Test Pinecone initialization
    pc = pinecone.Pinecone(api_key=api_key)
    print("✅ Pinecone client initialized")
    
    # List indexes
    indexes = pc.list_indexes()
    print(f"✅ Listed indexes: {indexes}")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    
# Also test with environment variable directly
print("\nTesting with environment='gcp-starter'...")
try:
    pc2 = pinecone.Pinecone(
        api_key=api_key,
        environment="gcp-starter"  # Try different environment
    )
    indexes2 = pc2.list_indexes()
    print(f"✅ With gcp-starter: {indexes2}")
except Exception as e:
    print(f"❌ Error with gcp-starter: {type(e).__name__}: {str(e)}")
