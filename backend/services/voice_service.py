"""
Voice service for ElevenLabs integration
Implements Task 2.2 from the roadmap: Backend Voice Service
"""

import os
import logging
import asyncio
from typing import AsyncIterator, Dict, List, Optional, Any
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import PersonaSettings
from fastapi import HTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class VoiceService:
    """ElevenLabs voice service with streaming and persona support"""
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not found in environment - voice features will be disabled")
            self.client = None
        else:
            self.client = ElevenLabs(api_key=self.api_key)
        
        # Use custom default voice from .env, fallback to Sarah
        self.default_voice_id = os.getenv('DEFAULT_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')
        self.default_model = 'eleven_flash_v2_5'  # Fast model as specified
        
    def stream_voice_sync(
        self, 
        text: str, 
        voice_id: str, 
        model: str = None,
        voice_settings: Dict[str, Any] = None,
        max_retries: int = 3
    ):
        """
        Stream voice generation with retry logic
        Task 2.2.2: Core streaming method
        """
        if not self.client:
            raise HTTPException(
                status_code=503,
                detail="Voice service is not available - ElevenLabs API key not configured"
            )
            
        if not text.strip():
            return
            
        model = model or self.default_model
        
        # Default voice settings if none provided
        if not voice_settings:
            voice_settings = {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        
        # Log character count for usage tracking (Task 2.2.7)
        char_count = len(text)
        logger.info(f"Generating voice for {char_count} characters with voice {voice_id}")
        
        retry_count = 0
        while retry_count <= max_retries:
            try:
                # Create voice settings object
                settings = VoiceSettings(
                    stability=voice_settings.get("stability", 0.5),
                    similarity_boost=voice_settings.get("similarity_boost", 0.75),
                    style=voice_settings.get("style", 0.0),
                    use_speaker_boost=voice_settings.get("use_speaker_boost", True)
                )
                
                # Stream audio generation using correct API method with latency optimization
                # Note: model_id parameter removed as it's no longer supported in stream method
                audio_stream = self.client.text_to_speech.stream(
                    text=text,
                    voice_id=voice_id,
                    voice_settings=settings,
                    output_format="mp3_22050_32",  # Default format for streaming
                    optimize_streaming_latency=3,  # Max latency optimizations (4s → <500ms)
                    model_id=self.default_model  # Use eleven_flash_v2_5 for speed
                )
                
                # Return synchronous generator (no yield, just return the iterator)
                # ElevenLabs client is synchronous, so return the iterator directly
                chunk_count = 0
                for chunk in audio_stream:
                    if chunk:
                        chunk_count += 1
                        yield chunk
                        
                logger.info(f"Successfully generated voice for {char_count} characters in {chunk_count} chunks")
                return
                
            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f"Voice generation failed after {max_retries} retries: {str(e)}")
                    raise
                
                # Exponential backoff (Task 2.2.6)
                wait_time = (2 ** retry_count) * 0.5  # 0.5s, 1s, 2s
                logger.warning(f"Voice generation attempt {retry_count} failed, retrying in {wait_time}s: {str(e)}")
                # Use time.sleep instead of asyncio.sleep for sync operation
                import time
                time.sleep(wait_time)
    
    async def stream_voice(
        self, 
        text: str, 
        voice_id: str, 
        model: str = None,
        voice_settings: Dict[str, Any] = None,
        max_retries: int = 3
    ) -> AsyncIterator[bytes]:
        """
        Async wrapper around synchronous ElevenLabs streaming
        FIXED: True streaming - yield chunks as they're generated
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        import queue
        import threading
        
        # Use a queue to pass chunks from sync generator to async generator
        chunk_queue = queue.Queue()
        exception_holder = [None]
        
        def run_sync_stream():
            try:
                for chunk in self.stream_voice_sync(text, voice_id, model, voice_settings, max_retries):
                    chunk_queue.put(chunk)
                chunk_queue.put(None)  # Signal end of stream
            except Exception as e:
                exception_holder[0] = e
                chunk_queue.put(None)  # Signal end even on error
        
        # Start sync streaming in background thread
        thread = threading.Thread(target=run_sync_stream)
        thread.daemon = True
        thread.start()
        
        # Yield chunks as they become available
        while True:
            try:
                # Wait for next chunk with timeout to avoid hanging
                chunk = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: chunk_queue.get(timeout=30)
                )
                
                if chunk is None:  # End of stream signal
                    if exception_holder[0]:
                        raise exception_holder[0]
                    break
                    
                yield chunk
                
            except queue.Empty:
                logger.error("Voice streaming timeout - no chunks received in 30s")
                break
            except Exception as e:
                logger.error(f"Voice streaming error: {e}")
                break
    
    async def list_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get all available ElevenLabs voices
        Task 2.2.3: Get all ElevenLabs voices
        """
        if not self.client:
            # Return default voice as fallback when API not available
            return [{
                "voice_id": self.default_voice_id,
                "name": "Sarah",
                "category": "premade",
                "description": "Default voice (API not configured)",
                "labels": {},
                "preview_url": None
            }]
            
        try:
            voices = self.client.voices.get_all()
            
            voice_list = []
            for voice in voices.voices:
                voice_info = {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                    "description": getattr(voice, 'description', ''),
                    "labels": getattr(voice, 'labels', {}),
                    "preview_url": getattr(voice, 'preview_url', None)
                }
                voice_list.append(voice_info)
            
            logger.info(f"Retrieved {len(voice_list)} available voices")
            return voice_list
            
        except Exception as e:
            logger.error(f"Failed to fetch available voices: {str(e)}")
            # Return default voice as fallback
            return [{
                "voice_id": self.default_voice_id,
                "name": "Sarah",
                "category": "premade",
                "description": "Default voice",
                "labels": {},
                "preview_url": None
            }]
    
    async def preview_voice(self, voice_id: str, text: str = None) -> bytes:
        """
        Generate 3-second voice preview
        Task 2.2.4: 3-second preview
        """
        if not self.client:
            raise HTTPException(
                status_code=503,
                detail="Voice preview is not available - ElevenLabs API key not configured"
            )
            
        preview_text = text or "Hello! I'm excited to help you today. This is a preview of my voice."
        
        try:
            # Use convert method for non-streaming preview
            # Note: model_id parameter removed as per current ElevenLabs API
            audio_stream = self.client.text_to_speech.convert(
                text=preview_text,
                voice_id=voice_id,
                output_format="mp3_22050_32"
            )
            
            # Convert generator to bytes
            audio_data = b"".join(audio_stream)
            logger.info(f"Generated voice preview for voice {voice_id}")
            return audio_data
            
        except Exception as e:
            logger.error(f"Failed to generate voice preview for {voice_id}: {str(e)}")
            raise
    
    async def get_persona_voice_settings(self, persona_id: str, db) -> Dict[str, Any]:
        """
        Get voice settings for a specific persona
        Returns default settings if persona has no custom voice
        """
        try:
            # Use async SQLAlchemy for AsyncSession
            from sqlalchemy import select
            
            # Query PersonaSettings using async session
            result = await db.execute(
                select(PersonaSettings).where(PersonaSettings.persona_id == persona_id)
            )
            settings = result.scalar_one_or_none()
            
            if settings and settings.voice_id:
                return {
                    "voice_id": settings.voice_id,
                    "voice_name": settings.voice_name or "Unknown",
                    "voice_settings": settings.voice_settings or self._get_default_voice_settings()
                }
            else:
                # Return default voice settings
                return {
                    "voice_id": self.default_voice_id,
                    "voice_name": "Sarah",
                    "voice_settings": self._get_default_voice_settings()
                }
                
        except Exception as e:
            logger.error(f"Failed to get persona voice settings for {persona_id}: {str(e)}")
            # Return default as fallback
            return {
                "voice_id": self.default_voice_id,
                "voice_name": "Sarah",
                "voice_settings": self._get_default_voice_settings()
            }
    
    async def stream_persona_voice(
        self, 
        persona_id: str, 
        text: str, 
        db: AsyncSession
    ) -> AsyncIterator[bytes]:
        """
        Stream voice generation using persona's specific voice settings
        This is the main method that will be called from the API
        """
        voice_config = await self.get_persona_voice_settings(persona_id, db)
        
        async for chunk in self.stream_voice(
            text=text,
            voice_id=voice_config["voice_id"],
            voice_settings=voice_config["voice_settings"]
        ):
            yield chunk
    
    def _get_default_voice_settings(self) -> Dict[str, Any]:
        """Default voice settings as specified in roadmap"""
        return {
            "stability": 0.5,  # Convert from percentage (50) to decimal (0.5)
            "similarity_boost": 0.75,  # Convert from percentage (75) to decimal (0.75)
            "style": 0.0,  # Already correct (0 = 0.0)
            "use_speaker_boost": True
        }


# Global voice service instance
voice_service = VoiceService() 