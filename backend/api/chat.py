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
from services.prompt_service import prompt_service
from services.persona_prompt_service import persona_prompt_service
from services.testing_service import testing_service
from services.llm_judge_service import llm_judge_service
from services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter()

# Request/Response models
class ChatRequest(BaseModel):
    persona_id: str
    question: str
    model: str = "auto"
    k: int = 6
    thread_id: Optional[str] = None  # Optional thread ID for conversation persistence

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
    Stream chat response with citations and optional conversation persistence
    
    Yields SSE events with:
    - thread_info: Thread ID for conversation (if persistence enabled)
    - token: Individual tokens
    - citations: Source citations
    - done: Completion signal
    - error: Error messages
    """
    # Track if we need to close the session at the end
    should_close_session = False
    conversation = None
    
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
        
        # Handle conversation persistence
        if request.thread_id:
            # Verify conversation exists and belongs to user
            conversation = await ConversationService.get_conversation(
                thread_id=request.thread_id,
                user_id=current_user.id,
                db=db
            )
            if not conversation:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Thread not found"})
                }
                return
        else:
            # Create new conversation if none provided
            conversation = await ConversationService.create_conversation_with_first_message(
                user_id=current_user.id,
                persona_id=request.persona_id,
                first_message=request.question,
                db=db
            )
        
        # Send thread info
        yield {
            "event": "thread_info",
            "data": json.dumps({
                "thread_id": conversation.id,
                "title": conversation.title
            })
        }
        
        # Check if persona is ready
        pinecone_client = get_pinecone_client()
        exists, vector_count = await pinecone_client.check_namespace_exists(persona.namespace)
        
        # Initialize variables
        citations = []
        formatted_chunks = []
        chunks = []
        
        # Handle personas with no documents gracefully
        if not exists or vector_count == 0:
            logger.info(f"Persona {persona.name} has no documents, using fallback prompt without RAG")
            
            # Send empty citations for consistency
            yield {
                "event": "citations",
                "data": json.dumps([])
            }
            
            # Use fallback prompt without RAG context
            formatted_chunks = []  # Empty chunks for personas without documents
        else:
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
                # Send empty citations if no relevant chunks found
                yield {
                    "event": "citations", 
                    "data": json.dumps([])
                }
            else:
                # Send citations first
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
                
                # Prepare chunks for the prompt service
                for chunk in chunks:
                    formatted_chunks.append({
                        "text": chunk["metadata"].get("text", ""),
                        "source": chunk["metadata"].get("source", ""),
                        "source_type": chunk["metadata"].get("source_type", "document"),
                        "metadata": chunk["metadata"]
                    })
        
        # Create three-layer prompt using new prompt service
        llm_router = get_llm_router()
        
        # Get persona-specific prompts (system, rag, user)
        try:
            persona_prompts = await persona_prompt_service.get_active_prompts(
                persona_id=request.persona_id,
                db=db
            )
            
            # If no persona-specific prompts, fall back to global service
            if not any(persona_prompts.values()):
                logger.warning(f"No persona prompts found for {request.persona_id}, using fallback")
                # Determine persona type for fallback prompt selection
                persona_type = "default"
                if persona.description:
                    desc_lower = persona.description.lower()
                    if any(word in desc_lower for word in ["technical", "engineer", "developer", "expert"]):
                        persona_type = "technical"
                    elif any(word in desc_lower for word in ["creative", "writer", "content", "marketing"]):
                        persona_type = "creative"
                
                # Build fallback prompt using global service
                prompt_layers = prompt_service.build_complete_prompt(
                    persona_name=persona.name,
                    description=persona.description or "helpful and informative",
                    user_query=request.question,
                    chunks=formatted_chunks,
                    persona_type=persona_type
                )
                prompt = prompt_service.format_for_llm(prompt_layers)
            else:
                # Use persona-specific prompts - build custom prompt
                system_prompt = persona_prompts.get("system", "You are a helpful AI assistant.")
                rag_prompt = persona_prompts.get("rag", "Based on the following information:\n\n{% for chunk in chunks %}[{{loop.index}}] {{chunk.text}}\nSource: {{chunk.source}}\n{% endfor %}")
                user_prompt = persona_prompts.get("user", "USER QUESTION: {{user_query}}\n\nPlease provide a helpful response.")
                
                # Simple template rendering (replace with proper Jinja2 if needed)
                # Format chunks for inclusion
                chunks_text = ""
                for i, chunk in enumerate(formatted_chunks):
                    chunks_text += f"[{i+1}] {chunk['text']}\nSource: {chunk['source']}\n\n"
                
                # Build final prompt by combining layers
                formatted_rag = rag_prompt.replace("{% for chunk in chunks %}", "").replace("{% endfor %}", "").replace("{{loop.index}}", "").replace("{{chunk.text}}", "").replace("{{chunk.source}}", "")
                formatted_user = user_prompt.replace("{{user_query}}", request.question)
                
                # Create complete prompt with persona's specific prompts
                prompt = f"{system_prompt}\n\n{formatted_rag}\n{chunks_text}\n{formatted_user}"
                
                logger.info(f"Using persona-specific prompts for {persona.name} (ID: {request.persona_id})")
                logger.debug(f"System prompt length: {len(system_prompt)} chars")
                logger.debug(f"RAG prompt length: {len(rag_prompt)} chars") 
                logger.debug(f"User prompt length: {len(user_prompt)} chars")
                
        except Exception as e:
            logger.error(f"Error loading persona prompts: {e}, falling back to global service")
            # Fallback to global service on error
            persona_type = "default"
            prompt_layers = prompt_service.build_complete_prompt(
                persona_name=persona.name,
                description=persona.description or "helpful and informative",
                user_query=request.question,
                chunks=formatted_chunks,
                persona_type=persona_type
            )
            prompt = prompt_service.format_for_llm(prompt_layers)
        
        # Count input tokens
        input_tokens = count_tokens(prompt)
        output_tokens = 0
        full_response = []
        
        # Save user message if this is a new conversation and we haven't added it yet
        if conversation and not request.thread_id:
            # Only add user message for new conversations since create_conversation_with_first_message already added it
            pass
        elif conversation and request.thread_id:
            # Add user message for existing conversation
            await ConversationService.add_message(
                thread_id=conversation.id,
                role="user",
                content=request.question,
                db=db
            )
        
        # Stream LLM response
        try:
            logger.info(f"Starting LLM call for persona {persona.name} with model {request.model}")
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
            
            logger.info(f"LLM call completed successfully. Generated {output_tokens} tokens.")
            
        except Exception as llm_error:
            logger.error(f"LLM call failed: {llm_error}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"error": f"AI service error: {str(llm_error)}"})
            }
            return
        
        # Save assistant response
        assistant_response = ''.join(full_response)
        if conversation:
            await ConversationService.add_message(
                thread_id=conversation.id,
                role="assistant",
                content=assistant_response,
                citations=citations,
                token_count=output_tokens,
                model=request.model if request.model != "auto" else "gpt-4o",
                db=db
            )
            
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
    - thread_info: Thread ID and title for conversation persistence
    - citations: Array of source citations
    - token: Individual response tokens
    - done: Completion signal with token count
    - error: Error messages
    """
    return EventSourceResponse(
        stream_chat_response(request, current_user, db),
        media_type="text/event-stream"
    )

