#!/usr/bin/env python3
"""Check which Alex Hormozi persona has the most knowledge"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id, name, chunk_count, description, created_at 
        FROM personas 
        WHERE name ILIKE '%alex%' AND name ILIKE '%hormozi%'
        ORDER BY chunk_count DESC, created_at DESC
    """))
    
    print("Alex Hormozi personas:")
    for row in result:
        print(f"  - {row[1]} ({row[0][:8]}...)")
        print(f"    Chunks: {row[2] or 0}")
        print(f"    Description: {row[3] or 'None'}")
        print(f"    Created: {row[4]}")
        print() 