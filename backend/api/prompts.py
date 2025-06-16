"""
API endpoints for Prompt Control Center

Handles CRUD operations for the three-layer prompt system with version control.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio
import json

from database import get_db
from api.auth import get_current_user, User
from services.async_prompt_version_service import AsyncPromptVersionService
from services.prompt_service import PromptService
from services.llm_router import get_llm_router
from models import PromptLayer
import os

router = APIRouter(tags=["prompts"])

# Request/Response Models
class CreateVersionRequest(BaseModel):
    content: str
    commit_message: Optional[str] = None
    persona_id: Optional[str] = None

class CreatePromptRequest(BaseModel):
    layer: str
    name: str
    content: str
    commit_message: Optional[str] = None
    persona_id: Optional[str] = None

class TestPromptRequest(BaseModel):
    layer: str
    name: str
    content: str
    test_query: str
    persona_id: Optional[str] = None
    model: Optional[str] = "gpt-4o-mini"

class VersionResponse(BaseModel):
    id: str
    layer: str
    name: str
    content: str
    version: int
    is_active: bool
    author_id: str
    commit_message: Optional[str]
    persona_id: Optional[str]
    created_at: str
    updated_at: str

class PromptListResponse(BaseModel):
    prompts: Dict[str, List[Dict[str, Any]]]

class VersionHistoryResponse(BaseModel):
    versions: List[VersionResponse]
    active_version: Optional[VersionResponse]


@router.options("/")
async def options_prompts():
    """Handle CORS preflight for prompts list endpoint"""
    return {"message": "OK"}

@router.options("", include_in_schema=False)
async def options_prompts_no_slash():
    """Handle CORS preflight for prompts list endpoint without trailing slash"""
    return {"message": "OK"}

@router.get("/", response_model=PromptListResponse)
async def list_prompts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all prompt templates grouped by layer"""
    
    try:
        prompts = await AsyncPromptVersionService.list_all_prompts(db)
        return PromptListResponse(prompts=prompts)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prompts: {str(e)}"
        )

