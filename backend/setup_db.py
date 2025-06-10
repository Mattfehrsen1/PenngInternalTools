#!/usr/bin/env python3
"""
Database setup script to create tables and demo user
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/cloneadvisor")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def setup_database():
    """Create tables and demo user"""
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Create personas table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS personas (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                description TEXT,
                source_type VARCHAR NOT NULL,
                source_filename VARCHAR,
                namespace VARCHAR UNIQUE NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                extra_metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            );
        ''')
        
        # Create usage_logs table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                persona_id VARCHAR,
                action VARCHAR NOT NULL,
                model VARCHAR,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cost_usd INTEGER DEFAULT 0,
                extra_metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        ''')
        
        # Create users table (for authentication)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL,
                email VARCHAR UNIQUE,
                hashed_password VARCHAR NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        ''')
        
        # Create demo user
        demo_password_hash = pwd_context.hash("demo123")
        
        # Check if demo user exists
        existing_user = await conn.fetchrow("SELECT id FROM users WHERE username = 'demo'")
        
        if not existing_user:
            await conn.execute('''
                INSERT INTO users (id, username, email, hashed_password, is_active)
                VALUES ($1, $2, $3, $4, $5)
            ''', "demo-user-id", "demo", "demo@example.com", demo_password_hash, True)
            print("✅ Demo user created successfully!")
        else:
            print("✅ Demo user already exists!")
        
        # Create indexes
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_personas_user_id ON personas(user_id);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);')
        
        await conn.close()
        print("✅ Database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_database())
