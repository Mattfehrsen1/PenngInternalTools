from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import io
import uuid
from typing import Optional, List
import logging
import asyncio
import hashlib
from datetime import datetime
from pydantic import BaseModel

from database import get_db
from models import Persona, IngestionJob, JobStatus, PromptVersion
from api.auth import get_current_user, User
from services.pinecone_client import get_pinecone_client
from services.chunker import TextChunker
from services.embedder import Embedder
from services.agent_service import agent_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Response models
class PersonaUploadResponse(BaseModel):
    persona_id: str
    name: str
    namespace: str
    chunks: int
    message: str

class PersonaListResponse(BaseModel):
    personas: list

class PersonaUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PersonaUpdateResponse(BaseModel):
    persona_id: str
    name: str
    description: Optional[str]
    message: str

class IngestJobResponse(BaseModel):
    job_id: str
    persona_id: str
    files_count: int
    estimated_time: str
    message: str

class JobProgressResponse(BaseModel):
    job_id: str
    persona_id: str
    status: str
    progress: int
    processed_files: int
    total_files: int
    current_file: Optional[str] = None
    error: Optional[str] = None

# Constants
MAX_FILE_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

@router.post("/upload", response_model=PersonaUploadResponse)
async def upload_persona(
    background_tasks: BackgroundTasks,
    name: str = Form(..., description="Name for the persona"),
    description: Optional[str] = Form(None, description="Description of the persona"),
    file: Optional[UploadFile] = File(None, description="PDF or text file"),
    text: Optional[str] = Form(None, description="Raw text content"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document or text to create a new persona.
    Accepts either a file upload or raw text, not both.
    """
    # Validate input
    if not file and not text:
        raise HTTPException(400, "Either file or text must be provided")
    
    if file and text:
        raise HTTPException(400, "Provide either file or text, not both")
    
    # Process file upload
    content = ""
    source_type = "text"
    source_filename = None
    
    if file:
        # Check file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(413, f"File size exceeds {MAX_FILE_SIZE_MB}MB limit")
        
        # Determine file type
        filename = file.filename.lower()
        if filename.endswith('.pdf'):
            source_type = "pdf"
            source_filename = file.filename
            # Process PDF
            content = await process_pdf(file_content)
        elif filename.endswith('.txt'):
            source_type = "text"
            source_filename = file.filename
            content = file_content.decode('utf-8', errors='ignore')
        else:
            raise HTTPException(400, "Unsupported file type. Use PDF or TXT")
    else:
        # Use provided text
        content = text
        source_type = "text"
    
    if not content.strip():
        raise HTTPException(400, "Document is empty or could not be processed")
    
    # Generate unique namespace for this persona
    namespace = f"persona_{uuid.uuid4()}"
    
    # Create persona record
    persona = Persona(
        user_id=current_user.id,
        name=name,
        description=description,
        source_type=source_type,
        source_filename=source_filename,
        namespace=namespace,
        metadata={
            "original_size": len(content),
            "upload_method": "file" if file else "text"
        }
    )
    
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    
    # Process in background
    background_tasks.add_task(
        process_and_embed_content,
        persona_id=persona.id,
        namespace=namespace,
        content=content,
        source=source_filename or "uploaded_text"
    )
    
    # 🎯 Sprint 7 Phase 2: Auto-create ElevenLabs agent for new persona
    background_tasks.add_task(
        auto_create_agent_for_persona,
        persona_id=persona.id,
        persona_name=persona.name
    )
    
    return PersonaUploadResponse(
        persona_id=persona.id,
        name=name,
        namespace=namespace,
        chunks=0,  # Will be updated by background task
        message="Upload received. Processing in background..."
    )

@router.post("/{persona_id}/ingest", response_model=IngestJobResponse)
async def ingest_multiple_files(
    persona_id: str,
    files: List[UploadFile] = File(..., description="Multiple PDF or text files"),
    topic_tags: Optional[str] = Form(None, description="JSON array of topic tags"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest multiple files to an existing persona.
    Creates a background job for processing and returns job tracking information.
    """
    logger.info(f"Starting ingest_multiple_files for persona {persona_id}")
    logger.info(f"Current user: {current_user.id if current_user else 'None'}")
    logger.info(f"Number of files: {len(files) if files else 0}")
    
    try:
        # Import queue manager
        from services.queue_manager import enqueue_job
        from services.ingestion_worker import run_ingestion_job
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        raise HTTPException(500, f"Server configuration error: {str(e)}")
    
    # Verify persona exists and belongs to user
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Validate files
    if not files or len(files) == 0:
        raise HTTPException(400, "At least one file must be provided")
    
    if len(files) > 50:  # Increased limit for production
        raise HTTPException(400, "Too many files. Maximum 50 files per upload")
    
    # Validate and read files
    file_data = []
    total_size = 0
    
    for file in files:
        # Read file content
        content = await file.read()
        total_size += len(content)
        
        # Check individual file size
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(413, f"File '{file.filename}' exceeds {MAX_FILE_SIZE_MB}MB limit")
        
        # Check file type
        filename = file.filename.lower() if file.filename else ""
        if not (filename.endswith('.pdf') or filename.endswith('.txt')):
            raise HTTPException(400, f"Unsupported file type for '{file.filename}'. Use PDF or TXT")
        
        # Generate file hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()
        
        file_data.append({
            "filename": file.filename,
            "content": content,
            "hash": file_hash,
            "size": len(content),
            "type": "pdf" if filename.endswith('.pdf') else "text"
        })
    
    # Check total size (100MB limit for batch)
    if total_size > 100 * 1024 * 1024:
        raise HTTPException(413, "Total file size exceeds 100MB limit")
    
    # Parse topic tags if provided
    parsed_tags = []
    if topic_tags:
        try:
            import json
            parsed_tags = json.loads(topic_tags)
            if not isinstance(parsed_tags, list):
                parsed_tags = []
        except:
            # Ignore invalid JSON, just use empty tags
            parsed_tags = []

    # Create ingestion job
    logger.info(f"Creating ingestion job for persona {persona_id}")
    try:
        job_metadata = {
            "files": [
                {
                    "filename": f["filename"], 
                    "hash": f["hash"], 
                    "size": f["size"], 
                    "type": f["type"]
                } 
                for f in file_data
            ],
            "total_size": total_size
        }
        
        # Add topic tags if provided
        if parsed_tags:
            job_metadata["topic_tags"] = parsed_tags
        
        job = IngestionJob(
            persona_id=persona_id,
            user_id=current_user.id,
            total_files=len(file_data),
            processed_files=0,
            status="QUEUED",
            progress=0,
            job_metadata=job_metadata
        )
        logger.info(f"Created job object: {job.id}")
        
        db.add(job)
        logger.info("Added job to session")
        
        await db.commit()
        logger.info("Committed job to database")
        
        await db.refresh(job)
        logger.info(f"Refreshed job: {job.id}")
        
    except Exception as e:
        logger.error(f"Failed to create/save ingestion job: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(500, f"Failed to create ingestion job: {str(e)}")
    
    # Prepare file data for worker (convert bytes to base64 for JSON serialization)
    import base64
    worker_files_data = []
    for f in file_data:
        worker_files_data.append({
            "filename": f["filename"],
            "content": base64.b64encode(f["content"]).decode('utf-8')  # base64 encoded content
        })
    
    # Enqueue background job using Redis Queue
    try:
        rq_job_id = enqueue_job(
            run_ingestion_job,
            job.id,
            persona_id,
            worker_files_data,
            parsed_tags,  # Pass topic tags to worker
            queue_name="ingestion",
            job_timeout="30m"  # 30 minute timeout
        )
        logger.info(f"Enqueued RQ job {rq_job_id} for ingestion job {job.id}")
    except Exception as e:
        logger.error(f"Failed to enqueue job: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Mark job as failed
        job.status = "FAILED"
        job.job_metadata = {"error": f"Failed to enqueue job: {str(e)}"}
        await db.commit()
        raise HTTPException(500, f"Failed to start processing: {str(e)}")
    
    # Estimate processing time (rough calculation)
    estimated_minutes = max(2, len(file_data) * 0.5)
    estimated_time = f"{int(estimated_minutes)}-{int(estimated_minutes + 1)} minutes"
    
    return IngestJobResponse(
        job_id=job.id,
        persona_id=persona_id,
        files_count=len(file_data),
        estimated_time=estimated_time,
        message=f"Started processing {len(file_data)} files. Use /jobs/{job.id}/stream for progress updates."
    )

async def process_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        import pypdf
        from io import BytesIO
        
        pdf_file = BytesIO(file_content)
        reader = pypdf.PdfReader(pdf_file)
        
        text_content = []
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
        
        return "\n\n".join(text_content)
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(500, f"Error processing PDF: {str(e)}")

def process_and_embed_content(
    persona_id: str,
    namespace: str,
    content: str,
    source: str
):
    """Background task to chunk and embed content"""
    # Create a new thread to run the async function
    import threading
    import time
    
    logger.info(f"Starting background task thread for persona {persona_id}")
    
    def run_async():
        try:
            logger.info(f"Thread started for persona {persona_id}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Process content and get chunks
                chunker = TextChunker(
                    chunk_size=int(os.getenv("CHUNK_SIZE_TOKENS", "800")),
                    chunk_overlap=int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))
                )
                chunks = chunker.chunk_text(content, source=source)
                logger.info(f"Created {len(chunks)} chunks for persona {persona_id}")
                
                if not chunks:
                    logger.warning(f"No chunks created for persona {persona_id}")
                    return
                
                # Generate embeddings synchronously
                embedder = Embedder()
                texts = [chunk["text"] for chunk in chunks]
                embeddings = loop.run_until_complete(embedder.embed_documents(texts))
                logger.info(f"Generated {len(embeddings)} embeddings for persona {persona_id}")
                
                # Initialize Pinecone client
                try:
                    pinecone_client = get_pinecone_client()
                    logger.info("Pinecone client initialized successfully")
                    
                    # Prepare metadata
                    metadata_list = []
                    ids = []
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{namespace}_chunk_{i}"
                        ids.append(chunk_id)
                        metadata_list.append({
                            "text": chunk["text"][:1000],  # Store first 1000 chars in metadata
                            "chunk_id": chunk["chunk_id"],
                            "source": chunk["source"],
                            "char_start": chunk["char_start"],
                            "char_end": chunk["char_end"],
                            "persona_id": persona_id
                        })
                    
                    # Upsert to Pinecone
                    result = loop.run_until_complete(pinecone_client.upsert_vectors(
                        namespace=namespace,
                        embeddings=embeddings,
                        metadata=metadata_list,
                        ids=ids
                    ))
                    logger.info(f"Upserted {len(ids)} vectors to Pinecone namespace {namespace}")
                except Exception as e:
                    logger.error(f"Pinecone error: {type(e).__name__}: {str(e)}")
                
                # Update database directly with raw SQL
                import psycopg2
                from urllib.parse import urlparse
                from database import DATABASE_URL
                
                # Parse the DATABASE_URL
                parsed_url = urlparse(DATABASE_URL)
                db_info = {
                    'dbname': parsed_url.path[1:],
                    'user': parsed_url.username,
                    'password': parsed_url.password,
                    'host': parsed_url.hostname,
                    'port': parsed_url.port
                }
                
                try:
                    # Connect directly with psycopg2
                    conn = psycopg2.connect(**db_info)
                    cur = conn.cursor()
                    
                    # Update the persona with direct SQL
                    cur.execute(
                        "UPDATE personas SET chunk_count = %s, total_tokens = %s WHERE id = %s",
                        (len(chunks), sum(chunk.get("token_count", 0) for chunk in chunks), persona_id)
                    )
                    
                    # Commit the transaction
                    conn.commit()
                    
                    # Check if any rows were affected
                    if cur.rowcount > 0:
                        logger.info(f"Updated persona {persona_id} with {len(chunks)} chunks using direct SQL")
                    else:
                        logger.error(f"Persona {persona_id} not found in database")
                    
                    # Close cursor and connection
                    cur.close()
                    conn.close()
                except Exception as e:
                    logger.error(f"Database update error: {type(e).__name__}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                logger.info(f"Thread completed successfully for persona {persona_id}")
            except Exception as e:
                logger.error(f"Error in thread for persona {persona_id}: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Thread setup error for persona {persona_id}: {type(e).__name__}: {str(e)}")
    
    thread = threading.Thread(target=run_async)
    thread.daemon = True  # Make thread a daemon so it doesn't block process exit
    thread.start()
    logger.info(f"Background thread started for persona {persona_id}")

async def _process_and_embed_content(
    persona_id: str,
    namespace: str,
    content: str,
    source: str
):
    """Async implementation of process and embed content"""
    try:
        logger.info(f"Starting processing for persona {persona_id}")
        
        # Initialize services
        chunker = TextChunker(
            chunk_size=int(os.getenv("CHUNK_SIZE_TOKENS", "800")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))
        )
        embedder = Embedder()
        
        # Chunk the content
        chunks = chunker.chunk_text(content, source=source)
        logger.info(f"Created {len(chunks)} chunks for persona {persona_id}")
        
        if not chunks:
            logger.warning(f"No chunks created for persona {persona_id}")
            return
        
        # Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await embedder.embed_documents(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Initialize Pinecone client here to catch the error
        try:
            pinecone_client = get_pinecone_client()
            logger.info("Pinecone client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {type(e).__name__}: {str(e)}")
            # For now, let's skip Pinecone and just update the database
            # This will allow us to test the rest of the flow
            logger.warning("Skipping Pinecone storage due to initialization error")
            
            await _update_persona_chunk_count(persona_id, chunks)
            return
        
        # Prepare metadata
        metadata_list = []
        ids = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{namespace}_chunk_{i}"
            ids.append(chunk_id)
            metadata_list.append({
                "text": chunk["text"][:1000],  # Store first 1000 chars in metadata
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
                "persona_id": persona_id
            })
        
        # Upsert to Pinecone
        result = await pinecone_client.upsert_vectors(
            namespace=namespace,
            embeddings=embeddings,
            metadata=metadata_list,
            ids=ids
        )
        logger.info(f"Upserted {len(ids)} vectors to Pinecone namespace {namespace}")
        
        await _update_persona_chunk_count(persona_id, chunks)
        
    except Exception as e:
        logger.error(f"Error processing content: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

async def _update_persona_chunk_count(persona_id: str, chunks: list):
    """Update persona with chunk count in a new database session"""
    try:
        # We need to use a fresh session for the background task
        from database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            # Find the existing persona record
            stmt = select(Persona).where(Persona.id == persona_id)
            result = await db.execute(stmt)
            persona = result.scalar_one_or_none()
            
            if persona:
                # Update the chunk count and total tokens
                logger.info(f"Found persona {persona_id}, updating chunk count to {len(chunks)}")
                persona.chunk_count = len(chunks)
                persona.total_tokens = sum(chunk.get("token_count", 0) for chunk in chunks)
                await db.commit()
                logger.info(f"Successfully updated persona {persona_id} with {len(chunks)} chunks")
            else:
                logger.warning(f"Persona {persona_id} not found in database")
    except Exception as e:
        logger.error(f"Error updating persona chunk count: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

async def auto_create_agent_for_persona(persona_id: str, persona_name: str):
    """
    Background task to automatically create ElevenLabs agent for new persona
    Sprint 7 Phase 2: Automatic Agent Creation
    """
    try:
        # Wait a bit to ensure persona is fully created
        await asyncio.sleep(2)
        
        logger.info(f"🎯 Auto-creating ElevenLabs agent for persona '{persona_name}' ({persona_id})")
        
        # Create agent with default settings
        agent_id = await agent_service.create_agent_for_persona(
            persona_id=persona_id,
            persona_name=persona_name,
            voice_id=None,  # Will use default voice
            system_prompt=None,  # Will use default prompt
            db=None  # Will update database internally
        )
        
        if agent_id:
            # Update persona with agent_id using fresh async session
            from database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Find the existing persona record
                stmt = select(Persona).where(Persona.id == persona_id)
                result = await db.execute(stmt)
                persona = result.scalar_one_or_none()
                
                if persona:
                    persona.elevenlabs_agent_id = agent_id
                    await db.commit()
                    logger.info(f"✅ Auto-created agent {agent_id} for persona '{persona_name}'")
                else:
                    logger.error(f"Could not find persona {persona_id} to update with agent_id")
        else:
            logger.warning(f"⚠️ Failed to auto-create agent for persona '{persona_name}' - ElevenLabs API may be unavailable")
            
    except Exception as e:
        logger.error(f"Auto agent creation failed for persona {persona_id}: {str(e)}")
        # Don't raise exception to avoid breaking persona creation workflow

@router.get("/templates")
async def list_available_templates(
    current_user: User = Depends(get_current_user)
):
    """Get list of available persona templates"""
    from services.persona_prompt_service import persona_prompt_service
    
    templates = await persona_prompt_service.get_available_templates()
    return {"templates": templates}

@router.get("/list", response_model=PersonaListResponse)
async def list_personas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all personas for the current user"""
    stmt = select(Persona).where(Persona.user_id == current_user.id).order_by(Persona.created_at.desc())
    result = await db.execute(stmt)
    personas = result.scalars().all()
    
    persona_list = []
    for persona in personas:
        persona_list.append({
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "source_type": persona.source_type,
            "chunk_count": persona.chunk_count,
            "created_at": persona.created_at.isoformat() if persona.created_at else None
        })
    
    return PersonaListResponse(personas=persona_list)

@router.get("/{persona_id}")
async def get_persona(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific persona"""
    stmt = select(Persona).where(
        Persona.id == persona_id,
        Persona.user_id == current_user.id
    )
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()
    
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Check Pinecone namespace status
    pinecone_client = get_pinecone_client()
    exists, vector_count = await pinecone_client.check_namespace_exists(persona.namespace)
    
    return {
        "id": persona.id,
        "name": persona.name,
        "description": persona.description,
        "source_type": persona.source_type,
        "source_filename": persona.source_filename,
        "chunk_count": persona.chunk_count,
        "total_tokens": persona.total_tokens,
        "namespace": persona.namespace,
        "vector_count": vector_count,
        "ready": exists and vector_count > 0,
        "elevenlabs_agent_id": persona.elevenlabs_agent_id,
        "created_at": persona.created_at.isoformat() if persona.created_at else None
    }

@router.put("/{persona_id}", response_model=PersonaUpdateResponse)
async def update_persona(
    persona_id: str,
    update_data: PersonaUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update persona name and/or description"""
    # Find the persona
    stmt = select(Persona).where(
        Persona.id == persona_id,
        Persona.user_id == current_user.id
    )
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()
    
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Update fields if provided
    if update_data.name is not None:
        persona.name = update_data.name
    if update_data.description is not None:
        persona.description = update_data.description
    
    await db.commit()
    await db.refresh(persona)
    
    return PersonaUpdateResponse(
        persona_id=persona.id,
        name=persona.name,
        description=persona.description,
        message="Persona updated successfully"
    )

@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a persona and all its associated data"""
    # Find the persona
    stmt = select(Persona).where(
        Persona.id == persona_id,
        Persona.user_id == current_user.id
    )
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()
    
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    try:
        # Delete from Pinecone first
        pinecone_client = get_pinecone_client()
        await pinecone_client.delete_namespace(persona.namespace)
        logger.info(f"Deleted Pinecone namespace: {persona.namespace}")
    except Exception as e:
        logger.warning(f"Failed to delete Pinecone namespace {persona.namespace}: {e}")
        # Continue with database deletion even if Pinecone fails
    
    # 🎯 Sprint 7 Phase 2: Delete associated ElevenLabs agent
    if persona.elevenlabs_agent_id:
        try:
            success = await agent_service.delete_agent_for_persona(
                agent_id=persona.elevenlabs_agent_id, 
                persona_id=persona_id
            )
            if success:
                logger.info(f"✅ Deleted ElevenLabs agent {persona.elevenlabs_agent_id} for persona '{persona.name}'")
            else:
                logger.warning(f"⚠️ Failed to delete ElevenLabs agent {persona.elevenlabs_agent_id}")
        except Exception as e:
            logger.warning(f"Failed to delete ElevenLabs agent {persona.elevenlabs_agent_id}: {e}")
            # Continue with database deletion even if agent deletion fails
    
    # Delete from database
    await db.delete(persona)
    await db.commit()
    
    return {
        "message": f"Persona '{persona.name}' deleted successfully",
        "persona_id": persona_id
    }

async def process_ingestion_job(job_id: str, persona: Persona, file_data: List[dict]):
    """Background task to process multiple files for an ingestion job"""
    from database import AsyncSessionLocal
    
    try:
        logger.info(f"Starting ingestion job {job_id} for persona {persona.id}")
        
        # Update job status to processing
        async with AsyncSessionLocal() as db:
            job_result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
            job = job_result.scalar_one_or_none()
            if job:
                job.status = JobStatus.PROCESSING
                job.progress = 5
                await db.commit()
        
        # Initialize services
        chunker = TextChunker(
            chunk_size=int(os.getenv("CHUNK_SIZE_TOKENS", "800")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))
        )
        embedder = Embedder()
        
        all_chunks = []
        processed_files = 0
        
        # Process each file
        for i, file_info in enumerate(file_data):
            try:
                logger.info(f"Processing file {i+1}/{len(file_data)}: {file_info['filename']}")
                
                # Update progress
                async with AsyncSessionLocal() as db:
                    job_result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
                    job = job_result.scalar_one_or_none()
                    if job:
                        job.progress = int(10 + (i / len(file_data)) * 70)  # 10-80% for processing
                        job.job_metadata = {
                            **job.job_metadata,
                            "current_file": file_info['filename']
                        }
                        await db.commit()
                
                # Extract text content
                if file_info['type'] == 'pdf':
                    content = await process_pdf(file_info['content'])
                else:
                    content = file_info['content'].decode('utf-8', errors='ignore')
                
                if not content.strip():
                    logger.warning(f"File {file_info['filename']} is empty or could not be processed")
                    continue
                
                # Chunk the content
                chunks = chunker.chunk_text(content, source=file_info['filename'])
                all_chunks.extend(chunks)
                
                processed_files += 1
                
                # Update processed files count
                async with AsyncSessionLocal() as db:
                    job_result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
                    job = job_result.scalar_one_or_none()
                    if job:
                        job.processed_files = processed_files
                        await db.commit()
                
            except Exception as e:
                logger.error(f"Error processing file {file_info['filename']}: {e}")
                # Continue with other files
                continue
        
        if not all_chunks:
            # Update job as failed
            async with AsyncSessionLocal() as db:
                job_result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
                job = job_result.scalar_one_or_none()
                if job:
                    job.status = JobStatus.FAILED
                    job.progress = 100
                    job.job_metadata = {
                        **job.job_metadata,
                        "error": "No content could be extracted from any files"
                    }
                    await db.commit()
            return
        
        logger.info(f"Created {len(all_chunks)} total chunks from {processed_files} files")
        
        # Generate embeddings
        async with AsyncSessionLocal() as db:
            job_result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
            job = job_result.scalar_one_or_none()
            if job:
                job.progress = 80
                job.job_metadata = {
                    **job.job_metadata,
                    "current_file": "Generating embeddings..."
                }
                await db.commit()
        
        texts = [chunk["text"] for chunk in all_chunks]
        embeddings = await embedder.embed_documents(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Store in Pinecone
        try:
            pinecone_client = get_pinecone_client()
            
            # Prepare metadata
            metadata_list = []
            ids = []
            for i, chunk in enumerate(all_chunks):
                chunk_id = f"{persona.namespace}_chunk_{persona.chunk_count + i}"
                ids.append(chunk_id)
                metadata_list.append({
                    "text": chunk["text"][:1000],
                    "chunk_id": chunk["chunk_id"],
                    "source": chunk["source"],
                    "char_start": chunk["char_start"],
                    "char_end": chunk["char_end"],
                    "persona_id": persona.id
                })
            
            # Upsert to Pinecone
            await pinecone_client.upsert_vectors(
                namespace=persona.namespace,
                embeddings=embeddings,
                metadata=metadata_list,
                ids=ids
            )
            logger.info(f"Upserted {len(ids)} vectors to Pinecone")
            
        except Exception as e:
            logger.error(f"Pinecone error: {e}")
            # Continue to update database even if Pinecone fails
        
        # Update persona chunk count
        async with AsyncSessionLocal() as db:
            persona_result = await db.execute(select(Persona).where(Persona.id == persona.id))
            db_persona = persona_result.scalar_one_or_none()
            if db_persona:
                db_persona.chunk_count += len(all_chunks)
                db_persona.total_tokens += sum(chunk.get("token_count", 0) for chunk in all_chunks)
                await db.commit()
        
        # Update job as completed
        async with AsyncSessionLocal() as db:
            job_result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
            job = job_result.scalar_one_or_none()
            if job:
                job.status = JobStatus.COMPLETED
                job.progress = 100
                job.processed_files = processed_files
                job.job_metadata = {
                    **job.job_metadata,
                    "chunks_created": len(all_chunks),
                    "completed_at": str(datetime.utcnow())
                }
                await db.commit()
        
        logger.info(f"Completed ingestion job {job_id}")
        
    except Exception as e:
        logger.error(f"Error in ingestion job {job_id}: {e}")
        
        # Update job as failed
        async with AsyncSessionLocal() as db:
            job_result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
            job = job_result.scalar_one_or_none()
            if job:
                job.status = JobStatus.FAILED
                job.progress = 100
                job.job_metadata = {
                    **job.job_metadata,
                    "error": str(e)
                }
                await db.commit()

@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current job status"""
    # Import queue manager
    from services.queue_manager import get_job_status as get_rq_job_status
    
    # Verify job exists and belongs to user
    result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    
    # Get RQ job status for additional details
    rq_status = get_rq_job_status(job_id, queue_name="ingestion")
    
    # Combine database and RQ status
    response_data = {
        "job_id": job.id,
        "persona_id": job.persona_id,
        "status": job.status.value,
        "progress": job.progress,
        "processed_files": job.processed_files,
        "total_files": job.total_files,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }
    
    # Add metadata from job
    if job.job_metadata:
        response_data.update({
            "error": job.job_metadata.get("error"),
            "files": job.job_metadata.get("files", [])
        })
    
    # Add RQ job details if available
    if rq_status and rq_status.get("status") != "not_found":
        response_data.update({
            "rq_status": rq_status.get("status"),
            "current_file": rq_status.get("current_file"),
            "total_chunks": rq_status.get("total_chunks", 0)
        })
    
    return response_data

@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(
    job_id: str,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """SSE endpoint for real-time job progress updates"""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    from api.auth import verify_token
    from services.queue_manager import get_job_status as get_rq_job_status
    
    # Verify token manually since EventSource doesn't support Authorization headers
    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(401, "Invalid token")
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    
    # Verify job belongs to user
    result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.user_id == user_id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    
    async def event_stream():
        """Generate SSE events for job progress"""
        from database import AsyncSessionLocal
        
        last_progress = -1
        last_status = None
        last_current_file = None
        
        while True:
            try:
                # Get latest job status from database
                async with AsyncSessionLocal() as db:
                    job_result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
                    current_job = job_result.scalar_one_or_none()
                    
                    if not current_job:
                        break
                    
                    # Get RQ job status for real-time details
                    rq_status = get_rq_job_status(job_id, queue_name="ingestion")
                    
                    # Determine current file and progress
                    current_file = None
                    current_progress = current_job.progress
                    
                    if rq_status and rq_status.get("status") != "not_found":
                        current_file = rq_status.get("current_file")
                        # Use RQ progress if available and more recent
                        rq_progress = rq_status.get("progress", 0)
                        if rq_progress > current_progress:
                            current_progress = rq_progress
                    
                    # Check if anything changed
                    status_changed = current_job.status != last_status
                    progress_changed = current_progress != last_progress
                    file_changed = current_file != last_current_file
                    
                    if status_changed or progress_changed or file_changed:
                        # Create progress response
                        progress_data = JobProgressResponse(
                            job_id=current_job.id,
                            persona_id=current_job.persona_id,
                            status=current_job.status.value,
                            progress=current_progress,
                            processed_files=current_job.processed_files,
                            total_files=current_job.total_files,
                            current_file=current_file,
                            error=current_job.job_metadata.get("error") if current_job.job_metadata else None
                        )
                        
                        # Send SSE event
                        yield f"event: progress\n"
                        yield f"data: {progress_data.json()}\n\n"
                        
                        last_progress = current_progress
                        last_status = current_job.status
                        last_current_file = current_file
                    
                    # If job is completed or failed, send final event and break
                    if current_job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                        final_data = JobProgressResponse(
                            job_id=current_job.id,
                            persona_id=current_job.persona_id,
                            status=current_job.status.value,
                            progress=100,
                            processed_files=current_job.processed_files,
                            total_files=current_job.total_files,
                            current_file=None,
                            error=current_job.job_metadata.get("error") if current_job.job_metadata else None
                        )
                        
                        yield f"event: complete\n"
                        yield f"data: {final_data.json()}\n\n"
                        break
                
                # Wait before next update
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in SSE stream: {e}")
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# ============================================
# NEW BULLETPROOF UPLOAD ENDPOINTS
# ============================================

class DirectUploadResponse(BaseModel):
    job_id: str
    persona_id: str
    message: str

class UploadProgressResponse(BaseModel):
    job_id: str
    status: str  # 'uploading', 'processing', 'completed', 'failed'
    progress: int  # 0-100
    chunks: Optional[int] = None
    error: Optional[str] = None

# Simple in-memory storage for upload progress (in production, use Redis or DB)
upload_sessions = {}

@router.post("/{persona_id}/upload-direct", response_model=DirectUploadResponse)
async def upload_file_direct(
    persona_id: str,
    file: UploadFile = File(..., description="PDF or text file"),
    topic_tags: Optional[str] = Form(None, description="JSON array of topic tags"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Direct file upload endpoint - processes immediately without queue.
    Designed for reliability over complexity.
    """
    # Generate job ID for tracking
    job_id = str(uuid.uuid4())
    
    # Verify persona exists and belongs to user
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Initialize progress tracking
    upload_sessions[job_id] = {
        "status": "uploading",
        "progress": 10,
        "persona_id": persona_id,
        "filename": file.filename,
        "started_at": datetime.utcnow()
    }
    
    # Validate file
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    
    filename = file.filename.lower()
    if not (filename.endswith('.pdf') or filename.endswith('.txt')):
        raise HTTPException(400, "Only PDF and TXT files are supported")
    
    # Parse topic tags if provided
    parsed_tags = []
    if topic_tags:
        try:
            import json
            parsed_tags = json.loads(topic_tags)
            if not isinstance(parsed_tags, list):
                parsed_tags = []
        except:
            # Ignore invalid JSON, just use empty tags
            parsed_tags = []
    
    # Read file content
    try:
        content = await file.read()
        
        # Check file size (100MB limit)
        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(413, "File size exceeds 100MB limit")
        
        # Update progress
        upload_sessions[job_id]["progress"] = 30
        upload_sessions[job_id]["status"] = "processing"
        
        # Extract text content
        if filename.endswith('.pdf'):
            text_content = await process_pdf(content)
        else:
            text_content = content.decode('utf-8', errors='ignore')
        
        if not text_content.strip():
            raise HTTPException(400, "File is empty or could not be processed")
        
        # Update progress
        upload_sessions[job_id]["progress"] = 50
        
        # Process content directly (no background task)
        chunks_created = await process_file_content(
            persona_id=persona_id,
            namespace=persona.namespace,
            content=text_content,
            source=file.filename,
            job_id=job_id,
            topic_tags=parsed_tags
        )
        
        # Update persona chunk count
        persona.chunk_count += chunks_created
        await db.commit()
        
        # Mark as completed
        upload_sessions[job_id]["status"] = "completed"
        upload_sessions[job_id]["progress"] = 100
        upload_sessions[job_id]["chunks"] = chunks_created
        
        return DirectUploadResponse(
            job_id=job_id,
            persona_id=persona_id,
            message=f"Successfully processed {file.filename} into {chunks_created} chunks"
        )
        
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}")
        
        # Mark as failed
        upload_sessions[job_id]["status"] = "failed"
        upload_sessions[job_id]["progress"] = 100
        upload_sessions[job_id]["error"] = str(e)
        
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(500, f"Error processing file: {str(e)}")

async def process_file_content(
    persona_id: str,
    namespace: str,
    content: str,
    source: str,
    job_id: str,
    topic_tags: Optional[List[str]] = None
) -> int:
    """
    Process file content directly - chunk, embed, and store.
    Returns the number of chunks created.
    """
    try:
        # Initialize services
        chunker = TextChunker(
            chunk_size=int(os.getenv("CHUNK_SIZE_TOKENS", "800")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))
        )
        embedder = Embedder()
        
        # Update progress
        if job_id in upload_sessions:
            upload_sessions[job_id]["progress"] = 60
        
        # Chunk the content
        chunks = chunker.chunk_text(content, source=source)
        logger.info(f"Created {len(chunks)} chunks for {source}")
        
        if not chunks:
            raise ValueError("No chunks created from content")
        
        # Update progress
        if job_id in upload_sessions:
            upload_sessions[job_id]["progress"] = 70
        
        # Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await embedder.embed_documents(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Update progress
        if job_id in upload_sessions:
            upload_sessions[job_id]["progress"] = 80
        
        # Store in Pinecone
        try:
            pinecone_client = get_pinecone_client()
            
            # Get current chunk count from database for proper ID generation
            from database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Persona).where(Persona.id == persona_id))
                persona = result.scalar_one_or_none()
                current_chunk_count = persona.chunk_count if persona else 0
            
            # Prepare metadata
            metadata_list = []
            ids = []
            for i, chunk in enumerate(chunks):
                chunk_id = f"{namespace}_chunk_{current_chunk_count + i}"
                ids.append(chunk_id)
                chunk_metadata = {
                    "text": chunk["text"][:1000],  # Store first 1000 chars
                    "chunk_id": chunk["chunk_id"],
                    "source": chunk["source"],
                    "char_start": chunk["char_start"],
                    "char_end": chunk["char_end"],
                    "persona_id": persona_id
                }
                
                # Add topic tags if provided
                if topic_tags:
                    chunk_metadata["topic_tags"] = topic_tags
                    
                metadata_list.append(chunk_metadata)
            
            # Upsert to Pinecone
            await pinecone_client.upsert_vectors(
                namespace=namespace,
                embeddings=embeddings,
                metadata=metadata_list,
                ids=ids
            )
            logger.info(f"Upserted {len(ids)} vectors to Pinecone namespace {namespace}")
            
        except Exception as e:
            logger.error(f"Pinecone error: {e}")
            # Continue even if Pinecone fails - at least we processed the content
        
        # Update progress
        if job_id in upload_sessions:
            upload_sessions[job_id]["progress"] = 95
        
        return len(chunks)
        
    except Exception as e:
        logger.error(f"Error in process_file_content: {e}")
        raise

@router.post("/jobs/{job_id}/requeue")
async def requeue_failed_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Requeue a failed ingestion job
    """
    # Get the failed job
    result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job.status != "FAILED":
        raise HTTPException(400, "Only failed jobs can be requeued")
    
    # Get original job metadata to reconstruct file data
    if not job.job_metadata or "files" not in job.job_metadata:
        raise HTTPException(400, "Job metadata missing - cannot requeue")
    
    try:
        # Reset job status
        job.status = "QUEUED"
        job.progress = 0
        job.processed_files = 0
        job.job_metadata = {**job.job_metadata, "requeued_at": datetime.utcnow().isoformat()}
        await db.commit()
        
        # Get topic tags from original job metadata
        topic_tags = job.job_metadata.get("topic_tags", [])
        
        # Since we don't have the original file content, we can only requeue 
        # if the files were stored (which they're not in current implementation)
        # For now, return an error message suggesting manual re-upload
        
        return {
            "message": "Job reset to QUEUED status. Note: Files need to be re-uploaded as content is not stored.",
            "job_id": job_id,
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Error requeuing job {job_id}: {e}")
        raise HTTPException(500, f"Failed to requeue job: {str(e)}")

@router.get("/upload-progress/{job_id}", response_model=UploadProgressResponse)
async def get_upload_progress(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get upload progress for a job"""
    
    # Find the job
    result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    return UploadProgressResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        chunks=job.job_metadata.get('chunks') if job.job_metadata else None,
        error=job.job_metadata.get('error') if job.job_metadata else None
    )

# ============================================
# PERSONA-SPECIFIC PROMPT MANAGEMENT ENDPOINTS
# ============================================

from services.persona_prompt_service import persona_prompt_service
from models import PromptLayer

# Request/Response Models for Persona Prompts
class PersonaPromptListResponse(BaseModel):
    prompts: dict  # Dict[str, List[Dict[str, Any]]]

class CreatePromptVersionRequest(BaseModel):
    content: str
    commit_message: Optional[str] = None

class PromptVersionResponse(BaseModel):
    id: str
    layer: str
    name: str
    content: str
    version: int
    is_active: bool
    author_id: str
    commit_message: Optional[str]
    persona_id: str
    created_at: str
    updated_at: str

class PersonaSettingsRequest(BaseModel):
    voice_id: Optional[str] = None
    voice_settings: Optional[dict] = None
    default_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class PersonaSettingsResponse(BaseModel):
    persona_id: str
    voice_id: Optional[str]
    voice_settings: Optional[dict]
    default_model: Optional[str]
    temperature: Optional[float]  # Will be converted from int storage
    max_tokens: Optional[int]

class CreateFromTemplateRequest(BaseModel):
    template_name: str

class CreateFromTemplateResponse(BaseModel):
    prompts: dict  # Created prompt versions
    success: bool
    message: str

class TemplateListResponse(BaseModel):
    templates: List[dict]

# Agent Management Response Models
class AgentCreateRequest(BaseModel):
    voice_id: Optional[str] = None
    system_prompt: Optional[str] = None

class AgentCreateResponse(BaseModel):
    agent_id: Optional[str]
    success: bool
    message: str

class AgentStatusResponse(BaseModel):
    status: str  # 'active', 'not_found', 'error', 'unavailable'
    agent_id: Optional[str] = None
    name: Optional[str] = None
    voice_id: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None

@router.get("/{persona_id}/prompts", response_model=PersonaPromptListResponse)
async def list_persona_prompts(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all prompts for a specific persona grouped by layer"""
    
    # Verify persona ownership
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    prompts = await persona_prompt_service.list_persona_prompts(persona_id, db)
    return PersonaPromptListResponse(prompts=prompts)

@router.post("/{persona_id}/prompts/{layer}/{name}/versions", 
             response_model=PromptVersionResponse, 
             status_code=status.HTTP_201_CREATED)
async def create_persona_prompt_version(
    persona_id: str,
    layer: str,
    name: str,
    request: CreatePromptVersionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new version of a persona's prompt"""
    
    # Verify persona ownership
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Validate layer
    try:
        prompt_layer = PromptLayer(layer.lower())
    except ValueError:
        raise HTTPException(400, f"Invalid layer: {layer}. Must be one of: system, rag, user")
    
    # Create new prompt version
    version = await persona_prompt_service.create_prompt_version(
        persona_id=persona_id,
        layer=prompt_layer,
        name=name,
        content=request.content,
        author_id=current_user.id,
        commit_message=request.commit_message or f"Updated {layer} prompt",
        db=db
    )
    
    return PromptVersionResponse(
        id=version.id,
        layer=version.layer.value,
        name=version.name,
        content=version.content,
        version=version.version,
        is_active=version.is_active,
        author_id=version.author_id,
        commit_message=version.commit_message,
        persona_id=version.persona_id,
        created_at=version.created_at.isoformat(),
        updated_at=version.updated_at.isoformat()
    )

@router.put("/{persona_id}/prompts/{version_id}/activate")
async def activate_persona_prompt_version(
    persona_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Activate specific prompt version for persona"""
    
    # Verify persona ownership
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Import the service we need
    from services.async_prompt_version_service import AsyncPromptVersionService
    
    # Verify version belongs to this persona
    version = await AsyncPromptVersionService.get_version_by_id(db, version_id)
    if not version or version.persona_id != persona_id:
        raise HTTPException(404, "Prompt version not found")
    
    # Activate the version
    activated_version = await AsyncPromptVersionService.activate_version(db, version_id)
    if not activated_version:
        raise HTTPException(500, "Failed to activate version")
    
    return {"success": True, "message": "Prompt version activated"}

@router.post("/{persona_id}/prompts/from-template", response_model=CreateFromTemplateResponse)
async def create_persona_from_template(
    persona_id: str,
    request: CreateFromTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Initialize persona with a template"""
    
    # Verify persona ownership
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    try:
        created_prompts = await persona_prompt_service.create_persona_with_template(
            persona_id=persona_id,
            template_name=request.template_name,
            author_id=current_user.id,
            db=db
        )
        
        # Convert to response format
        prompts_dict = {}
        for layer, version in created_prompts.items():
            prompts_dict[layer] = {
                "id": version.id,
                "version": version.version,
                "content_preview": version.content[:100] + "..." if len(version.content) > 100 else version.content
            }
        
        return CreateFromTemplateResponse(
            prompts=prompts_dict,
            success=True,
            message=f"Successfully applied {request.template_name} template"
        )
        
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to create persona from template: {e}")
        raise HTTPException(500, "Failed to apply template")

@router.get("/{persona_id}/settings", response_model=PersonaSettingsResponse)
async def get_persona_settings(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get settings for a persona"""
    
    # Verify persona ownership
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    settings = await persona_prompt_service.get_persona_settings(persona_id, db)
    
    return PersonaSettingsResponse(
        persona_id=persona_id,
        voice_id=settings.voice_id if settings else None,
        voice_settings=settings.voice_settings if settings else None,
        default_model=settings.default_model if settings else None,
        temperature=settings.temperature / 100.0 if settings and settings.temperature else None,
        max_tokens=settings.max_tokens if settings else None
    )

@router.put("/{persona_id}/settings", response_model=PersonaSettingsResponse)
async def update_persona_settings(
    persona_id: str,
    request: PersonaSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update persona settings (voice, model, temperature)"""
    
    # Verify persona ownership
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Validate temperature range
    if request.temperature is not None and (request.temperature < 0 or request.temperature > 2.0):
        raise HTTPException(400, "Temperature must be between 0.0 and 2.0")
    
    # Validate max_tokens
    if request.max_tokens is not None and (request.max_tokens < 1 or request.max_tokens > 4000):
        raise HTTPException(400, "Max tokens must be between 1 and 4000")
    
    settings = await persona_prompt_service.update_persona_settings(
        persona_id=persona_id,
        db=db,
        voice_id=request.voice_id,
        voice_settings=request.voice_settings,
        default_model=request.default_model,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    return PersonaSettingsResponse(
        persona_id=persona_id,
        voice_id=settings.voice_id,
        voice_settings=settings.voice_settings,
        default_model=settings.default_model,
        temperature=settings.temperature / 100.0 if settings.temperature else None,
        max_tokens=settings.max_tokens
    )

@router.post("/{persona_id}/prompts/test")
async def test_persona_prompts(
    persona_id: str,
    request: dict,  # {testQuery: str, useActivePrompts: bool, customPrompts?: {...}}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test prompts with persona's knowledge base (SSE stream response)"""
    
    # Verify persona ownership
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # For now, return a simple test response
    # In production, this would integrate with the chat service
    test_query = request.get("testQuery", "")
    use_active = request.get("useActivePrompts", True)
    
    if use_active:
        prompts = await persona_prompt_service.get_active_prompts(persona_id, db)
    else:
        prompts = request.get("customPrompts", {})
    
    return {
        "message": "Prompt test endpoint - integrate with chat service for full functionality",
        "test_query": test_query,
        "prompts_used": prompts,
        "persona_name": persona.name
    }

@router.get("/{persona_id}/prompts/debug")
async def debug_persona_prompts(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to see all prompt versions for a persona"""
    
    # Verify persona ownership
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Get all prompt versions for this persona
    result = await db.execute(
        select(PromptVersion).where(PromptVersion.persona_id == persona_id).order_by(PromptVersion.created_at.desc())
    )
    all_versions = result.scalars().all()
    
    debug_info = {
        "persona_id": persona_id,
        "total_prompt_versions": len(all_versions),
        "versions": []
    }
    
    for version in all_versions:
        debug_info["versions"].append({
            "id": version.id,
            "layer": version.layer.value,
            "name": version.name,
            "version": version.version,
            "is_active": version.is_active,
            "content_length": len(version.content),
            "content_preview": version.content[:100] + "..." if len(version.content) > 100 else version.content,
            "created_at": version.created_at.isoformat(),
            "commit_message": version.commit_message
        })
    
    return debug_info

# Agent Management Endpoints for Sprint 7 Phase 2

@router.post("/{persona_id}/agent/create", response_model=AgentCreateResponse)
async def create_agent_for_persona(
    persona_id: str,
    request: AgentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create ElevenLabs agent for persona automatically
    Sprint 7 Phase 2: Automatic Agent Creation
    """
    # Verify persona ownership
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    try:
        # Create agent using the agent service
        agent_id = await agent_service.create_agent_for_persona(
            persona_id=persona_id,
            persona_name=persona.name,
            voice_id=request.voice_id,
            system_prompt=request.system_prompt,
            db=db
        )
        
        if agent_id:
            return AgentCreateResponse(
                agent_id=agent_id,
                success=True,
                message=f"Successfully created ElevenLabs agent for '{persona.name}'"
            )
        else:
            return AgentCreateResponse(
                agent_id=None,
                success=False,
                message="Failed to create agent - check ElevenLabs API configuration"
            )
            
    except Exception as e:
        logger.error(f"Agent creation failed for persona {persona_id}: {str(e)}")
        raise HTTPException(500, f"Agent creation failed: {str(e)}")

@router.get("/{persona_id}/agent/status", response_model=AgentStatusResponse)
async def get_agent_status(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get ElevenLabs agent status for persona
    Sprint 7 Phase 2: Agent Status Monitoring
    """
    # Verify persona ownership
    result = await db.execute(
        select(Persona.elevenlabs_agent_id, Persona.name).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona_data = result.first()
    if not persona_data:
        raise HTTPException(404, "Persona not found")
    
    agent_id, persona_name = persona_data
    
    if not agent_id:
        return AgentStatusResponse(
            status="not_configured",
            message=f"No ElevenLabs agent configured for '{persona_name}'"
        )
    
    try:
        # Get agent status from ElevenLabs
        status_info = await agent_service.get_agent_status(agent_id)
        
        return AgentStatusResponse(
            status=status_info.get("status", "unknown"),
            agent_id=agent_id,
            name=status_info.get("name"),
            voice_id=status_info.get("voice_id"),
            created_at=status_info.get("created_at"),
            error=status_info.get("error")
        )
        
    except Exception as e:
        logger.error(f"Failed to get agent status for {persona_id}: {str(e)}")
        return AgentStatusResponse(
            status="error",
            agent_id=agent_id,
            error=str(e)
        )

@router.post("/{persona_id}/agent/recreate", response_model=AgentCreateResponse)
async def recreate_agent_for_persona(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Recreate ElevenLabs agent if missing or broken
    Sprint 7 Phase 2: Agent Recovery
    """
    # Verify persona ownership
    result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    try:
        # Recreate agent using the agent service
        agent_id = await agent_service.recreate_agent_if_needed(
            persona_id=persona_id,
            persona_name=persona.name,
            db=db
        )
        
        if agent_id:
            return AgentCreateResponse(
                agent_id=agent_id,
                success=True,
                message=f"Successfully recreated ElevenLabs agent for '{persona.name}'"
            )
        else:
            return AgentCreateResponse(
                agent_id=None,
                success=False,
                message="Failed to recreate agent - check ElevenLabs API configuration"
            )
            
    except Exception as e:
        logger.error(f"Agent recreation failed for persona {persona_id}: {str(e)}")
        raise HTTPException(500, f"Agent recreation failed: {str(e)}")

@router.delete("/{persona_id}/agent")
async def delete_agent_for_persona(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete ElevenLabs agent for persona
    Sprint 7 Phase 2: Agent Cleanup
    """
    # Verify persona ownership
    result = await db.execute(
        select(Persona.elevenlabs_agent_id, Persona.name).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona_data = result.first()
    if not persona_data:
        raise HTTPException(404, "Persona not found")
    
    agent_id, persona_name = persona_data
    
    if not agent_id:
        return {"success": True, "message": f"No agent to delete for '{persona_name}'"}
    
    try:
        # Delete agent from ElevenLabs
        success = await agent_service.delete_agent_for_persona(agent_id, persona_id)
        
        if success:
            # Clear agent_id from database
            from sqlalchemy import update
            await db.execute(
                update(Persona)
                .where(Persona.id == persona_id)
                .values(elevenlabs_agent_id=None)
            )
            await db.commit()
            
            return {
                "success": True, 
                "message": f"Successfully deleted ElevenLabs agent for '{persona_name}'"
            }
        else:
            return {
                "success": False, 
                "message": f"Failed to delete agent for '{persona_name}'"
            }
            
    except Exception as e:
        logger.error(f"Agent deletion failed for persona {persona_id}: {str(e)}")
        raise HTTPException(500, f"Agent deletion failed: {str(e)}")
