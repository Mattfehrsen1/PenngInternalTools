"""
Persona-Specific Prompt Management Service

Handles prompt management for individual personas, including:
- Creating prompts from templates
- Managing persona-specific prompt versions  
- Retrieving active prompts per persona
- Persona settings management
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from models import PromptVersion, PromptLayer, PersonaSettings, Persona
from services.async_prompt_version_service import AsyncPromptVersionService
import uuid
from datetime import datetime
import json
import os
from pathlib import Path


class PersonaPromptService:
    """Service for managing persona-specific prompts and settings"""
    
    def __init__(self, templates_base_path: str = "../prompts/templates"):
        # Get the absolute path relative to this file
        current_dir = Path(__file__).parent.parent.parent  # Go up to clone-advisor root
        self.templates_base_path = current_dir / "prompts" / "templates"
    
    async def create_persona_with_template(
        self,
        persona_id: str,
        template_name: str,
        author_id: str,
        db: AsyncSession
    ) -> Dict[str, PromptVersion]:
        """Create all prompt layers for a persona from a template"""
        
        # Load template files
        template_dir = self.templates_base_path / template_name
        if not template_dir.exists():
            raise ValueError(f"Template '{template_name}' not found")
        
        created_prompts = {}
        
        # Define the prompt layers to create
        layers = [
            (PromptLayer.SYSTEM, "system.txt", "main"),
            (PromptLayer.RAG, "rag.txt", "main"), 
            (PromptLayer.USER, "user.txt", "main")
        ]
        
        for layer, filename, name in layers:
            template_file = template_dir / filename
            if template_file.exists():
                with open(template_file, 'r') as f:
                    content = f.read()
                
                # Create and activate the prompt version
                version = await AsyncPromptVersionService.create_version(
                    db=db,
                    layer=layer,
                    name=name,
                    content=content,
                    author_id=author_id,
                    commit_message=f"Created from template: {template_name}",
                    persona_id=persona_id
                )
                
                # Activate this version
                activated_version = await AsyncPromptVersionService.activate_version(db, version.id)
                if activated_version:
                    created_prompts[layer.value] = activated_version
                else:
                    print(f"Warning: Failed to activate {layer.value} prompt for persona {persona_id}")
                    created_prompts[layer.value] = version
        
        return created_prompts
    
    async def get_active_prompts(
        self,
        persona_id: str,
        db: AsyncSession
    ) -> Dict[str, str]:
        """Get all active prompts for a persona"""
        
        active_prompts = {}
        
        for layer in [PromptLayer.SYSTEM, PromptLayer.RAG, PromptLayer.USER]:
            version = await AsyncPromptVersionService.get_active_version(
                db=db,
                layer=layer,
                name="main",  # Default to 'main' prompt name
                persona_id=persona_id
            )
            
            if version:
                active_prompts[layer.value] = version.content
            else:
                # Fallback to default prompts if no persona-specific prompt exists
                active_prompts[layer.value] = await self._get_fallback_prompt(layer)
        
        return active_prompts
    
    async def create_prompt_version(
        self,
        persona_id: str,
        layer: PromptLayer,
        name: str,
        content: str,
        author_id: str,
        commit_message: str,
        db: AsyncSession
    ) -> PromptVersion:
        """Create new version of a persona's prompt and activate it"""
        
        # Verify persona ownership would be handled by the API layer
        
        # Create the new version
        new_version = await AsyncPromptVersionService.create_version(
            db=db,
            layer=layer,
            name=name,
            content=content,
            author_id=author_id,
            commit_message=commit_message,
            persona_id=persona_id
        )
        
        # Automatically activate the new version
        activated_version = await AsyncPromptVersionService.activate_version(db, new_version.id)
        
        return activated_version or new_version
    
    async def clone_persona_prompts(
        self,
        source_persona_id: str,
        target_persona_id: str,
        author_id: str,
        db: AsyncSession
    ) -> List[PromptVersion]:
        """Clone all prompts from one persona to another"""
        
        cloned_prompts = []
        
        # Get all active prompts from source persona
        for layer in [PromptLayer.SYSTEM, PromptLayer.RAG, PromptLayer.USER]:
            source_version = await AsyncPromptVersionService.get_active_version(
                db=db,
                layer=layer,
                name="main",
                persona_id=source_persona_id
            )
            
            if source_version:
                # Create new version for target persona
                new_version = await self.create_prompt_version(
                    persona_id=target_persona_id,
                    layer=layer,
                    name="main",
                    content=source_version.content,
                    author_id=author_id,
                    commit_message=f"Cloned from persona {source_persona_id}",
                    db=db
                )
                
                # Activate the cloned version
                await AsyncPromptVersionService.activate_version(db, new_version.id)
                cloned_prompts.append(new_version)
        
        return cloned_prompts
    
    async def get_persona_settings(
        self,
        persona_id: str,
        db: AsyncSession
    ) -> Optional[PersonaSettings]:
        """Get settings for a persona"""
        
        result = await db.execute(
            select(PersonaSettings).where(PersonaSettings.persona_id == persona_id)
        )
        return result.scalar_one_or_none()
    
    async def update_persona_settings(
        self,
        persona_id: str,
        db: AsyncSession,
        voice_id: Optional[str] = None,
        voice_settings: Optional[Dict] = None,
        default_model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> PersonaSettings:
        """Update or create persona settings"""
        
        # Try to get existing settings
        settings = await self.get_persona_settings(persona_id, db)
        
        if settings:
            # Update existing settings
            if voice_id is not None:
                settings.voice_id = voice_id
            if voice_settings is not None:
                settings.voice_settings = voice_settings
            if default_model is not None:
                settings.default_model = default_model
            if temperature is not None:
                settings.temperature = int(temperature * 100)  # Store as int
            if max_tokens is not None:
                settings.max_tokens = max_tokens
            
            settings.updated_at = datetime.utcnow()
        else:
            # Create new settings
            settings = PersonaSettings(
                id=str(uuid.uuid4()),
                persona_id=persona_id,
                voice_id=voice_id,
                voice_settings=voice_settings,
                default_model=default_model,
                temperature=int(temperature * 100) if temperature is not None else None,
                max_tokens=max_tokens,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(settings)
        
        await db.commit()
        await db.refresh(settings)
        return settings
    
    async def list_persona_prompts(
        self,
        persona_id: str,
        db: AsyncSession
    ) -> Dict[str, List[Dict[str, Any]]]:
        """List all prompts for a persona grouped by layer"""
        
        prompts_by_layer = {}
        
        for layer in [PromptLayer.SYSTEM, PromptLayer.RAG, PromptLayer.USER]:
            # Get all prompt names for this layer and persona
            result = await db.execute(
                select(PromptVersion.name).where(
                    and_(
                        PromptVersion.layer == layer,
                        PromptVersion.persona_id == persona_id
                    )
                ).distinct()
            )
            names = result.scalars().all()
            
            prompt_list = []
            for name in names:
                # Get active version info
                active_version = await AsyncPromptVersionService.get_active_version(
                    db, layer, name, persona_id
                )
                
                # Get total version count
                count_result = await db.execute(
                    select(func.count(PromptVersion.id)).where(
                        and_(
                            PromptVersion.layer == layer,
                            PromptVersion.name == name,
                            PromptVersion.persona_id == persona_id
                        )
                    )
                )
                version_count = count_result.scalar()
                
                prompt_list.append({
                    "id": active_version.id if active_version else None,
                    "name": name,
                    "layer": layer.value,
                    "content": active_version.content if active_version else "",
                    "version": active_version.version if active_version else None,
                    "is_active": True,  # This is the active version
                    "active_version_id": active_version.id if active_version else None,
                    "total_versions": version_count,
                    "created_at": active_version.created_at.isoformat() if active_version else None,
                    "updated_at": active_version.updated_at.isoformat() if active_version else None,
                    "commit_message": active_version.commit_message if active_version else None
                })
            
            prompts_by_layer[layer.value] = prompt_list
        
        return prompts_by_layer
    
    async def _get_fallback_prompt(self, layer: PromptLayer) -> str:
        """Get fallback prompt content for a layer"""
        
        fallback_prompts = {
            PromptLayer.SYSTEM: """You are {{persona_name}}, an AI assistant.

{{description}}

Instructions:
- Answer questions based on your knowledge
- Cite sources using [1], [2], etc.
- Be helpful and accurate""",
            
            PromptLayer.RAG: """Based on the following information:

{% for chunk in chunks %}
[{{chunk.index_plus_one}}] {{chunk.text}}
Source: {{chunk.metadata.source or 'Unknown'}}

{% endfor %}""",
            
            PromptLayer.USER: """USER QUESTION: {{user_query}}

Please provide a helpful response based on the above information."""
        }
        
        return fallback_prompts.get(layer, "Default prompt content")
    
    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available persona templates"""
        
        templates = []
        
        if self.templates_base_path.exists():
            for template_dir in self.templates_base_path.iterdir():
                if template_dir.is_dir():
                    metadata_file = template_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                        except:
                            metadata = {}
                    else:
                        metadata = {}
                    
                    templates.append({
                        "id": template_dir.name,
                        "name": metadata.get("name", template_dir.name.replace("_", " ").title()),
                        "description": metadata.get("description", "No description available"),
                        "tags": metadata.get("tags", []),
                        "preview": metadata.get("preview", {})
                    })
        
        return templates


# Global service instance
persona_prompt_service = PersonaPromptService() 