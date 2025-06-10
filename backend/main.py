from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from os import getenv

# Load environment variables
load_dotenv()

# Read allowed origins from environment, defaulting to FRONTEND_URL
ALLOWED_ORIGINS = getenv(
    'ALLOWED_ORIGINS',
    getenv('FRONTEND_URL', 'http://localhost:3000')
).split(',')

# Import routers (will be created next)
from api.auth import router as auth_router
from api.persona import router as persona_router
from api.chat import router as chat_router
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(persona_router, prefix="/persona", tags=["persona"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(test_sse_router, prefix="/test", tags=["test"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
