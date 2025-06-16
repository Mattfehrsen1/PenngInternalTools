from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Boolean, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class JobStatus(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"  # New simplified state (replaces COMPLETED)
    COMPLETED = "completed"  # Keep for backwards compatibility
    FAILED = "failed"

class MessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class PromptLayer(enum.Enum):
    SYSTEM = "system"
    RAG = "rag"
    USER = "user"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Persona(Base):
    __tablename__ = "personas"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String, nullable=False)  # 'pdf', 'text'
    source_filename = Column(String, nullable=True)
    namespace = Column(String, unique=True, nullable=False)  # Pinecone namespace
    chunk_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata
    elevenlabs_agent_id = Column(String(255), nullable=True)  # ElevenLabs agent ID for voice conversations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    settings = relationship("PersonaSettings", back_populates="persona", uselist=False)

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    persona_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    total_files = Column(Integer, nullable=False)
    processed_files = Column(Integer, default=0)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    error_message = Column(Text, nullable=True)  # Store error details for failed jobs
    job_metadata = Column(JSON, nullable=True)  # file details, results, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    persona_id = Column(String, nullable=True)
    action = Column(String, nullable=False)  # 'embed', 'chat'
    model = Column(String, nullable=True)  # 'gpt-4o', 'claude-3', etc.
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Integer, default=0)  # Store in cents
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CloneQuality(Base):
    __tablename__ = "clone_quality"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    test_id = Column(String, nullable=False)  # Reference to test case
    persona_type = Column(String, nullable=False)  # 'default', 'technical', 'creative'
    prompt_version = Column(String, nullable=False)  # Prompt version used
    query = Column(Text, nullable=False)  # Test query
    response = Column(Text, nullable=False)  # AI response
    overall_score = Column(Integer, nullable=False)  # 1-10 score * 100 (for precision)
    accuracy_score = Column(Integer, nullable=False)  # 1-10 score * 100
    relevance_score = Column(Integer, nullable=False)  # 1-10 score * 100
    tone_score = Column(Integer, nullable=False)  # 1-10 score * 100
    citations_score = Column(Integer, nullable=False)  # 1-10 score * 100
    judge_feedback = Column(Text, nullable=True)  # LLM judge feedback
    judge_reasoning = Column(Text, nullable=True)  # LLM judge reasoning
    test_metadata = Column(JSON, nullable=True)  # Additional test data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, index=True)
    persona_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    thread_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)  # Array of {text, source, page}
    token_count = Column(Integer, nullable=True)
    model = Column(String, nullable=True)  # e.g., 'gpt-4o'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    persona_id = Column(String, nullable=True, index=True)  # NULL for system prompts
    layer = Column(Enum(PromptLayer), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)  # e.g., 'default', 'technical_expert'
    content = Column(Text, nullable=False)  # The actual prompt content
    version = Column(Integer, nullable=False)  # Auto-increment per name
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    author_id = Column(String, nullable=False, index=True)  # FK to users.id
    commit_message = Column(String, nullable=True)  # Optional change description
    parent_version_id = Column(String, ForeignKey("prompt_versions.id"), nullable=True)  # FK to self
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Self-referential relationship for version tree
    parent_version = relationship("PromptVersion", remote_side=[id])
    
    __table_args__ = (
        # Unique constraint on name and version
        # This ensures version numbers are unique per prompt name
    )

class PersonaSettings(Base):
    __tablename__ = "persona_settings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    voice_id = Column(String, nullable=True)  # ElevenLabs voice ID
    voice_settings = Column(JSON, nullable=True)  # speed, pitch, stability, etc.
    default_model = Column(String, nullable=True)  # 'gpt-4o', 'claude-3', etc.
    temperature = Column(Integer, nullable=True)  # 0-200 (stored as int, divided by 100)
    max_tokens = Column(Integer, nullable=True)  # max tokens for responses
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to persona
    persona = relationship("Persona", back_populates="settings")
