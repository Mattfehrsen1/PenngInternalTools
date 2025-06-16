#!/usr/bin/env python3
"""Check environment configuration for document processing"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / "backend" / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print(f"⚠️  No .env file found at: {env_path}")

print("\n🔍 Checking Environment Variables:")
print("=" * 50)

# Check critical environment variables
env_vars = {
    "OPENAI_API_KEY": "Required for text embeddings",
    "PINECONE_API_KEY": "Required for vector storage (or uses mock)",
    "DATABASE_URL": "PostgreSQL connection string",
    "JWT_SECRET_KEY": "Authentication secret",
}

all_good = True
for var, description in env_vars.items():
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if "KEY" in var or "SECRET" in var:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✅ {var}: SET ({masked})")
        else:
            print(f"✅ {var}: {value[:50]}...")
    else:
        print(f"❌ {var}: NOT SET - {description}")
        all_good = False

print("\n📊 Summary:")
if all_good:
    print("✅ All critical environment variables are set!")
else:
    print("⚠️  Some environment variables are missing.")
    print("   The system may use mock services for missing components.")

# Check if mock_pinecone_data.json exists
mock_file = Path(__file__).parent / "backend" / "mock_pinecone_data.json"
if mock_file.exists():
    print(f"\n📁 Mock Pinecone data file exists: {mock_file}")
    print("   The system is using mock vector storage.") 