@router.get("/prompts/version")
async def get_prompt_version(
    current_user: User = Depends(get_current_user)
):
    """Get current prompt version information"""
    return prompt_service.get_version_info()

@router.get("/prompts/templates")
async def get_available_templates(
    current_user: User = Depends(get_current_user)
):
    """Get available prompt templates"""
    return prompt_service.get_available_templates()

@router.post("/prompts/preview")
async def preview_prompt(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Preview a prompt with given parameters"""
    try:
        prompt_layers = prompt_service.build_complete_prompt(
            persona_name=request.get("persona_name", "Test Persona"),
            description=request.get("description", "A helpful assistant"),
            user_query=request.get("user_query", "Hello, how can you help me?"),
            chunks=request.get("chunks", []),
            persona_type=request.get("persona_type", "default")
        )
        
        return {
            "layers": {
                "system": prompt_layers.system,
                "rag_context": prompt_layers.rag_context,
                "user_query": prompt_layers.user_query
            },
            "complete_prompt": prompt_service.format_for_llm(prompt_layers)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tests/suites")
async def get_test_suites(
    current_user: User = Depends(get_current_user)
):
    """Get available test suites"""
    return {
        "available_suites": testing_service.get_available_test_suites()
    }

@router.post("/tests/run/{persona_type}")
async def run_test_suite(
    persona_type: str,
    request: dict = None,
    current_user: User = Depends(get_current_user)
):
    """Run a test suite for a specific persona type"""
    try:
        persona_name = request.get("persona_name", "Test Persona") if request else "Test Persona"
        persona_description = request.get("persona_description", "A helpful AI assistant for testing") if request else "A helpful AI assistant for testing"
        
        results = await testing_service.run_test_suite(
            persona_type=persona_type,
            persona_name=persona_name,
            persona_description=persona_description
        )
        
        summary = testing_service.get_test_summary(results)
        
        return {
            "summary": summary,
            "results": [
                {
                    "test_id": r.test_id,
                    "query": r.query,
                    "passed": r.passed,
                    "overall_score": r.overall_score,
                    "keyword_score": r.keyword_score,
                    "citation_check": r.citation_check,
                    "tone_check": r.tone_check,
                    "llm_judge_score": r.llm_judge_score,
                    "errors": r.errors
                } for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tests/single")
async def run_single_test(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Run a single test case"""
    try:
        from services.testing_service import TestCase
        
        test_case = TestCase(
            id=request.get("id", "test_001"),
            category=request.get("category", "General"),
            query=request["query"],
            expected_keywords=request.get("expected_keywords", []),
            expected_tone=request.get("expected_tone", "helpful"),
            success_criteria=request.get("success_criteria", {"min_score": 6}),
            sample_chunks=request.get("sample_chunks", [])
        )
        
        result = await testing_service.run_single_test(
            test_case=test_case,
            persona_name=request.get("persona_name", "Test Persona"),
            persona_description=request.get("persona_description", "A helpful AI assistant"),
            persona_type=request.get("persona_type", "default")
        )
        
        return {
            "test_id": result.test_id,
            "query": result.query,
            "response": result.response,
            "passed": result.passed,
            "overall_score": result.overall_score,
            "keyword_score": result.keyword_score,
            "citation_check": result.citation_check,
            "tone_check": result.tone_check,
            "llm_judge_score": result.llm_judge_score,
            "errors": result.errors
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/judge/evaluate")
async def judge_response(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Use LLM judge to evaluate a response"""
    try:
        judge_result = await llm_judge_service.judge_response(
            query=request["query"],
            response=request["response"],
            expected_tone=request.get("expected_tone", "helpful"),
            expected_keywords=request.get("expected_keywords", []),
            provided_chunks=request.get("provided_chunks", [])
        )
        
        return {
            "overall_score": judge_result.overall_score,
            "accuracy_score": judge_result.accuracy_score,
            "relevance_score": judge_result.relevance_score,
            "tone_score": judge_result.tone_score,
            "citations_score": judge_result.citations_score,
            "feedback": judge_result.feedback,
            "reasoning": judge_result.reasoning,
            "timestamp": judge_result.timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
