from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel, validator
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from database import get_db
from services.elevenlabs_auth import get_elevenlabs_auth, ElevenLabsAuth
from services.cache_service import cache_service
from api.chat import ChatRequest
from services.rag_service import RAGService
from models import Persona
import logging
import asyncio
import time
from functools import wraps
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# Step 4.2.1: Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/elevenlabs", tags=["elevenlabs"])

# Step 4.2.2: Retry Logic Implementation
def retry_on_failure(max_retries=3, delay=1, backoff=2):
    """
    Retry decorator for handling temporary failures
    Implements exponential backoff as per Phase 4.2.2
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logger.error(f"Function {func.__name__} failed after {max_retries} attempts: {str(e)}")
                        raise e
                    
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator

class FunctionCallRequest(BaseModel):
    function_name: str
    parameters: Dict[str, Any]
    conversation_id: Optional[str] = None
    
    # Step 4.2.1: Enhanced validation
    @validator('function_name')
    def validate_function_name(cls, v):
        allowed_functions = ['query_persona_knowledge']
        if v not in allowed_functions:
            raise ValueError(f'Function {v} not allowed')
        return v
    
    @validator('parameters')
    def validate_parameters(cls, v):
        if 'query' in v and len(v.get('query', '')) > 1000:
            raise ValueError('Query too long (max 1000 characters)')
        return v

class FunctionCallResponse(BaseModel):
    result: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None

# Step 4.2.1 & 4.2.2: Enhanced RAG function with retry logic and comprehensive fallbacks
# Step 4.3: Redis Caching Integration for performance optimization
@retry_on_failure(max_retries=3, delay=1, backoff=2)
async def query_persona_knowledge(query: str, persona_id: str, db: AsyncSession) -> Dict[str, Any]:
    """
    Query the persona's knowledge base using the existing RAG system
    Includes retry logic, comprehensive error handling, and Redis caching per Phase 4.2-4.3
    """
    start_time = time.time()
    
    try:
        # 🎯 PERSONA MAPPING FIX: Handle "default" persona_id by mapping to first persona with documents
        actual_persona_id = persona_id
        
        if persona_id == "default":
            logger.info("🔄 Mapping 'default' persona_id to first persona with completed files...")
            try:
                # Query for the persona with the most completed files (our Alex Hormozi persona)
                from models import IngestionJob
                result = await db.execute(text("""
                    SELECT p.id, p.name, p.namespace, COUNT(ij.id) as file_count
                    FROM personas p 
                    LEFT JOIN ingestion_jobs ij ON p.id = ij.persona_id 
                    WHERE ij.status = 'COMPLETED' 
                    GROUP BY p.id, p.name, p.namespace
                    HAVING COUNT(ij.id) > 0 
                    ORDER BY file_count DESC 
                    LIMIT 1;
                """))
                
                best_persona_row = result.fetchone()
                if best_persona_row:
                    actual_persona_id = best_persona_row.id
                    logger.info(f"✅ Mapped 'default' → '{best_persona_row.name}' ({actual_persona_id}) with {best_persona_row.file_count} files")
                else:
                    logger.warning("⚠️ No personas found with completed files, using original persona_id")
                    
            except Exception as e:
                logger.error(f"Failed to map default persona: {str(e)}")
                # Continue with original persona_id if mapping fails
        
        # 🚀 CACHE CHECK: Now check cache with the actual persona ID (after mapping)
        cached_response = await cache_service.get_cached_response(query, actual_persona_id)
        if cached_response:
            # Add fresh latency metrics while preserving cached content
            cached_response["cache_hit"] = True
            cached_response["total_latency_ms"] = round((time.time() - start_time) * 1000, 2)
            logger.info(f"🚀 Cache hit! Query served in {cached_response['total_latency_ms']:.2f}ms (was {cached_response.get('latency_ms', 'unknown')}ms)")
            return cached_response
        
        # Step 4.2.1: Verify persona exists with detailed error handling  
        try:
            result = await db.execute(select(Persona).filter(Persona.id == actual_persona_id))
            persona = result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database query failed for persona {actual_persona_id}: {str(e)}")
            return {
                "error": "Database connection issue",
                "content": "I'm experiencing database connectivity issues. Please try again in a moment."
            }
        
        if not persona:
            return {
                "error": "Persona not found",
                "content": f"I couldn't find the requested persona (ID: {actual_persona_id}). Please check the persona ID."
            }
        
        # Step 4.2.1: Use RAG service with enhanced error handling
        try:
            rag_service = RAGService()
            relevant_docs = await rag_service.query_documents(
                query=query,
                namespace=persona.namespace,
                top_k=5
            )
        except Exception as e:
            logger.error(f"RAG service failed for persona {persona_id}: {str(e)}")
            # Fallback response when RAG fails
            return {
                "error": "Knowledge base temporarily unavailable",
                "content": f"I'm having trouble accessing my knowledge base right now. However, I can tell you that I'm {persona.name}. Please try your question again in a moment.",
                "persona_name": persona.name
            }
        
        # Step 4.2.3: Format response with user-friendly content
        if relevant_docs:
            # Limit content length for voice (Step 4.3.2)
            content_parts = []
            citations = []
            
            for i, doc in enumerate(relevant_docs):
                citation_num = i + 1
                # Truncate individual doc text for voice
                doc_text = doc['text']
                if len(doc_text) > 200:
                    doc_text = doc_text[:200] + "..."
                
                content_parts.append(f"According to source {citation_num}: {doc_text}")
                citations.append({
                    "text": doc['text'],  # Full text for citations
                    "source": doc.get('source', 'Unknown'),
                    "page": doc.get('page', 1),
                    "citation_number": citation_num
                })
            
            content = "\n\n".join(content_parts)
            
            # Step 4.3.2: Limit total response length for voice
            if len(content) > 500:
                # Find last complete sentence within limit
                truncated = content[:500]
                last_period = truncated.rfind('.')
                if last_period > 350:  # Keep at least 70% of content
                    content = truncated[:last_period + 1]
                else:
                    content = truncated + "..."
            
            # Step 4.3.4: Log performance metrics
            latency = (time.time() - start_time) * 1000
            logger.info(f"RAG query completed in {latency:.2f}ms for persona {persona.name}")
            
            response = {
                "content": content,
                "citations": citations,
                "persona_name": persona.name,
                "latency_ms": round(latency, 2),
                "cache_hit": False
            }
            
            # Step 4.3.2: Cache successful response for future queries
            await cache_service.cache_response(query, actual_persona_id, response, ttl_minutes=5)
            
            return response
        else:
            response = {
                "content": f"I don't have specific information about that in my knowledge base. However, as {persona.name}, I'm here to help. Could you try rephrasing your question or ask about something else?",
                "citations": [],
                "persona_name": persona.name,
                "cache_hit": False
            }
            
            # Step 4.3.2: Cache "no results" response to avoid repeated processing
            await cache_service.cache_response(query, actual_persona_id, response, ttl_minutes=2)  # Shorter TTL for "no results"
            
            return response
            
    except Exception as e:
        # Step 4.2.4: Comprehensive error logging
        logger.error(f"Unexpected error in query_persona_knowledge: {str(e)}", exc_info=True)
        return {
            "error": f"Unexpected error: {type(e).__name__}",
            "content": "I encountered an unexpected issue. Please try asking your question again."
        }

@router.post("/function-call", response_model=FunctionCallResponse)
@limiter.limit("60/minute")  # Step 4.2.1: Rate limiting - 60 calls per minute per IP
async def handle_function_call(
    request: Request,  # Required for rate limiter
    function_request: FunctionCallRequest,
    x_service_token: str = Header(alias="X-Service-Token"),
    auth: ElevenLabsAuth = Depends(get_elevenlabs_auth),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle function calls from ElevenLabs agents
    Enhanced with comprehensive error handling, validation, and rate limiting per Phase 4.2
    """
    start_time = time.time()
    
    try:
        # Step 4.2.1: Enhanced authentication with detailed logging
        if not auth.verify_service_token(x_service_token):
            logger.warning(f"Invalid service token attempt from {get_remote_address(request)}")
            raise HTTPException(401, "Invalid service token")
        
        logger.info(f"🚀 ELEVENLABS WEBHOOK CALLED: {function_request.function_name} with params: {function_request.parameters}")
        print(f"🚀 ELEVENLABS WEBHOOK CALLED: {function_request.function_name} with params: {function_request.parameters}")
        
        # Step 4.2.1: Enhanced parameter validation
        if function_request.function_name == "query_persona_knowledge":
            query = function_request.parameters.get("query")
            persona_id = function_request.parameters.get("persona_id")
            
            # Detailed parameter validation
            if not query:
                return FunctionCallResponse(
                    result={"error": "Missing required parameter: query", "content": "Please provide a query to search for."},
                    success=False
                )
            
            if not persona_id:
                return FunctionCallResponse(
                    result={"error": "Missing required parameter: persona_id", "content": "Please specify which persona to query."},
                    success=False
                )
            
            # Query length validation (already handled by pydantic validator, but double-check)
            if len(query) > 1000:
                return FunctionCallResponse(
                    result={"error": "Query too long", "content": "Please shorten your question to under 1000 characters."},
                    success=False
                )
            
            # Execute query with enhanced error handling
            try:
                result = await query_persona_knowledge(query, persona_id, db)
                
                # Step 4.3.4: Log performance metrics
                total_latency = (time.time() - start_time) * 1000
                logger.info(f"Total function call latency: {total_latency:.2f}ms")
                
                print(f"✅ RETURNING TO ELEVENLABS: success=True, content_length={len(result.get('content', ''))}, persona={result.get('persona_name', 'unknown')}")
                return FunctionCallResponse(result=result, success=True)
                
            except Exception as e:
                logger.error(f"Knowledge query failed: {str(e)}", exc_info=True)
                return FunctionCallResponse(
                    result={
                        "error": "Knowledge query failed", 
                        "content": "I'm having trouble processing your request right now. Please try again."
                    },
                    success=False
                )
            
        else:
            logger.warning(f"Unknown function requested: {function_request.function_name}")
            raise HTTPException(400, f"Unknown function: {function_request.function_name}")
            
    except HTTPException:
        raise
    except RateLimitExceeded:
        logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
        raise
    except Exception as e:
        # Step 4.2.4: Comprehensive error logging and monitoring
        logger.error(f"Function call handler failed: {str(e)}", exc_info=True)
        return FunctionCallResponse(
            result={
                "error": "Internal server error", 
                "content": "I encountered an unexpected issue. Please try again in a moment."
            },
            success=False
        )

@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get Redis cache performance statistics
    Step 4.3.3: Monitor cache hit rates and performance metrics for Cape Town deployment
    """
    try:
        stats = cache_service.get_cache_stats()
        return {
            "cache_stats": stats,
            "success": True,
            "message": "Cache statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        return {
            "cache_stats": {"enabled": False, "error": str(e)},
            "success": False,
            "message": "Failed to retrieve cache statistics"
        }