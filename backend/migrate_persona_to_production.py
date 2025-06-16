#!/usr/bin/env python3
"""
Migrate Alex Hormozi persona from local database to production backend
Uses the production API endpoints to create persona and upload files
"""

import os
import sys
import json
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import List, Dict
import logging

# Add the app directory to Python path
sys.path.append('/app' if os.path.exists('/app') else '.')

from database import AsyncSessionLocal
from models import Persona, IngestionJob
from sqlalchemy import select, text

# Production API configuration
PRODUCTION_URL = "https://clone-api.fly.dev"
# SERVICE_TOKEN = "NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0"  # For internal endpoints

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersonaMigrator:
    def __init__(self):
        self.production_url = PRODUCTION_URL
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_best_local_persona(self) -> Dict:
        """Get the persona with the most completed files from local DB"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                SELECT p.id, p.name, p.namespace, p.description, p.user_id, 
                       COUNT(ij.id) as file_count
                FROM personas p 
                LEFT JOIN ingestion_jobs ij ON p.id = ij.persona_id 
                WHERE ij.status = 'COMPLETED'
                GROUP BY p.id, p.name, p.namespace, p.description, p.user_id
                HAVING COUNT(ij.id) > 0
                ORDER BY file_count DESC
                LIMIT 1;
            """))
            
            persona_row = result.fetchone()
            if not persona_row:
                raise Exception("No persona found with completed files")
                
            # Get the files for this persona
            files_result = await db.execute(text("""
                SELECT ij.id, ij.file_name, ij.file_path, ij.created_at
                FROM ingestion_jobs ij 
                WHERE ij.persona_id = :persona_id AND ij.status = 'COMPLETED'
                ORDER BY ij.created_at DESC;
            """), {"persona_id": persona_row.id})
            
            files = files_result.fetchall()
            
            return {
                "persona": {
                    "id": persona_row.id,
                    "name": persona_row.name,
                    "namespace": persona_row.namespace,
                    "description": persona_row.description,
                    "user_id": persona_row.user_id,
                    "file_count": persona_row.file_count
                },
                "files": [
                    {
                        "id": f.id,
                        "file_name": f.file_name,
                        "file_path": f.file_path,
                        "created_at": str(f.created_at)
                    }
                    for f in files
                ]
            }

    async def create_production_persona(self, persona_data: Dict) -> str:
        """Create persona in production via API"""
        # Note: This would require authentication
        # For now, we'll use the webhook method or create manually
        
        logger.info(f"📝 Would create persona in production:")
        logger.info(f"   Name: {persona_data['name']}")
        logger.info(f"   Description: {persona_data['description']}")
        logger.info(f"   Namespace: {persona_data['namespace']}")
        
        # Return a placeholder for now - you'd need to create this via the UI
        # or implement proper authentication
        return "PRODUCTION_PERSONA_ID_PLACEHOLDER"

    async def upload_file_to_production(self, persona_id: str, file_path: str, file_name: str):
        """Upload a file to production backend"""
        if not os.path.exists(file_path):
            logger.warning(f"📄 File not found: {file_path}")
            return False
            
        try:
            # This would require proper authentication
            # For demo purposes, showing the structure
            logger.info(f"📤 Would upload: {file_name} -> {persona_id}")
            
            # async with aiofiles.open(file_path, 'rb') as f:
            #     file_content = await f.read()
            #     
            #     data = aiohttp.FormData()
            #     data.add_field('file', file_content, filename=file_name)
            #     
            #     async with self.session.post(
            #         f"{self.production_url}/api/personas/{persona_id}/files",
            #         data=data,
            #         headers={"Authorization": f"Bearer {token}"}
            #     ) as response:
            #         if response.status == 201:
            #             result = await response.json()
            #             logger.info(f"✅ Uploaded {file_name}: {result['id']}")
            #             return True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upload {file_name}: {e}")
            return False

    async def migrate(self):
        """Main migration function"""
        try:
            # Step 1: Get local persona with most files
            logger.info("🔍 Finding best local persona...")
            data = await self.get_best_local_persona()
            
            persona = data["persona"]
            files = data["files"]
            
            logger.info(f"📋 Found: {persona['name']} with {len(files)} files")
            logger.info(f"   ID: {persona['id']}")
            logger.info(f"   Namespace: {persona['namespace']}")
            
            # Step 2: Create persona in production (manual step for now)
            logger.info(f"\n🎯 MIGRATION PLAN:")
            logger.info(f"1. Create persona in production with:")
            logger.info(f"   - Name: {persona['name']}")
            logger.info(f"   - Description: {persona['description']}")
            
            # Step 3: List files to upload
            logger.info(f"\n2. Upload {len(files)} files:")
            for file_info in files:
                file_path = file_info['file_path']
                file_name = file_info['file_name']
                exists = os.path.exists(file_path)
                logger.info(f"   📄 {file_name} {'✅' if exists else '❌ MISSING'}")
                
            # Export file list for manual upload
            export_data = {
                "persona": persona,
                "files": files,
                "migration_instructions": {
                    "step1": "Create persona manually in production UI",
                    "step2": "Note the production persona ID",
                    "step3": "Run upload script with production persona ID",
                    "step4": "Verify webhook works"
                }
            }
            
            with open("persona_migration_export.json", "w") as f:
                json.dump(export_data, f, indent=2, default=str)
                
            logger.info(f"\n💾 Export saved to: persona_migration_export.json")
            logger.info(f"📊 Summary: {persona['name']} -> {len(files)} files ready")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise

async def main():
    logger.info("🚀 Starting persona migration analysis...")
    
    async with PersonaMigrator() as migrator:
        await migrator.migrate()

if __name__ == "__main__":
    asyncio.run(main()) 