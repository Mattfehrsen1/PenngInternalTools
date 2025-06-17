#!/usr/bin/env python3
"""Check what tables exist in the database"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)
with engine.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
    tables = [row[0] for row in result]
    
    print("Available tables:")
    for table in sorted(tables):
        print(f"  - {table}")
    
    # Show personas table structure
    if 'personas' in tables:
        print(f"\nPersonas table columns:")
        result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'personas'"))
        for row in result:
            print(f"  - {row[0]}: {row[1]}") 