import os
import secrets
from typing import Optional
from fastapi import HTTPException, Header
from dotenv import load_dotenv

load_dotenv()

class ElevenLabsAuth:
    """Authentication service for ElevenLabs function calls"""
    
    def __init__(self):
        self.service_token = os.getenv("ELEVENLABS_SERVICE_TOKEN")
        if not self.service_token:
            # Generate a secure token if not set
            self.service_token = secrets.token_urlsafe(32)
            print(f"⚠️  ELEVENLABS_SERVICE_TOKEN not found in .env")
            print(f"Generated token: {self.service_token}")
            print("Please add this to your .env file as ELEVENLABS_SERVICE_TOKEN")
    
    def verify_service_token(self, token: str) -> bool:
        """Verify the service token matches our expected token"""
        return token == self.service_token

def get_elevenlabs_auth() -> ElevenLabsAuth:
    """Dependency function to get ElevenLabs auth instance"""
    return ElevenLabsAuth() 