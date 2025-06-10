from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, AsyncIterator
import json
import logging
import asyncio
import tiktoken

from database import get_db
from models import Persona, UsageLog
from api.auth import get_current_user, User
from services.pinecone_client import get_pinecone_client
from services.embedder import Embedder
from services.llm_router import get_llm_router

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response models
class ChatRequest(BaseModel):
    persona_id: str
    question: str
    model: str = "auto"
    k: int = 6

class ChatMessage(BaseModel):
    role: str
    content: str

# Token counting
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Count tokens in text"""
    return len(encoding.encode(text))

async def stream_chat_response(
    request: ChatRequest,
    current_user: User,
    db: AsyncSession
) -> AsyncIterator[str]:
    """
    Stream chat response with citations
    
    Yields SSE events with:
    - token: Individual tokens
    - citations: Source citations
    - done: Completion signal
    - error: Error messages
    """
    # Track if we need to close the session at the end
    should_close_session = False
    
    try:
        # Get persona
        stmt = select(Persona).where(
            Persona.id == request.persona_id,
            Persona.user_id == current_user.id
        )
        result = await db.execute(stmt)
        persona = result.scalar_one_or_none()
        
        if not persona:
            yield {
                "event": "error",
                "data": json.dumps({"error": "Persona not found"})
            }
            return
        
        # Check if persona is ready
        pinecone_client = get_pinecone_client()
        exists, vector_count = await pinecone_client.check_namespace_exists(persona.namespace)
        
        if not exists or vector_count == 0:
            yield {
                "event": "error", 
                "data": json.dumps({"error": "Persona not ready. Please wait for processing to complete."})
            }
            return
        
        # Embed the question
        embedder = Embedder()
        query_embedding = await embedder.embed_query(request.question)
        
        # Search for relevant chunks
        chunks = await pinecone_client.similarity_search(
            namespace=persona.namespace,
            query_embedding=query_embedding,
            k=request.k
        )
        
        if not chunks:
            yield {
                "event": "error",
                "data": json.dumps({"error": "No relevant content found"})
            }
            return
        
        # Send citations first
        citations = []
        for i, chunk in enumerate(chunks):
            citations.append({
                "id": i + 1,
                "text": chunk["metadata"].get("text", "")[:200] + "...",
                "source": chunk["metadata"].get("source", ""),
                "score": chunk["score"]
            })
        
        yield {
            "event": "citations",
            "data": json.dumps(citations)
        }
        
        # Create RAG prompt
        llm_router = get_llm_router()
        prompt = await llm_router.create_rag_prompt(
            question=request.question,
            chunks=chunks,
            persona_name=persona.name,
            style=persona.description or "helpful and informative"
        )
        
        # Count input tokens
        input_tokens = count_tokens(prompt)
        output_tokens = 0
        full_response = []
        
        # Stream LLM response
        async for token in llm_router.call_llm(
            prompt=prompt,
            model=request.model,
            temperature=0.7,
            max_tokens=2000
        ):
            full_response.append(token)
            output_tokens = count_tokens(''.join(full_response))
            yield {
                "event": "token",
                "data": json.dumps({"token": token})
            }
            
        # Log usage
        cost_info = llm_router.estimate_cost(
            model=request.model if request.model != "auto" else "gpt-4o",
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        usage_log = UsageLog(
            user_id=current_user.id,
            persona_id=request.persona_id,
            action="chat",
            model=request.model if request.model != "auto" else "gpt-4o",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=int(cost_info["total_cost"] * 100),  # Store in cents
            metadata={
                "question": request.question[:100],
                "chunk_count": len(chunks),
                "response_length": len(''.join(full_response))
            }
        )
        db.add(usage_log)
        await db.commit()
        
        # Send completion signal
        yield {
            "event": "done",
            "data": json.dumps({"status": "complete", "tokens": output_tokens})
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }
    finally:
        # Close session if we opened it
        if should_close_session and db:
            await db.close()

@router.post("")
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream chat responses via Server-Sent Events (SSE)
    
    Events:
    - citations: Array of source citations
    - token: Individual response tokens
    - done: Completion signal with token count
    - error: Error messages
    """
    return EventSourceResponse(
        stream_chat_response(request, current_user, db),
        media_type="text/event-stream"
    )

@router.get("/history/{persona_id}")
async def get_chat_history(
    persona_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat history for a persona"""
    # Verify persona ownership
    stmt = select(Persona).where(
        Persona.id == persona_id,
        Persona.user_id == current_user.id
    )
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()
    
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Get usage logs
    stmt = select(UsageLog).where(
        UsageLog.user_id == current_user.id,
        UsageLog.persona_id == persona_id,
        UsageLog.action == "chat"
    ).order_by(UsageLog.created_at.desc()).limit(limit)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    history = []
    for log in logs:
        history.append({
            "id": log.id,
            "question": log.metadata.get("question", "") if log.metadata else "",
            "model": log.model,
            "tokens": log.output_tokens,
            "cost_cents": log.cost_usd,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return {"history": history}
