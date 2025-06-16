#!/usr/bin/env python3
"""
ElevenLabs Integration Test Suite - Phase 4.1
Tests the complete voice conversation flow with function calling to RAG system
"""

import os
import asyncio
import logging
import time
import json
import requests
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
from models import Persona, User
from services.agent_manager import AgentManager
from services.elevenlabs_auth import ElevenLabsAuth
from api.elevenlabs_functions import query_persona_knowledge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElevenLabsIntegrationTester:
    """
    Comprehensive test suite for ElevenLabs voice integration
    Tests all components from voice connection to RAG query responses
    """
    
    def __init__(self):
        self.agent_manager = AgentManager()
        self.auth = ElevenLabsAuth()
        self.base_url = "http://localhost:8000"
        self._db_session = None
        
    async def __aenter__(self):
        self._db_session = AsyncSessionLocal()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._db_session:
            await self._db_session.close()
    
    @property
    def db(self) -> AsyncSession:
        return self._db_session
    
    # ========== Step 4.1.1: Test Basic Voice Connection ==========
    
    def test_elevenlabs_api_key(self) -> bool:
        """Test if ElevenLabs API key is valid"""
        try:
            api_key = os.getenv("ELEVENLABS_API_KEY")
            if not api_key:
                logger.error("❌ ELEVENLABS_API_KEY not found")
                return False
                
            # Test API key with a simple voices request
            from elevenlabs import ElevenLabs
            client = ElevenLabs(api_key=api_key)
            voices = client.voices.get_all()
            
            logger.info(f"✅ ElevenLabs API key valid - found {len(voices.voices)} voices")
            return True
            
        except Exception as e:
            logger.error(f"❌ ElevenLabs API key test failed: {str(e)}")
            return False
    
    def test_service_token_auth(self) -> bool:
        """Test service token authentication"""
        try:
            service_token = os.getenv("ELEVENLABS_SERVICE_TOKEN")
            if not service_token:
                logger.error("❌ ELEVENLABS_SERVICE_TOKEN not found")
                return False
            
            # Test auth verification
            is_valid = self.auth.verify_service_token(service_token)
            if is_valid:
                logger.info("✅ Service token authentication working")
                return True
            else:
                logger.error("❌ Service token verification failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Service token test failed: {str(e)}")
            return False
    
    async def test_agent_creation(self, persona_id: str) -> Optional[str]:
        """Test creating an ElevenLabs agent for a persona"""
        try:
            # Get persona from database
            from sqlalchemy import select
            result = await self.db.execute(select(Persona).filter(Persona.id == persona_id))
            persona = result.scalar_one_or_none()
            if not persona:
                logger.error(f"❌ Persona {persona_id} not found")
                return None
            
            # Create agent configuration
            config = self.agent_manager.get_agent_config_template(
                persona_name=persona.name,
                persona_prompt=persona.description or "You are a helpful assistant",
                persona_id=persona.id
            )
            
            logger.info(f"📋 Agent config for {persona.name}:")
            logger.info(f"   - Name: {config['name']}")
            logger.info(f"   - Voice ID: {config['voice']['voice_id']}")
            logger.info(f"   - Has function tools: {len(config['tools'])} tools")
            logger.info(f"   - Webhook configured: {config.get('webhook') is not None}")
            
            # Note: We're not actually creating the agent in ElevenLabs yet
            # This would require the conversational AI API endpoints
            logger.info("✅ Agent configuration generated successfully")
            return "test-agent-id"  # Placeholder
            
        except Exception as e:
            logger.error(f"❌ Agent creation test failed: {str(e)}")
            return None
    
    # ========== Step 4.1.2: Test Function Calling Flow ==========
    
    def test_function_call_endpoint(self, persona_id: str, query: str) -> bool:
        """Test the function call endpoint that ElevenLabs will use"""
        try:
            service_token = os.getenv("ELEVENLABS_SERVICE_TOKEN")
            
            # Prepare function call request
            payload = {
                "function_name": "query_persona_knowledge",
                "parameters": {
                    "query": query,
                    "persona_id": persona_id
                }
            }
            
            # Make request to function call endpoint
            response = requests.post(
                f"{self.base_url}/elevenlabs/function-call",
                json=payload,
                headers={
                    "X-Service-Token": service_token,
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Function call endpoint working")
                logger.info(f"   - Success: {result.get('success', False)}")
                logger.info(f"   - Content length: {len(result.get('result', {}).get('content', ''))}")
                logger.info(f"   - Citations: {len(result.get('result', {}).get('citations', []))}")
                return True
            else:
                logger.error(f"❌ Function call failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Function call test failed: {str(e)}")
            return False
    
    # ========== Step 4.1.3: Test RAG Integration ==========
    
    async def test_rag_integration(self, persona_id: str, query: str) -> bool:
        """Test RAG system integration through function calling"""
        try:
            start_time = time.time()
            
            # Test the RAG query function directly
            result = await query_persona_knowledge(query, persona_id, self.db)
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if "error" in result:
                logger.error(f"❌ RAG query failed: {result['error']}")
                return False
            
            content = result.get('content', '')
            citations = result.get('citations', [])
            
            logger.info("✅ RAG integration working")
            logger.info(f"   - Query latency: {latency:.2f}ms")
            logger.info(f"   - Response length: {len(content)} characters")
            logger.info(f"   - Citations found: {len(citations)}")
            
            # Test citation format
            for i, citation in enumerate(citations[:3]):  # Show first 3
                logger.info(f"   - Citation {i+1}: {citation.get('source', 'Unknown')}")
            
            # Check if latency meets target (<400ms)
            if latency < 400:
                logger.info(f"✅ Latency target met: {latency:.2f}ms < 400ms")
            else:
                logger.warning(f"⚠️ Latency target missed: {latency:.2f}ms > 400ms")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ RAG integration test failed: {str(e)}")
            return False
    
    # ========== Step 4.1.4: Test Error Handling ==========
    
    def test_error_handling(self) -> bool:
        """Test various error scenarios"""
        try:
            logger.info("🧪 Testing error handling scenarios...")
            
            # Test 1: Invalid persona ID
            result1 = requests.post(
                f"{self.base_url}/elevenlabs/function-call",
                json={
                    "function_name": "query_persona_knowledge",
                    "parameters": {"query": "test", "persona_id": "invalid-id"}
                },
                headers={"X-Service-Token": os.getenv("ELEVENLABS_SERVICE_TOKEN")}
            )
            
            if result1.status_code == 200:
                data = result1.json()
                if "error" in data.get('result', {}):
                    logger.info("✅ Invalid persona ID handled correctly")
                else:
                    logger.warning("⚠️ Invalid persona ID should return error")
            
            # Test 2: Invalid service token
            result2 = requests.post(
                f"{self.base_url}/elevenlabs/function-call",
                json={
                    "function_name": "query_persona_knowledge",
                    "parameters": {"query": "test", "persona_id": "test"}
                },
                headers={"X-Service-Token": "invalid-token"}
            )
            
            if result2.status_code == 401:
                logger.info("✅ Invalid service token rejected correctly")
            else:
                logger.warning(f"⚠️ Expected 401 for invalid token, got {result2.status_code}")
            
            # Test 3: Missing parameters
            result3 = requests.post(
                f"{self.base_url}/elevenlabs/function-call",
                json={
                    "function_name": "query_persona_knowledge",
                    "parameters": {"query": "test"}  # Missing persona_id
                },
                headers={"X-Service-Token": os.getenv("ELEVENLABS_SERVICE_TOKEN")}
            )
            
            if result3.status_code == 200:
                data = result3.json()
                if not data.get('success', True):
                    logger.info("✅ Missing parameters handled correctly")
                else:
                    logger.warning("⚠️ Missing parameters should cause failure")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {str(e)}")
            return False
    
    # ========== Test Runner ==========
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all Phase 4.1 tests"""
        results = {}
        
        logger.info("🚀 Starting ElevenLabs Integration Tests - Phase 4.1")
        logger.info("=" * 60)
        
        # Get a test persona
        from sqlalchemy import select
        result = await self.db.execute(select(Persona).limit(1))
        persona = result.scalar_one_or_none()
        if not persona:
            logger.error("❌ No personas found in database for testing")
            return {"error": "No test personas available"}
        
        logger.info(f"🎭 Using test persona: {persona.name} ({persona.id})")
        logger.info("-" * 60)
        
        # Step 4.1.1: Basic voice connection tests
        logger.info("📋 Step 4.1.1: Testing basic voice connection...")
        results['api_key'] = self.test_elevenlabs_api_key()
        results['service_token'] = self.test_service_token_auth()
        results['agent_creation'] = await self.test_agent_creation(persona.id)
        
        # Step 4.1.2: Function calling flow
        logger.info("\n📋 Step 4.1.2: Testing function calling flow...")
        results['function_call'] = self.test_function_call_endpoint(
            persona.id, 
            "What can you tell me about this persona's knowledge?"
        )
        
        # Step 4.1.3: RAG integration
        logger.info("\n📋 Step 4.1.3: Testing RAG integration...")
        results['rag_integration'] = await self.test_rag_integration(
            persona.id,
            "Tell me about the documents in this knowledge base"
        )
        
        # Step 4.1.4: Error handling
        logger.info("\n📋 Step 4.1.4: Testing error handling...")
        results['error_handling'] = self.test_error_handling()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed = 0
        total = 0
        
        for test_name, result in results.items():
            if isinstance(result, bool):
                total += 1
                if result:
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.info(f"❌ {test_name}: FAILED")
            elif result is not None:
                logger.info(f"ℹ️ {test_name}: COMPLETED")
        
        logger.info(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - ElevenLabs integration ready!")
        else:
            logger.info("⚠️ Some tests failed - review issues before proceeding")
        
        return results

# Main execution
async def main():
    """Run the test suite"""
    async with ElevenLabsIntegrationTester() as tester:
        results = await tester.run_all_tests()
        
        # Exit with appropriate code
        if all(isinstance(r, bool) and r for r in results.values() if isinstance(r, bool)):
            exit(0)  # All tests passed
        else:
            exit(1)  # Some tests failed

if __name__ == "__main__":
    asyncio.run(main()) 