"""
Prompt Version Management Service

Handles version control for the three-layer prompt system:
- System Prompts: Persona characteristics 
- RAG Prompts: Context formatting templates
- User Prompts: Query processing templates
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from models import PromptVersion, PromptLayer
import uuid
from datetime import datetime


class PromptVersionService:
    """Service for managing prompt versions with auto-increment and activation"""
    
    @staticmethod
    def create_version(
        db: Session,
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
        max_version = db.query(func.max(PromptVersion.version)).filter(
            PromptVersion.layer == layer,
            PromptVersion.name == name
        ).scalar() or 0
        
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
        db.commit()
        db.refresh(new_version)
        
        return new_version
    
    @staticmethod
    def get_active_version(
        db: Session,
        layer: PromptLayer,
        name: str,
        persona_id: Optional[str] = None
    ) -> Optional[PromptVersion]:
        """Get the currently active version of a prompt"""
        
        query = db.query(PromptVersion).filter(
            PromptVersion.layer == layer,
            PromptVersion.name == name,
            PromptVersion.is_active == True
        )
        
        if persona_id:
            query = query.filter(PromptVersion.persona_id == persona_id)
        else:
            query = query.filter(PromptVersion.persona_id.is_(None))
            
        return query.first()
    
    @staticmethod
    def get_version_history(
        db: Session,
        layer: PromptLayer,
        name: str,
        persona_id: Optional[str] = None,
        limit: int = 10
    ) -> List[PromptVersion]:
        """Get version history for a prompt, ordered by version descending"""
        
        query = db.query(PromptVersion).filter(
            PromptVersion.layer == layer,
            PromptVersion.name == name
        )
        
        if persona_id:
            query = query.filter(PromptVersion.persona_id == persona_id)
        else:
            query = query.filter(PromptVersion.persona_id.is_(None))
            
        return query.order_by(desc(PromptVersion.version)).limit(limit).all()
    
    @staticmethod
    def get_version_by_id(db: Session, version_id: str) -> Optional[PromptVersion]:
        """Get a specific version by ID"""
        return db.query(PromptVersion).filter(PromptVersion.id == version_id).first()
    
    @staticmethod
    def activate_version(db: Session, version_id: str) -> Optional[PromptVersion]:
        """Activate a version and deactivate all others for the same prompt"""
        
        version = PromptVersionService.get_version_by_id(db, version_id)
        if not version:
            return None
        
        # Deactivate all versions for this prompt
        db.query(PromptVersion).filter(
            PromptVersion.layer == version.layer,
            PromptVersion.name == version.name,
            PromptVersion.persona_id == version.persona_id
        ).update({"is_active": False})
        
        # Activate the selected version
        version.is_active = True
        version.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(version)
        
        return version
    
    @staticmethod
    def get_diff_data(
        db: Session,
        from_version_id: str,
        to_version_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get diff data between two versions"""
        
        from_version = PromptVersionService.get_version_by_id(db, from_version_id)
        to_version = PromptVersionService.get_version_by_id(db, to_version_id)
        
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
    def list_all_prompts(db: Session) -> Dict[str, List[Dict[str, Any]]]:
        """List all available prompts grouped by layer"""
        
        # Get unique prompt names by layer
        prompts_by_layer = {}
        
        for layer in [PromptLayer.SYSTEM, PromptLayer.RAG, PromptLayer.USER]:
            # Get distinct prompt names for this layer
            names = db.query(PromptVersion.name).filter(
                PromptVersion.layer == layer
            ).distinct().all()
            
            prompt_list = []
            for (name,) in names:
                # Get active version info
                active_version = PromptVersionService.get_active_version(db, layer, name)
                
                # Get total version count
                version_count = db.query(PromptVersion).filter(
                    PromptVersion.layer == layer,
                    PromptVersion.name == name
                ).count()
                
                prompt_list.append({
                    "name": name,
                    "layer": layer.value,
                    "active_version": active_version.version if active_version else None,
                    "active_version_id": active_version.id if active_version else None,
                    "total_versions": version_count,
                    "last_updated": active_version.updated_at.isoformat() if active_version else None
                })
            
            prompts_by_layer[layer.value] = prompt_list
        
        return prompts_by_layer


# Global service instance
prompt_version_service = PromptVersionService() 