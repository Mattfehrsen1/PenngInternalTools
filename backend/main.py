from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from os import getenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

# Read allowed origins from environment, defaulting to FRONTEND_URL
origins_string = getenv(
    'ALLOWED_ORIGINS',
    getenv('FRONTEND_URL', 'http://localhost:3000,http://localhost:3001')
)
ALLOWED_ORIGINS = [origin.strip() for origin in origins_string.split(',')]

# Import routers (will be created next)
from api.auth import router as auth_router
from api.persona import router as persona_router
from api.chat import router as chat_router
from api.conversations import router as conversations_router
from api.prompts import router as prompts_router
from api.documents import router as documents_router
from api.voice import router as voice_router
from api.elevenlabs_functions import router as elevenlabs_router

from test_sse_endpoint import router as test_sse_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Clone Advisor API...")
    yield
    # Shutdown
    print("Shutting down Clone Advisor API...")

# Create FastAPI app
app = FastAPI(
    title="Clone Advisor API",
    version="0.1.0",
    description="RAG-powered chat API for document clones",
    lifespan=lifespan
)

# Configure rate limiting (Phase 4.2.1)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "clone-advisor-api"
    }

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(persona_router, prefix="/persona", tags=["persona"])  # Legacy singular route

# Add routes for Next.js rewrite compatibility (frontend /api/personas -> backend /personas)
app.include_router(persona_router, prefix="/personas", tags=["personas-rewrite"])
app.include_router(documents_router, prefix="/personas", tags=["documents-rewrite"])

# Add API prefix for direct backend access (optional)
app.include_router(persona_router, prefix="/api/personas", tags=["api-personas"])
app.include_router(documents_router, prefix="/api/personas", tags=["api-documents"])

# Voice API endpoints - Add both with and without /api prefix for Next.js compatibility
app.include_router(voice_router, tags=["voice"])  # Voice router already has /api prefix (for direct access)

# Create voice router without /api prefix for Next.js rewrite compatibility
from api.voice import router as base_voice_router
from fastapi import APIRouter
voice_router_no_api = APIRouter()

# Import the voice endpoints and mount them without the /api prefix
from api.voice import (
    stream_persona_voice, list_available_voices
)

# Mount voice endpoints without /api prefix for Next.js compatibility
voice_router_no_api.add_api_route(
    "/personas/{persona_id}/voice/stream", 
    stream_persona_voice, 
    methods=["POST"]
)
voice_router_no_api.add_api_route(
    "/voices", 
    list_available_voices, 
    methods=["GET"]
)

app.include_router(voice_router_no_api, tags=["voice-rewrite"])

# Note: voice_simple_router was removed - using main voice router instead

app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(chat_router, prefix="/api/chat", tags=["api-chat"])  # Add API prefix for chat
app.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
app.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
app.include_router(elevenlabs_router, tags=["elevenlabs"])
app.include_router(test_sse_router, prefix="/test", tags=["test"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
