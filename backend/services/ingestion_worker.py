"""
Ingestion Worker for processing multiple files asynchronously
Handles file parsing, chunking, deduplication, embedding, and vector storage
"""
import os
import io
import hashlib
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from rq import get_current_job
from dotenv import load_dotenv

# Load environment variables for background tasks
load_dotenv()

# Import async database session
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update

# Import our services
from services.chunker import TextChunker
from services.embedder import Embedder
from services.pinecone_client import get_pinecone_client
from models import IngestionJob, JobStatus, Persona

# PDF processing
import pypdf
from io import BytesIO

logger = logging.getLogger(__name__)

# Database setup for worker  
def get_database_url():
    """Get database URL with fallback to existing database config"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback to constructing from existing config
        from database import DATABASE_URL as fallback_url
        db_url = fallback_url
    
    # Always convert to async URL (handles both postgresql:// and postgresql+psycopg2://)
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    elif db_url.startswith("postgresql+psycopg2://"):
        db_url = db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    
    return db_url

# Create engine with pool settings for better connection management
engine = create_async_engine(
    get_database_url(),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class FileProcessor:
    """Handles individual file processing tasks"""
    
    def __init__(self):
        self.chunker = TextChunker()
        self.embedder = Embedder()
        
    def process_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF content"""
        try:
            pdf_file = BytesIO(file_content)
            reader = pypdf.PdfReader(pdf_file)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            raise ValueError(f"Failed to process PDF: {str(e)}")
    
    def process_text_file(self, file_content: bytes) -> str:
        """Process text file content"""
        try:
            return file_content.decode('utf-8', errors='ignore').strip()
        except Exception as e:
            logger.error(f"Text file processing error: {e}")
            raise ValueError(f"Failed to process text file: {str(e)}")
    
    def get_file_hash(self, content: str) -> str:
        """Generate SHA-256 hash of file content for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def parse_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """
        Parse file content and extract text
        
        Returns:
            Dict with parsed content and metadata
        """
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf'):
            text_content = self.process_pdf(content)
            file_type = "pdf"
        elif filename_lower.endswith('.txt'):
            text_content = self.process_text_file(content)
            file_type = "text"
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        
        if not text_content.strip():
            raise ValueError(f"File {filename} is empty or could not be processed")
        
        file_hash = self.get_file_hash(text_content)
        
        return {
            "filename": filename,
            "content": text_content,
            "file_type": file_type,
            "hash": file_hash,
            "size": len(content),
            "char_count": len(text_content)
        }

async def process_ingestion_job(job_id: str, persona_id: str, files_data: List[Dict[str, Any]], topic_tags: Optional[List[str]] = None):
    """
    Main worker function to process multiple files for a persona
    
    Args:
        job_id: Database job ID (not RQ job ID)
        persona_id: Target persona ID
        files_data: List of file data dicts with 'filename' and 'content' keys
    """
    logger.info(f"=== STARTING INGESTION JOB {job_id} ===")
    logger.info(f"Persona ID: {persona_id}")
    logger.info(f"Number of files: {len(files_data)}")
    
    processor = FileProcessor()
    rq_job = get_current_job()
    
    logger.info(f"Starting ingestion job {job_id} for persona {persona_id} with {len(files_data)} files")
    
    # Debug: Check environment variables
    import os
    openai_key = os.getenv("OPENAI_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    logger.info(f"Environment check - OpenAI: {'SET' if openai_key else 'NOT SET'}, Pinecone: {'SET' if pinecone_key else 'NOT SET'}")
    
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"Database session created, updating job status to PROCESSING")
            # Update job status to processing
            await update_job_status(db, job_id, JobStatus.PROCESSING, 0)
            await db.commit()  # Commit the status update immediately
            
            # Get persona info
            result = await db.execute(select(Persona).where(Persona.id == persona_id))
            persona = result.scalar_one_or_none()
            if not persona:
                raise ValueError(f"Persona {persona_id} not found")
            
            # Get Pinecone client
            pinecone_client = get_pinecone_client()
            namespace = persona.namespace
            
            processed_files = 0
            total_chunks = 0
            processed_hashes = set()  # For deduplication
            
            for i, file_data in enumerate(files_data):
                try:
                    filename = file_data['filename']
                    # Decode base64 content back to bytes
                    import base64
                    content_bytes = base64.b64decode(file_data['content'])
                    
                    # Update progress with current file
                    progress = int((i / len(files_data)) * 100)
                    if rq_job:
                        rq_job.meta['current_file'] = filename
                        rq_job.meta['progress'] = progress
                        rq_job.save_meta()
                    
                    logger.info(f"Processing file {i+1}/{len(files_data)}: {filename}")
                    
                    # Parse file content
                    parsed_data = processor.parse_file(filename, content_bytes)
                    file_hash = parsed_data['hash']
                    
                    # Check for duplicates
                    if file_hash in processed_hashes:
                        logger.info(f"Skipping duplicate file: {filename} (hash: {file_hash[:8]})")
                        continue
                    
                    processed_hashes.add(file_hash)
                    
                    # Chunk the content
                    chunks = processor.chunker.chunk_text(
                        text=parsed_data['content'],
                        source=filename
                    )
                    
                    if not chunks:
                        logger.warning(f"No chunks generated for file: {filename}")
                        continue
                    
                    logger.info(f"Generated {len(chunks)} chunks for {filename}")
                    
                    # Create embeddings in batches
                    batch_size = 100  # Process 100 chunks at a time
                    for batch_start in range(0, len(chunks), batch_size):
                        batch_chunks = chunks[batch_start:batch_start + batch_size]
                        
                        # Generate embeddings for batch
                        texts = [chunk['text'] for chunk in batch_chunks]
                        embeddings = await processor.embedder.embed_documents(texts)
                        
                        # Prepare vectors for Pinecone
                        vector_ids = []
                        metadata_list = []
                        
                        for j, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
                            vector_id = f"{persona_id}_{file_hash[:8]}_{batch_start + j}"
                            vector_ids.append(vector_id)
                            
                            metadata = {
                                "persona_id": persona_id,
                                "source": filename,
                                "file_type": parsed_data['file_type'],
                                "file_hash": file_hash,
                                "chunk_index": batch_start + j,
                                "text": chunk['text'],
                                "created_at": datetime.utcnow().isoformat()
                            }
                            
                            # Add topic tags if provided
                            if topic_tags:
                                metadata["topic_tags"] = topic_tags
                            
                            metadata_list.append(metadata)
                        
                        # Upsert to Pinecone with correct method signature
                        await pinecone_client.upsert_vectors(
                            namespace=namespace,
                            embeddings=embeddings,
                            metadata=metadata_list,
                            ids=vector_ids
                        )
                        
                        logger.info(f"Uploaded batch {batch_start//batch_size + 1} for {filename}")
                    
                    total_chunks += len(chunks)
                    processed_files += 1
                    
                    # Update job progress
                    progress = int(((i + 1) / len(files_data)) * 100)
                    await update_job_status(db, job_id, JobStatus.PROCESSING, progress, processed_files)
                    
                    if rq_job:
                        rq_job.meta['processed_files'] = processed_files
                        rq_job.meta['total_chunks'] = total_chunks
                        rq_job.save_meta()
                
                except Exception as file_error:
                    logger.error(f"Error processing file {filename}: {file_error}")
                    # Continue with other files, don't fail entire job
                    continue
            
            # Update persona chunk count
            await db.execute(
                update(Persona)
                .where(Persona.id == persona_id)
                .values(chunk_count=Persona.chunk_count + total_chunks)
            )
            
            # Mark job as completed with chunk count in metadata
            await update_job_status(db, job_id, JobStatus.COMPLETED, 100, processed_files, chunks_created=total_chunks)
            await db.commit()
            
            logger.info(f"Completed ingestion job {job_id}: {processed_files} files, {total_chunks} chunks")
            
            if rq_job:
                rq_job.meta['completed'] = True
                rq_job.meta['final_chunks'] = total_chunks
                rq_job.save_meta()
            
            return {
                "processed_files": processed_files,
                "total_chunks": total_chunks,
                "status": "completed"
            }
        
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            
            # Mark job as failed
            error_msg = str(e)
            await update_job_status(db, job_id, JobStatus.FAILED, 0, 0, error_msg)
            await db.commit()
            
            if rq_job:
                rq_job.meta['error'] = error_msg
                rq_job.save_meta()
            
            raise e
        
        finally:
            # Ensure database connections are properly closed
            await db.close()

async def update_job_status(
    db: AsyncSession, 
    job_id: str, 
    status: JobStatus, 
    progress: int, 
    processed_files: int = 0,
    error_message: Optional[str] = None,
    chunks_created: Optional[int] = None
):
    """Update job status in database"""
    update_data = {
        "status": status,
        "progress": progress,
        "processed_files": processed_files,
    }
    
    # Get existing metadata to preserve it
    result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
    job = result.scalar_one_or_none()
    existing_metadata = job.job_metadata if job and job.job_metadata else {}
    
    # Update metadata
    if error_message:
        existing_metadata["error"] = error_message
    if chunks_created is not None:
        existing_metadata["chunks_created"] = chunks_created
        
    update_data["job_metadata"] = existing_metadata
    
    await db.execute(
        update(IngestionJob)
        .where(IngestionJob.id == job_id)
        .values(**update_data)
    )

# Wrapper function that can be called by RQ (must be sync)
def run_ingestion_job(job_id: str, persona_id: str, files_data: List[Dict[str, Any]], topic_tags: Optional[List[str]] = None):
    """Sync wrapper for the async ingestion job"""
    import asyncio
    
    # Simply create a new event loop and run the async function
    # This works because BackgroundTasks runs in a separate thread
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                process_ingestion_job(job_id, persona_id, files_data, topic_tags)
            )
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Background job failed: {e}")
        # Try to mark job as failed in database using a sync approach
        try:
            import psycopg2
            import os
            from urllib.parse import urlparse
            
            # Parse database URL for sync connection
            db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cloneadvisor")
            parsed = urlparse(db_url)
            
            # Create sync connection to mark job as failed
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],
                user=parsed.username,
                password=parsed.password
            )
            
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE ingestion_jobs SET status = 'failed', progress = 100, job_metadata = job_metadata || %s WHERE id = %s",
                ({'error': str(e)}, job_id)
            )
            conn.commit()
            conn.close()
            
        except Exception as db_error:
            logger.error(f"Failed to update job status: {db_error}")
        
        raise e 