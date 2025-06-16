"""
Conversation Service

Handles chat persistence operations including:
- Creating and managing conversations (threads)
- Adding and retrieving messages
- Pagination and context management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from models import Conversation, Message


@asynccontextmanager
async def transaction_scope(db: AsyncSession):
    """Provide a transactional scope for database operations"""
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise


class ConversationService:
    """Service for managing conversations and messages"""
    
    @staticmethod
    async def create_conversation(
        user_id: str,
        persona_id: str,
        title: Optional[str] = None,
        db: AsyncSession = None
    ) -> Conversation:
        """Create a new conversation"""
        try:
            conversation = Conversation(
                user_id=user_id,
                persona_id=persona_id,
                title=title or "New Conversation",
                last_message_at=datetime.utcnow()
            )
            
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            
            return conversation
            
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create conversation: {str(e)}"
            )
    
    @staticmethod
    async def get_conversation(
        thread_id: str,
        user_id: str,
        db: AsyncSession
    ) -> Optional[Conversation]:
        """Get a conversation by ID, ensuring user ownership"""
        try:
            result = await db.execute(
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(
                    and_(
                        Conversation.id == thread_id,
                        Conversation.user_id == user_id
                    )
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch conversation: {str(e)}"
            )
    
    @staticmethod
    async def list_conversations(
        user_id: str,
        limit: int = 20,
        before: Optional[str] = None,
        db: AsyncSession = None
    ) -> List[Conversation]:
        """List conversations for a user with pagination"""
        try:
            query = (
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
            )
            
            # Add pagination if before parameter is provided
            if before:
                before_conversation = await db.execute(
                    select(Conversation.updated_at)
                    .where(Conversation.id == before)
                )
                before_timestamp = before_conversation.scalar_one_or_none()
                if before_timestamp:
                    query = query.where(Conversation.updated_at < before_timestamp)
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list conversations: {str(e)}"
            )
    
    @staticmethod
    async def add_message(
        thread_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        token_count: Optional[int] = None,
        model: Optional[str] = None,
        db: AsyncSession = None
    ) -> Message:
        """Add a message to a conversation"""
        try:
            async with transaction_scope(db):
                # Create the message
                message = Message(
                    thread_id=thread_id,
                    role=role,
                    content=content,
                    citations=citations,
                    token_count=token_count,
                    model=model
                )
                
                db.add(message)
                await db.flush()  # Get ID without committing
                
                # Update conversation's last_message_at
                await db.execute(
                    Conversation.__table__.update()
                    .where(Conversation.id == thread_id)
                    .values(
                        last_message_at=message.created_at,
                        updated_at=func.now()
                    )
                )
                
                await db.refresh(message)
                return message
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add message: {str(e)}"
            )
    
    @staticmethod
    async def get_messages(
        thread_id: str,
        user_id: str,
        limit: int = 50,
        before: Optional[str] = None,
        db: AsyncSession = None
    ) -> List[Message]:
        """Get messages for a conversation with pagination"""
        try:
            # Verify user owns the conversation
            conversation = await ConversationService.get_conversation(
                thread_id, user_id, db
            )
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found"
                )
            
            query = (
                select(Message)
                .where(Message.thread_id == thread_id)
                .order_by(desc(Message.created_at))
                .limit(limit)
            )
            
            # Add pagination if before parameter is provided
            if before:
                before_message = await db.execute(
                    select(Message.created_at)
                    .where(Message.id == before)
                )
                before_timestamp = before_message.scalar_one_or_none()
                if before_timestamp:
                    query = query.where(Message.created_at < before_timestamp)
            
            result = await db.execute(query)
            messages = result.scalars().all()
            
            # Return in chronological order (oldest first)
            return list(reversed(messages))
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get messages: {str(e)}"
            )
    
    @staticmethod
    async def update_conversation_title(
        thread_id: str,
        user_id: str,
        title: str,
        db: AsyncSession
    ) -> Optional[Conversation]:
        """Update conversation title"""
        try:
            # Verify user owns the conversation
            conversation = await ConversationService.get_conversation(
                thread_id, user_id, db
            )
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found"
                )
            
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(conversation)
            
            return conversation
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update conversation title: {str(e)}"
            )
    
    @staticmethod
    async def delete_conversation(
        thread_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Delete a conversation and all its messages"""
        try:
            # Verify user owns the conversation
            conversation = await ConversationService.get_conversation(
                thread_id, user_id, db
            )
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found"
                )
            
            await db.delete(conversation)
            await db.commit()
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete conversation: {str(e)}"
            )
    
    @staticmethod
    async def get_conversation_context(
        thread_id: str,
        user_id: str,
        max_messages: int = 20,
        max_tokens: int = 4000,
        db: AsyncSession = None
    ) -> List[Message]:
        """
        Get conversation context for LLM, limiting by message count and tokens.
        Returns messages in chronological order (oldest first).
        """
        try:
            # Get recent messages in reverse chronological order
            messages = await ConversationService.get_messages(
                thread_id, user_id, limit=max_messages, db=db
            )
            
            if not messages:
                return []
            
            # If we have token limits, select messages that fit
            if max_tokens > 0:
                selected_messages = []
                total_tokens = 0
                
                # Process messages from newest to oldest, but build list in reverse
                for message in reversed(messages):
                    message_tokens = message.token_count or len(message.content.split()) * 1.3
                    
                    if total_tokens + message_tokens <= max_tokens:
                        selected_messages.insert(0, message)  # Insert at beginning
                        total_tokens += message_tokens
                    else:
                        break
                
                return selected_messages
            
            return messages
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get conversation context: {str(e)}"
            )
    
    @staticmethod
    async def create_conversation_with_first_message(
        user_id: str,
        persona_id: str,
        first_message: str,
        db: AsyncSession
    ) -> Conversation:
        """Create a new conversation with an initial user message"""
        try:
            async with transaction_scope(db):
                # Generate title from first message
                title = first_message[:50] + "..." if len(first_message) > 50 else first_message
                
                # Create conversation
                conversation = Conversation(
                    user_id=user_id,
                    persona_id=persona_id,
                    title=title
                )
                db.add(conversation)
                await db.flush()  # Get ID without committing
                
                # Add first message
                message = Message(
                    thread_id=conversation.id,
                    role="user",
                    content=first_message
                )
                db.add(message)
                await db.flush()
                
                # Update conversation timestamps
                conversation.last_message_at = message.created_at
                conversation.updated_at = message.created_at
                
                await db.refresh(conversation)
                return conversation
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create conversation with message: {str(e)}"
            )


# Convenience instance
conversation_service = ConversationService() 