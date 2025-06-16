#!/usr/bin/env python3
"""
Update all personas without agent IDs to use the working ElevenLabs agent
"""

import asyncio
from sqlalchemy import create_engine, text
from database import DATABASE_URL
import os

def update_all_personas_agent_id():
    """Update all personas without agent IDs"""
    
    # Create synchronous engine for this script
    engine = create_engine(
        DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    )
    
    agent_id = "agent_01jxmeyxz2fh0v3cqx848qk1e0"
    
    try:
        with engine.connect() as conn:
            # Get all personas without agent IDs
            result = conn.execute(text("""
                SELECT id, name FROM personas 
                WHERE elevenlabs_agent_id IS NULL
                ORDER BY created_at;
            """))
            
            personas_without_agents = result.fetchall()
            
            if not personas_without_agents:
                print("✅ All personas already have agent IDs!")
                return
            
            print(f"📝 Found {len(personas_without_agents)} personas without agent IDs:")
            for persona in personas_without_agents:
                print(f"   - {persona.id}: {persona.name}")
            
            # Update all personas without agent IDs
            update_result = conn.execute(text("""
                UPDATE personas 
                SET elevenlabs_agent_id = :agent_id 
                WHERE elevenlabs_agent_id IS NULL
            """), {"agent_id": agent_id})
            
            conn.commit()
            
            updated_count = update_result.rowcount
            print(f"✅ SUCCESS: Updated {updated_count} personas with agent ID: {agent_id}")
            
            # Verify the update
            verification = conn.execute(text("""
                SELECT COUNT(*) as count FROM personas 
                WHERE elevenlabs_agent_id = :agent_id
            """), {"agent_id": agent_id})
            
            total_with_agent = verification.fetchone().count
            print(f"✅ VERIFICATION: {total_with_agent} personas now have agent ID: {agent_id}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🎤 Updating all personas with ElevenLabs agent ID...")
    success = update_all_personas_agent_id()
    
    if success:
        print("\n🎉 All personas are now ready for voice chat!")
        print("💡 Refresh your browser to see the updated agent IDs")
    else:
        print("\n❌ Update failed. Check the error above.") 