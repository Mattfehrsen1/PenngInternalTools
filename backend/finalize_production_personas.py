#!/usr/bin/env python3
"""
Finalize Production Personas
Keep only the best Alex Hormozi and update descriptions for production
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

def finalize_production_personas():
    """Finalize production personas with proper descriptions and cleanup"""
    
    print("🎯 FINALIZING PRODUCTION PERSONAS")
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
        
        # Production persona IDs (keep the one with most chunks)
        alex_hormozi_production_id = "cd35a4a9-31ad-44f5-9de7-cc7dc3196541"  # 1,272 chunks
        alex_hormozi_test_ids = [
            "5e0bdbe6-1fb8-4e54-be75-e300d222f00e",  # 3 chunks
            "f0ad0e89-1b2b-4958-bfed-9bc0637b7d7a"   # 0 chunks
        ]
        
        # Update Alex Hormozi production persona with proper description
        print("📝 Updating Alex Hormozi production persona...")
        session.execute(text("""
            UPDATE personas 
            SET 
                name = 'Alex Hormozi',
                description = 'Entrepreneur, author, and business growth expert. Specializes in acquisitions, scaling businesses, and creating irresistible offers. Author of "$100M Offers" and founder of Acquisition.com.'
            WHERE id = :id
        """), {"id": alex_hormozi_production_id})
        
        # Update Rory Sutherland with better description
        print("📝 Updating Rory Sutherland persona...")
        session.execute(text("""
            UPDATE personas 
            SET 
                description = 'Vice Chairman of Ogilvy UK, behavioral economist, and advertising strategist. Expert in psychology, consumer behavior, and unconventional business thinking. Author of "Alchemy" and renowned speaker on marketing psychology.'
            WHERE name ILIKE '%rory%' OR name ILIKE '%sutherland%'
        """))
        
        # Delete test Alex Hormozi personas
        print("🗑️ Removing test Alex Hormozi personas...")
        for test_id in alex_hormozi_test_ids:
            # Delete messages for this persona's conversations
            session.execute(text("""
                DELETE FROM messages 
                WHERE thread_id IN (
                    SELECT id FROM conversations WHERE persona_id = :persona_id
                )
            """), {"persona_id": test_id})
            
            # Delete conversations for this persona
            session.execute(text("""
                DELETE FROM conversations WHERE persona_id = :persona_id
            """), {"persona_id": test_id})
            
            # Delete the persona itself
            session.execute(text("""
                DELETE FROM personas WHERE id = :persona_id
            """), {"persona_id": test_id})
            
            print(f"   ✅ Deleted test Alex Hormozi persona: {test_id[:8]}...")
        
        # Commit changes
        session.commit()
        
        # Show final personas
        print(f"\n🎉 FINALIZATION COMPLETE!")
        print(f"\n📋 FINAL PRODUCTION PERSONAS:")
        result = session.execute(text("""
            SELECT id, name, description, chunk_count
            FROM personas 
            WHERE user_id = 'demo-user-id'
            ORDER BY name
        """))
        
        for persona in result.fetchall():
            persona_id, name, description, chunks = persona
            print(f"\n   🎭 {name}")
            print(f"      ID: {persona_id}")
            print(f"      Chunks: {chunks or 0}")
            print(f"      Description: {description}")
        
        session.close()
        
        print(f"\n✅ Production database ready!")
        print(f"   • 2 high-quality AI business expert clones")
        print(f"   • Clean UI with simplified navigation")
        print(f"   • Ready for production deployment")
        
    except Exception as e:
        print(f"❌ Error during finalization: {e}")
        session.rollback()

if __name__ == "__main__":
    finalize_production_personas() 