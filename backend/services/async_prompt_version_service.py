"""
Async Prompt Version Management Service

Handles version control for the three-layer prompt system:
- System Prompts: Persona characteristics 
- RAG Prompts: Context formatting templates
- User Prompts: Query processing templates
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, and_, func, select, update
from models import PromptVersion, PromptLayer
import uuid
from datetime import datetime


class AsyncPromptVersionService:
    """Async service for managing prompt versions with auto-increment and activation"""
    
    @staticmethod
    async def create_version(
        db: AsyncSession,
        layer: PromptLayer,
        name: str,
        content: str,
        author_id: str,
        commit_message: Optional[str] = None,
        persona_id: Optional[str] = None,
        parent_version_id: Optional[str] = None
    ) -> PromptVersion:
        """Create a new prompt version with auto-increment version number"""
        
        # Get the next version number for this prompt name
        result = await db.execute(
            select(func.max(PromptVersion.version)).where(
                and_(
                    PromptVersion.layer == layer,
                    PromptVersion.name == name
                )
            )
        )
        max_version = result.scalar() or 0
        
        new_version = PromptVersion(
            id=str(uuid.uuid4()),
            layer=layer,
            name=name,
            content=content,
            version=max_version + 1,
            is_active=False,  # New versions start inactive
            author_id=author_id,
            commit_message=commit_message,
            persona_id=persona_id,
            parent_version_id=parent_version_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_version)
        await db.commit()
        await db.refresh(new_version)
        
        return new_version
    
    @staticmethod
    async def get_active_version(
        db: AsyncSession,
        layer: PromptLayer,
        name: str,
        persona_id: Optional[str] = None
    ) -> Optional[PromptVersion]:
        """Get the currently active version of a prompt"""
        
        query = select(PromptVersion).where(
            and_(
                PromptVersion.layer == layer,
                PromptVersion.name == name,
                PromptVersion.is_active == True
            )
        )
        
        if persona_id:
            query = query.where(PromptVersion.persona_id == persona_id)
        else:
            query = query.where(PromptVersion.persona_id.is_(None))
            
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_version_history(
        db: AsyncSession,
        layer: PromptLayer,
        name: str,
        persona_id: Optional[str] = None,
        limit: int = 10
    ) -> List[PromptVersion]:
        """Get version history for a prompt, ordered by version descending"""
        
        query = select(PromptVersion).where(
            and_(
                PromptVersion.layer == layer,
                PromptVersion.name == name
            )
        )
        
        if persona_id:
            query = query.where(PromptVersion.persona_id == persona_id)
        else:
            query = query.where(PromptVersion.persona_id.is_(None))
            
        query = query.order_by(desc(PromptVersion.version)).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_version_by_id(db: AsyncSession, version_id: str) -> Optional[PromptVersion]:
        """Get a specific version by ID"""
        result = await db.execute(
            select(PromptVersion).where(PromptVersion.id == version_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def activate_version(db: AsyncSession, version_id: str) -> Optional[PromptVersion]:
        """Activate a version and deactivate all others for the same prompt"""
        
        version = await AsyncPromptVersionService.get_version_by_id(db, version_id)
        if not version:
            return None
        
        # Deactivate all versions for this prompt
        await db.execute(
            update(PromptVersion).where(
                and_(
                    PromptVersion.layer == version.layer,
                    PromptVersion.name == version.name,
                    PromptVersion.persona_id == version.persona_id
                )
            ).values(is_active=False)
        )
        
        # Activate the selected version
        version.is_active = True
        version.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(version)
        
        return version
    
    @staticmethod
    async def get_diff_data(
        db: AsyncSession,
        from_version_id: str,
        to_version_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get diff data between two versions"""
        
        from_version = await AsyncPromptVersionService.get_version_by_id(db, from_version_id)
        to_version = await AsyncPromptVersionService.get_version_by_id(db, to_version_id)
        
        if not from_version or not to_version:
            return None
        
        # Simple line-by-line diff (frontend will handle detailed diff rendering)
        from_lines = from_version.content.splitlines()
        to_lines = to_version.content.splitlines()
        
        return {
            "from_version": {
                "id": from_version.id,
                "version": from_version.version,
                "content": from_version.content,
                "lines": from_lines
            },
            "to_version": {
                "id": to_version.id,
                "version": to_version.version,
                "content": to_version.content,
                "lines": to_lines
            },
            "metadata": {
                "from_author": from_version.author_id,
                "to_author": to_version.author_id,
                "from_created": from_version.created_at.isoformat(),
                "to_created": to_version.created_at.isoformat()
            }
        }
    
    @staticmethod
    async def list_all_prompts(db: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
        """List all available prompts grouped by layer"""
        
        # Get unique prompt names by layer
        prompts_by_layer = {}
        
        for layer in [PromptLayer.SYSTEM, PromptLayer.RAG, PromptLayer.USER]:
            # Get distinct prompt names for this layer
            result = await db.execute(
                select(PromptVersion.name).where(
                    PromptVersion.layer == layer
                ).distinct()
            )
            names = result.scalars().all()
            
            prompt_list = []
            for name in names:
                # Get active version info
                active_version = await AsyncPromptVersionService.get_active_version(db, layer, name)
                
                # Get total version count
                count_result = await db.execute(
                    select(func.count(PromptVersion.id)).where(
                        and_(
                            PromptVersion.layer == layer,
                            PromptVersion.name == name
                        )
                    )
                )
                version_count = count_result.scalar()
                
                # Get latest version for last updated
                latest_result = await db.execute(
                    select(PromptVersion).where(
                        and_(
                            PromptVersion.layer == layer,
                            PromptVersion.name == name
                        )
                    ).order_by(desc(PromptVersion.created_at)).limit(1)
                )
                latest_version = latest_result.scalar_one_or_none()
                
                prompt_list.append({
                    "name": name,
                    "layer": layer.value,
                    "active_version": active_version.version if active_version else None,
                    "active_version_id": active_version.id if active_version else None,
                    "total_versions": version_count,
                    "last_updated": latest_version.updated_at.isoformat() if latest_version else None
                })
            
            prompts_by_layer[layer.value.lower()] = prompt_list
        
        return prompts_by_layer 