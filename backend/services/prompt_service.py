"""
Three-Layer Prompt Architecture Service

Handles the modular prompt system with:
1. System Prompt: Persona characteristics
2. RAG Context: Retrieved documents 
3. User Query: User's question
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from jinja2 import Template


@dataclass
class PromptLayers:
    """Data class for the three prompt layers"""
    system: str
    rag_context: str
    user_query: str


@dataclass
class RAGChunk:
    """Data class for RAG context chunks"""
    text: str
    source: str
    source_type: str
    metadata: Dict[str, Any]
    index_plus_one: int


class PromptService:
    """Service for managing three-layer prompt architecture"""
    
    def __init__(self, prompts_base_path: str = "../prompts"):
        # Get the absolute path relative to this file
        current_dir = Path(__file__).parent.parent  # Go up to backend directory
        
        # Try different path locations for development vs production
        possible_paths = [
            current_dir.parent / "prompts",  # Development: clone-advisor/prompts 
            current_dir / "prompts",         # Production: /app/prompts
            Path("/app/prompts"),            # Fallback production path
        ]
        
        self.prompts_base_path = None
        for path in possible_paths:
            if path.exists() and (path / "versions").exists():
                self.prompts_base_path = path
                print(f"✅ Found prompts directory at: {path}")
                break
        
        if self.prompts_base_path is None:
            print(f"❌ WARNING: Could not find prompts directory in any of: {possible_paths}")
            # Create a minimal fallback path
            self.prompts_base_path = current_dir / "prompts"
            
        self.current_version = self._load_current_version()
        self.templates_cache = {}
    
    def _load_current_version(self) -> Dict[str, Any]:
        """Load the current prompt version configuration"""
        try:
            version_file = self.prompts_base_path / "versions" / "v1.0.json"
            with open(version_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading prompt version: {e}")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Fallback configuration if version file is missing"""
        return {
            "version": "fallback",
            "layers": {
                "system": {"default": "prompts/system/default.txt"},
                "rag": {"standard": "prompts/rag/standard.txt"}
            },
            "default_config": {
                "system_template": "default",
                "rag_template": "standard"
            }
        }
    
    def _load_template(self, template_path: str) -> str:
        """Load a template file with caching"""
        if template_path in self.templates_cache:
            return self.templates_cache[template_path]
        
        try:
            # Use the base path directly since template_path includes 'prompts/'
            full_path = self.prompts_base_path.parent / template_path
            with open(full_path, 'r') as f:
                content = f.read()
                self.templates_cache[template_path] = content
                return content
        except Exception as e:
            print(f"Error loading template {template_path}: {e}")
            return self._get_fallback_template()
    
    def _get_fallback_template(self) -> str:
        """Fallback template content"""
        return """You are {{persona_name}}, an AI assistant.

Your characteristics: {{description}}

Instructions:
- Answer questions based on your knowledge
- Cite sources using [1], [2], etc.
- Be helpful and accurate"""
    
    def get_system_prompt(self, persona_name: str, description: str, persona_type: str = "default") -> str:
        """Generate the system prompt layer"""
        # Determine which system template to use
        config = self.current_version
        persona_config = config.get("persona_overrides", {}).get(persona_type, config["default_config"])
        system_template_key = persona_config["system_template"]
        
        # Get template path
        template_path = config["layers"]["system"][system_template_key]
        template_content = self._load_template(template_path)
        
        # Render template
        template = Template(template_content)
        return template.render(
            persona_name=persona_name,
            description=description
        )
    
    def get_rag_context(self, chunks: List[Dict[str, Any]], persona_type: str = "default") -> str:
        """Generate the RAG context layer"""
        if not chunks:
            return "No relevant information found in your documents."
        
        # Determine which RAG template to use
        config = self.current_version
        persona_config = config.get("persona_overrides", {}).get(persona_type, config["default_config"])
        rag_template_key = persona_config["rag_template"]
        
        # Get template path
        template_path = config["layers"]["rag"][rag_template_key]
        template_content = self._load_template(template_path)
        
        # Prepare chunks with proper indexing
        formatted_chunks = []
        for i, chunk in enumerate(chunks):
            formatted_chunks.append({
                **chunk,
                "index_plus_one": i + 1,
                "metadata": chunk.get("metadata", {})
            })
        
        # Render template
        template = Template(template_content)
        return template.render(chunks=formatted_chunks)
    
    def build_complete_prompt(
        self,
        persona_name: str,
        description: str,
        user_query: str,
        chunks: List[Dict[str, Any]],
        persona_type: str = "default"
    ) -> PromptLayers:
        """Build the complete three-layer prompt"""
        system_prompt = self.get_system_prompt(persona_name, description, persona_type)
        rag_context = self.get_rag_context(chunks, persona_type)
        
        return PromptLayers(
            system=system_prompt,
            rag_context=rag_context,
            user_query=user_query
        )
    
    def format_for_llm(self, prompt_layers: PromptLayers) -> str:
        """Format the three layers into a single prompt for the LLM"""
        return f"""{prompt_layers.system}

{prompt_layers.rag_context}

USER QUESTION: {prompt_layers.user_query}

Please provide a helpful response based on the above information."""
    
    def get_available_templates(self) -> Dict[str, List[str]]:
        """Get list of available templates for each layer"""
        config = self.current_version
        return {
            "system": list(config["layers"]["system"].keys()),
            "rag": list(config["layers"]["rag"].keys())
        }
    
    def get_version_info(self) -> Dict[str, Any]:
        """Get information about the current prompt version"""
        return {
            "version": self.current_version.get("version"),
            "created_at": self.current_version.get("created_at"),
            "description": self.current_version.get("description"),
            "available_templates": self.get_available_templates()
        }


# Global prompt service instance
prompt_service = PromptService() 