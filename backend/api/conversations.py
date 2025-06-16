from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import Conversation, Message, Persona
from api.auth import get_current_user, User
from services.conversation_service import ConversationService

router = APIRouter()

# Request/Response models
class CreateConversationRequest(BaseModel):
    persona_id: str
    title: Optional[str] = None

class CreateConversationResponse(BaseModel):
    thread_id: str
    title: str
    persona_id: str
    created_at: datetime

class ConversationSummary(BaseModel):
    id: str
    title: str
    persona_name: str
    persona_id: str
    last_message_at: Optional[datetime]
    message_count: int
    created_at: datetime

class ConversationListResponse(BaseModel):
    conversations: List[ConversationSummary]
    has_more: bool

class ConversationDetail(BaseModel):
    id: str
    title: str
    persona_id: str
    persona_name: str
    persona_description: Optional[str]
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: Optional[List] = None
    token_count: Optional[int] = None
    model: Optional[str] = None
    created_at: datetime

class ConversationDetailResponse(BaseModel):
    conversation: ConversationDetail
    messages: List[MessageResponse]
    persona: dict

class MessagesResponse(BaseModel):
    messages: List[MessageResponse]
    has_more: bool

@router.post("", status_code=201, response_model=CreateConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation with specified persona"""
    
    # Verify persona exists and belongs to user
    result = await db.execute(
        select(Persona).where(
            Persona.id == request.persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    
    if not persona:
        raise HTTPException(
            status_code=404,
            detail="Persona not found"
        )
    
    # Create conversation
    conversation = await ConversationService.create_conversation(
        user_id=current_user.id,
        persona_id=request.persona_id,
        title=request.title,
        db=db
    )
    
    return CreateConversationResponse(
        thread_id=conversation.id,
        title=conversation.title,
        persona_id=conversation.persona_id,
        created_at=conversation.created_at
    )

@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(20, le=100),
    before: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's conversations with pagination"""
    
    # Get conversations with persona info
    conversations = await ConversationService.list_conversations(
        user_id=current_user.id,
        limit=limit + 1,  # Get one extra to check if there are more
        before=before,
        db=db
    )
    
    has_more = len(conversations) > limit
    if has_more:
        conversations = conversations[:limit]
    
    # Get persona names and message counts
    conversation_summaries = []
    for conv in conversations:
        # Get persona info
        persona_result = await db.execute(
            select(Persona.name).where(Persona.id == conv.persona_id)
        )
        persona_name = persona_result.scalar_one_or_none() or "Unknown Persona"
        
        # Count messages
        message_count_result = await db.execute(
            select(func.count(Message.id)).where(Message.thread_id == conv.id)
        )
        message_count = message_count_result.scalar_one_or_none() or 0
        
        conversation_summaries.append(ConversationSummary(
            id=conv.id,
            title=conv.title,
            persona_name=persona_name,
            persona_id=conv.persona_id,
            last_message_at=conv.last_message_at,
            message_count=message_count,
            created_at=conv.created_at
        ))
    
    return ConversationListResponse(
        conversations=conversation_summaries,
        has_more=has_more
    )

@router.get("/{thread_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation details with initial messages"""
    
    # Get conversation with ownership verification
    conversation = await ConversationService.get_conversation(
        thread_id=thread_id,
        user_id=current_user.id,
        db=db
    )
    
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    
    # Get persona details
    persona_result = await db.execute(
        select(Persona).where(Persona.id == conversation.persona_id)
    )
    persona = persona_result.scalar_one_or_none()
    
    if not persona:
        raise HTTPException(
            status_code=404,
            detail="Associated persona not found"
        )
    
    # Get initial messages (most recent 50)
    messages = await ConversationService.get_messages(
        thread_id=thread_id,
        user_id=current_user.id,
        limit=50,
        db=db
    )
    
    # Convert to response format
    message_responses = [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            citations=msg.citations,
            token_count=msg.token_count,
            model=msg.model,
            created_at=msg.created_at
        )
        for msg in reversed(messages)  # Reverse to show oldest first
    ]
    
    conversation_detail = ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        persona_id=conversation.persona_id,
        persona_name=persona.name,
        persona_description=persona.description,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )
    
    persona_dict = {
        "id": persona.id,
        "name": persona.name,
        "description": persona.description,
        "namespace": persona.namespace,
        "chunk_count": persona.chunk_count
    }
    
    return ConversationDetailResponse(
        conversation=conversation_detail,
        messages=message_responses,
        persona=persona_dict
    )

@router.get("/{thread_id}/messages", response_model=MessagesResponse)
async def get_conversation_messages(
    thread_id: str,
    limit: int = Query(50, le=100),
    before: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated message history for a conversation"""
    
    # Get messages with pagination
    messages = await ConversationService.get_messages(
        thread_id=thread_id,
        user_id=current_user.id,
        limit=limit + 1,  # Get one extra to check if there are more
        before=before,
        db=db
    )
    
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]
    
    # Convert to response format
    message_responses = [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            citations=msg.citations,
            token_count=msg.token_count,
            model=msg.model,
            created_at=msg.created_at
        )
        for msg in reversed(messages)  # Reverse to show oldest first in chat
    ]
    
    return MessagesResponse(
        messages=message_responses,
        has_more=has_more
    )

@router.put("/{thread_id}/title")
async def update_conversation_title(
    thread_id: str,
    title: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update conversation title"""
    
    conversation = await ConversationService.update_conversation_title(
        thread_id=thread_id,
        user_id=current_user.id,
        title=title,
        db=db
    )
    
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    
    return {
        "thread_id": conversation.id,
        "title": conversation.title,
        "message": "Title updated successfully"
    }

@router.delete("/{thread_id}", status_code=204)
async def delete_conversation(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation and all its messages"""
    
    success = await ConversationService.delete_conversation(
        thread_id=thread_id,
        user_id=current_user.id,
        db=db
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    
    # Return 204 No Content as specified in requirements
    return 