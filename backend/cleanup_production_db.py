#!/usr/bin/env python3
"""
Production Database Cleanup
Remove all test personas and keep only Alex Hormozi and Rory Sutherland
"""

import asyncio
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

def cleanup_production_database():
    """Clean up database for production - keep only Alex Hormozi and Rory Sutherland"""
    
    print("🧹 PRODUCTION DATABASE CLEANUP")
    print("=" * 50)
    
    # Database connection
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ No DATABASE_URL found in environment")
        return
    
    # Convert postgres:// to postgresql:// if needed
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Production personas to keep (using actual IDs from database)
        alex_hormozi_id = "cd35a4a9-31ad-44f5-9de7-cc7dc3196541"  # Alex Hormozi from database
        rory_sutherland_id = "ecaef512-e7b6-4f68-a947-7e1b2c8d3e4f"  # Rory Sutherland (exists)
        
        # List current personas
        print("📋 Current personas in database:")
        result = session.execute(text("""
            SELECT id, name, description, created_at
            FROM personas 
            WHERE user_id = 'demo-user-id'
            ORDER BY created_at DESC
        """))
        
        personas = result.fetchall()
        print(f"Found {len(personas)} personas")
        
        # Show which personas will be kept vs deleted
        personas_to_keep = []
        personas_to_delete = []
        
        for persona in personas:
            persona_id, name, description, created_at = persona
            if persona_id == alex_hormozi_id or "alex" in name.lower() and "hormozi" in name.lower():
                personas_to_keep.append((persona_id, name, "Alex Hormozi - Production Ready"))
            elif persona_id == rory_sutherland_id or "rory" in name.lower() or "sutherland" in name.lower():
                personas_to_keep.append((persona_id, name, "Rory Sutherland - Keep"))
            else:
                personas_to_delete.append((persona_id, name, "Test persona - Delete"))
        
        print(f"\n✅ PERSONAS TO KEEP ({len(personas_to_keep)}):")
        for persona_id, name, reason in personas_to_keep:
            print(f"   • {name} ({persona_id[:8]}...) - {reason}")
        
        print(f"\n❌ PERSONAS TO DELETE ({len(personas_to_delete)}):")
        for persona_id, name, reason in personas_to_delete:
            print(f"   • {name} ({persona_id[:8]}...) - {reason}")
        
        # Confirmation
        print(f"\n⚠️ This will DELETE {len(personas_to_delete)} test personas")
        print("   Only Alex Hormozi and Rory Sutherland will remain")
        
        # Get user confirmation
        response = input("\nProceed with cleanup? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Cleanup cancelled")
            return
        
        # Delete conversations and messages for test personas first
        print("\n🗑️ Cleaning up conversations and messages...")
        for persona_id, name, _ in personas_to_delete:
            # Delete messages for this persona's conversations
            session.execute(text("""
                DELETE FROM messages 
                WHERE thread_id IN (
                    SELECT id FROM conversations WHERE persona_id = :persona_id
                )
            """), {"persona_id": persona_id})
            
            # Delete conversations for this persona
            session.execute(text("""
                DELETE FROM conversations WHERE persona_id = :persona_id
            """), {"persona_id": persona_id})
            
            # Delete the persona itself (no separate documents table)
            session.execute(text("""
                DELETE FROM personas WHERE id = :persona_id
            """), {"persona_id": persona_id})
            
            print(f"   ✅ Deleted {name}")
        
        # Create Rory Sutherland persona if it doesn't exist
        rory_exists = session.execute(text("""
            SELECT COUNT(*) FROM personas 
            WHERE name ILIKE '%rory%' OR name ILIKE '%sutherland%'
        """)).scalar()
        
        if rory_exists == 0:
            print("\n👤 Creating Rory Sutherland persona...")
            session.execute(text("""
                INSERT INTO personas (id, user_id, name, description, created_at, updated_at)
                VALUES (
                    :id, 
                    'demo-user-id', 
                    'Rory Sutherland',
                    'Behavioral economist and advertising guru, known for his insights into psychology, consumer behavior, and unconventional business thinking.',
                    NOW(),
                    NOW()
                )
            """), {"id": rory_sutherland_id})
            print(f"   ✅ Created Rory Sutherland persona: {rory_sutherland_id}")
        
        # Commit changes
        session.commit()
        
        # Final count
        final_count = session.execute(text("""
            SELECT COUNT(*) FROM personas WHERE user_id = 'demo-user-id'
        """)).scalar()
        
        print(f"\n🎉 CLEANUP COMPLETE!")
        print(f"   • Deleted {len(personas_to_delete)} test personas")
        print(f"   • Kept {final_count} production personas")
        print(f"   • Database ready for production use")
        
        # Show final personas
        print(f"\n📋 FINAL PERSONAS:")
        result = session.execute(text("""
            SELECT id, name, description
            FROM personas 
            WHERE user_id = 'demo-user-id'
            ORDER BY name
        """))
        
        for persona in result.fetchall():
            persona_id, name, description = persona
            print(f"   • {name} ({persona_id})")
            print(f"     {description}")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        session.rollback()

if __name__ == "__main__":
    cleanup_production_database() 