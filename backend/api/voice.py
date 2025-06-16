"""
Voice API endpoints for ElevenLabs integration
Implements Task 2.3 from the roadmap: Voice Streaming API Endpoint
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from services.voice_service import voice_service
from database import get_db
from api.auth import get_current_user, User
from models import Persona, PersonaSettings
import json
from services.persona_prompt_service import PersonaPromptService
from api.elevenlabs_functions import query_persona_knowledge

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["voice"])

# Pydantic models for request/response
class VoiceStreamRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None  # Override persona's default voice
    voice_settings: Optional[Dict[str, Any]] = None

class VoicePreviewRequest(BaseModel):
    voice_id: str
    text: Optional[str] = None

class VoiceInfo(BaseModel):
    voice_id: str
    name: str
    category: str
    description: str
    labels: Dict[str, Any]
    preview_url: Optional[str] = None

class PersonaVoiceSettings(BaseModel):
    voice_id: str
    voice_name: str
    voice_settings: Dict[str, Any]

@router.post("/personas/{persona_id}/voice/stream")
async def stream_persona_voice(
    persona_id: str,
    request: VoiceStreamRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stream voice for a specific persona with custom voice settings"""
    try:
        # Verify user owns this persona
        persona_service = PersonaPromptService()
        if not await persona_service.user_owns_persona(current_user.id, persona_id, db):
            raise HTTPException(status_code=403, detail="Access denied to this persona")
        
        text = request.text
        voice_id = request.voice_id
        voice_settings = request.voice_settings or {}
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # If no voice_id provided, use default
        if not voice_id:
            voice_id = voice_service.default_voice_id
        
        # Stream voice response
        return StreamingResponse(
            voice_service.stream_voice(
                text=text,
                voice_id=voice_id,
                voice_settings=voice_settings
            ),
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice streaming error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice streaming failed: {str(e)}")

@router.get("/voices", response_model=List[VoiceInfo])
async def list_available_voices(
    current_user: User = Depends(get_current_user)
):
    """
    Get all available ElevenLabs voices for selection
    """
    try:
        voices = await voice_service.list_available_voices()
        return voices
        
    except Exception as e:
        logger.error(f"Failed to fetch available voices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch available voices"
        )

@router.get("/list")
async def list_available_voices(
    current_user = Depends(get_current_user)
):
    """List all available ElevenLabs voices"""
    try:
        voices = await voice_service.list_available_voices()
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch voices: {str(e)}")

@router.get("/personas/{persona_id}/settings")
async def get_persona_voice_settings(
    persona_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get voice settings for a specific persona"""
    try:
        # Verify user owns this persona
        persona_service = PersonaPromptService()
        if not await persona_service.user_owns_persona(current_user.id, persona_id, db):
            raise HTTPException(status_code=403, detail="Access denied to this persona")
        
        # Get persona settings from database
        settings = await persona_service.get_persona_settings(persona_id, db)
        
        return {
            "voice_id": settings.voice_id if settings else voice_service.default_voice_id,
            "voice_settings": json.loads(settings.voice_settings) if settings and settings.voice_settings else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get voice settings: {str(e)}")

@router.put("/personas/{persona_id}/settings")
async def update_persona_voice_settings(
    persona_id: str,
    request_data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update voice settings for a specific persona"""
    try:
        # Verify user owns this persona
        persona_service = PersonaPromptService()
        if not await persona_service.user_owns_persona(current_user.id, persona_id, db):
            raise HTTPException(status_code=403, detail="Access denied to this persona")
        
        voice_id = request_data.get("voice_id")
        voice_settings = request_data.get("voice_settings", {})
        
        # Update persona voice settings
        await persona_service.update_persona_settings(
            persona_id=persona_id,
            db=db,
            voice_id=voice_id,
            voice_settings=voice_settings
        )
        
        return {"success": True, "message": "Voice settings updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update voice settings: {str(e)}")

# Add a simple endpoint that will work with current frontend calls
@router.post("/personas/{persona_id}/voice/stream-simple")
async def stream_persona_voice_simple(
    persona_id: str,
    request_data: dict,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Simple voice streaming endpoint that works with frontend - TESTS REDIS CACHING"""
    try:
        # Get text from request
        text = request_data.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        logger.info(f"[VOICE] Voice streaming for persona {persona_id}: {text[:100]}...")
        
        # This will use the Redis-cached query_persona_knowledge function!
        # The function call will demonstrate the caching performance improvement
        cached_response = await query_persona_knowledge(
            persona_id=persona_id,
            query=f"Please respond to this as if speaking: {text}"
        )
        
        logger.info(f"[VOICE] Got cached response: {cached_response[:100]}...")
        
        # For now, return a simple audio response (you can enhance this later)
        # This demonstrates that Redis caching is working with the voice API
        if not voice_service.client:
            raise HTTPException(status_code=503, detail="Voice service not available")
        
        # Stream the cached response as voice
        return StreamingResponse(
            voice_service.stream_voice(
                text=cached_response,
                voice_id=voice_service.default_voice_id,
                voice_settings={}
            ),
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice streaming error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice streaming failed: {str(e)}")

# TODO: Fix these endpoints to use AsyncSession properly
# @router.post("/voices/preview")
# @router.get("/personas/{persona_id}/voice") 
# @router.put("/personas/{persona_id}/voice")
# @router.get("/personas/{persona_id}/voice/usage")
# These endpoints are temporarily disabled to focus on getting voice streaming working 