@router.get("", response_model=PromptListResponse, include_in_schema=False)
async def list_prompts_no_slash(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all prompt templates grouped by layer (no trailing slash)"""
    
    try:
        prompts = await AsyncPromptVersionService.list_all_prompts(db)
        return PromptListResponse(prompts=prompts)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prompts: {str(e)}"
        )

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=VersionResponse)
async def create_prompt(
    request: CreatePromptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new prompt (first version)"""
    
    try:
        # Validate layer
        try:
            prompt_layer = PromptLayer(request.layer.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid layer: {request.layer}. Must be one of: system, rag, user"
            )
        
        # Create new prompt (version 1)
        new_version = await AsyncPromptVersionService.create_version(
            db=db,
            layer=prompt_layer,
            name=request.name,
            content=request.content,
            author_id=current_user.id,
            commit_message=request.commit_message or "Initial prompt creation",
            persona_id=request.persona_id
        )
        
        # Activate the first version
        await AsyncPromptVersionService.activate_version(db, new_version.id)
        
        return VersionResponse(
            id=new_version.id,
            layer=new_version.layer.value,
            name=new_version.name,
            content=new_version.content,
            version=new_version.version,
            is_active=True,  # First version is activated
            author_id=new_version.author_id,
            commit_message=new_version.commit_message,
            persona_id=new_version.persona_id,
            created_at=new_version.created_at.isoformat(),
            updated_at=new_version.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt: {str(e)}"
        )

@router.post("", status_code=status.HTTP_201_CREATED, response_model=VersionResponse, include_in_schema=False)
async def create_prompt_no_slash(
    request: CreatePromptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new prompt (first version) - no trailing slash"""
    
    try:
        # Validate layer
        try:
            prompt_layer = PromptLayer(request.layer.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid layer: {request.layer}. Must be one of: system, rag, user"
            )
        
        # Create new prompt (version 1)
        new_version = await AsyncPromptVersionService.create_version(
            db=db,
            layer=prompt_layer,
            name=request.name,
            content=request.content,
            author_id=current_user.id,
            commit_message=request.commit_message or "Initial prompt creation",
            persona_id=request.persona_id
        )
        
        # Activate the first version
        await AsyncPromptVersionService.activate_version(db, new_version.id)
        
        return VersionResponse(
            id=new_version.id,
            layer=new_version.layer.value,
            name=new_version.name,
            content=new_version.content,
            version=new_version.version,
            is_active=True,  # First version is activated
            author_id=new_version.author_id,
            commit_message=new_version.commit_message,
            persona_id=new_version.persona_id,
            created_at=new_version.created_at.isoformat(),
            updated_at=new_version.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt: {str(e)}"
        )

@router.get("/{layer}/{name}/versions", response_model=VersionHistoryResponse)
async def get_version_history(
    layer: str,
    name: str,
    persona_id: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get version history for a specific prompt"""
    
    try:
        # Validate layer
        try:
            prompt_layer = PromptLayer(layer.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid layer: {layer}. Must be one of: system, rag, user"
            )
        
        # Get version history
        versions = await AsyncPromptVersionService.get_version_history(
            db, prompt_layer, name, persona_id, limit
        )
        
        # Get active version
        active_version = await AsyncPromptVersionService.get_active_version(
            db, prompt_layer, name, persona_id
        )
        
        # Convert to response models
        version_responses = []
        for v in versions:
            version_responses.append(VersionResponse(
                id=v.id,
                layer=v.layer.value,
                name=v.name,
                content=v.content,
                version=v.version,
                is_active=v.is_active,
                author_id=v.author_id,
                commit_message=v.commit_message,
                persona_id=v.persona_id,
                created_at=v.created_at.isoformat(),
                updated_at=v.updated_at.isoformat()
            ))
        
        active_response = None
        if active_version:
            active_response = VersionResponse(
                id=active_version.id,
                layer=active_version.layer.value,
                name=active_version.name,
                content=active_version.content,
                version=active_version.version,
                is_active=active_version.is_active,
                author_id=active_version.author_id,
                commit_message=active_version.commit_message,
                persona_id=active_version.persona_id,
                created_at=active_version.created_at.isoformat(),
                updated_at=active_version.updated_at.isoformat()
            )
        
        return VersionHistoryResponse(
            versions=version_responses,
            active_version=active_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version history: {str(e)}"
        )


@router.post("/{layer}/{name}/versions", status_code=status.HTTP_201_CREATED, response_model=VersionResponse)
async def create_version(
    layer: str,
    name: str,
    request: CreateVersionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new version of a prompt"""
    
    try:
        # Validate layer
        try:
            prompt_layer = PromptLayer(layer.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid layer: {layer}. Must be one of: system, rag, user"
            )
        
        # Create new version
        new_version = await AsyncPromptVersionService.create_version(
            db=db,
            layer=prompt_layer,
            name=name,
            content=request.content,
            author_id=current_user.id,
            commit_message=request.commit_message,
            persona_id=request.persona_id
        )
        
        return VersionResponse(
            id=new_version.id,
            layer=new_version.layer.value,
            name=new_version.name,
            content=new_version.content,
            version=new_version.version,
            is_active=new_version.is_active,
            author_id=new_version.author_id,
            commit_message=new_version.commit_message,
            persona_id=new_version.persona_id,
            created_at=new_version.created_at.isoformat(),
            updated_at=new_version.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version: {str(e)}"
        )


@router.get("/diff")
async def get_diff(
    from_version: str,
    to_version: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare two prompt versions"""
    
    try:
        diff_data = await AsyncPromptVersionService.get_diff_data(db, from_version, to_version)
        
        if not diff_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both versions not found"
            )
        
        return diff_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate diff: {str(e)}"
        )


@router.put("/{version_id}/activate", response_model=VersionResponse)
async def activate_version(
    version_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate a specific prompt version"""
    
    try:
        activated_version = await AsyncPromptVersionService.activate_version(db, version_id)
        
        if not activated_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        return VersionResponse(
            id=activated_version.id,
            layer=activated_version.layer.value,
            name=activated_version.name,
            content=activated_version.content,
            version=activated_version.version,
            is_active=activated_version.is_active,
            author_id=activated_version.author_id,
            commit_message=activated_version.commit_message,
            persona_id=activated_version.persona_id,
            created_at=activated_version.created_at.isoformat(),
            updated_at=activated_version.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate version: {str(e)}"
        )


@router.post("/test")
async def test_prompt(
    request: TestPromptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test a prompt with streaming response"""
    
    try:
        # Validate layer
        try:
            prompt_layer = PromptLayer(request.layer.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid layer: {request.layer}. Must be one of: system, rag, user"
            )
        
        # Initialize prompt service and LLM router
        prompt_service = PromptService()
        llm_router = get_llm_router()
        
        # Build a test prompt based on the layer
        if prompt_layer == PromptLayer.SYSTEM:
            # Test system prompt
            full_prompt = f"{request.content}\n\nUser Query: {request.test_query}"
        elif prompt_layer == PromptLayer.RAG:
            # Test RAG prompt with mock context
            mock_chunks = [
                {"text": "Sample context from test document", "source": "test.pdf", "metadata": {}}
            ]
            from jinja2 import Template
            template = Template(request.content)
            rag_context = template.render(chunks=mock_chunks)
            full_prompt = f"System: You are a helpful assistant.\n\n{rag_context}\n\nUser Query: {request.test_query}"
        else:  # USER layer
            # Test user prompt processing
            from jinja2 import Template
            template = Template(request.content)
            processed_query = template.render(query=request.test_query)
            full_prompt = f"System: You are a helpful assistant.\n\nUser Query: {processed_query}"
        
        # Create streaming response
        async def generate_test_response():
            try:
                # Send initial metadata
                yield f"data: {json.dumps({'type': 'metadata', 'prompt_length': len(full_prompt), 'timestamp': 'start'})}\n\n"
                
                # Stream the LLM response using the router
                full_response = ""
                async for chunk in llm_router.stream_completion(
                    prompt=full_prompt,
                    model=request.model or "gpt-4o-mini",
                    max_tokens=500
                ):
                    if chunk:
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                
                # Send completion metadata
                yield f"data: {json.dumps({'type': 'complete', 'total_tokens': len(full_response.split()), 'timestamp': 'end'})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_test_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test prompt: {str(e)}"
        ) 