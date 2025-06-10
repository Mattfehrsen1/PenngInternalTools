from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import io
import uuid
from typing import Optional
import logging
import asyncio
from pydantic import BaseModel

from database import get_db
from models import Persona
from api.auth import get_current_user, User
from services.pinecone_client import get_pinecone_client
from services.chunker import TextChunker
from services.embedder import Embedder

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
    
    return PersonaUploadResponse(
        persona_id=persona.id,
        name=name,
        namespace=namespace,
        chunks=0,  # Will be updated by background task
        message="Upload received. Processing in background..."
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
        "created_at": persona.created_at.isoformat() if persona.created_at else None
    }
