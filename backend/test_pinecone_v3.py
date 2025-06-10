import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Try different import approaches
try:
    from pinecone import Pinecone
    print("✅ Imported from pinecone import Pinecone")
except:
    print("❌ Failed to import from pinecone import Pinecone")

try:
    import pinecone
    print("✅ Imported import pinecone")
except:
    print("❌ Failed to import pinecone")

# Test with correct initialization for v3
api_key = os.getenv("PINECONE_API_KEY")
print(f"\nAPI Key format check:")
print(f"- Starts with: {api_key[:3] if api_key else 'None'}")
print(f"- Length: {len(api_key) if api_key else 0}")

# Check if it's the right format for Pinecone v3
# v3 keys typically start with "pc-" or similar
if api_key and not api_key.startswith("pc-"):
    print("⚠️  Warning: API key doesn't start with 'pc-' which is typical for Pinecone v3 keys")

# Try initializing
try:
    from pinecone import Pinecone
    pc = Pinecone(api_key=api_key)
    print("\n✅ Pinecone client created")
    
    # Try to list indexes
    indexes = pc.list_indexes()
    print(f"✅ Successfully connected! Indexes: {indexes}")
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
