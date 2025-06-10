import os
from dotenv import load_dotenv
from services.chunker import TextChunker

# Load environment
load_dotenv()

# Read test file
with open("../test_upload.txt", "r") as f:
    content = f.read()

print(f"Content length: {len(content)} characters")

# Test chunker
chunker = TextChunker(
    chunk_size=int(os.getenv("CHUNK_SIZE_TOKENS", "800")),
    chunk_overlap=int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))
)

chunks = chunker.chunk_text(content, source="test_upload.txt")
print(f"Created {len(chunks)} chunks")

if chunks:
    print("\nFirst chunk:")
    print(f"- Text length: {len(chunks[0]['text'])}")
    print(f"- Token count: {chunks[0].get('token_count', 'N/A')}")
    print(f"- Text preview: {chunks[0]['text'][:100]}...")
    print(f"- Metadata: {chunks[0]}")
else:
    print("No chunks created!")
