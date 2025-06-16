"""
Simple Document Processor - Threading-based approach to avoid async database conflicts

This replaces the complex async ingestion_worker.py with a simple, reliable threading approach.
Each processing thread gets its own database session to avoid conflicts.
"""

import os
import io
import hashlib
import threading
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import base64
import time

# Import SQLAlchemy components
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

# Database session setup for synchronous operations (needed for threading)
def get_database_url():
    """Get database URL and convert to synchronous format"""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cloneadvisor")
    
    # Convert from async to sync format
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://")
    if "postgresql+asyncpg://" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    elif db_url.startswith("postgresql://") and "+psycopg2" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
    
    # Fix SSL parameter format for psycopg2 (keep sslmode for compatibility)
    # psycopg2 uses sslmode, asyncpg uses ssl
    
    return db_url

# Create synchronous engine and session for threading
sync_engine = create_engine(
    get_database_url(),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

# Database and model imports
from models import IngestionJob, JobStatus, Persona

# Processing services
from services.chunker import TextChunker
from services.embedder import Embedder
from services.pinecone_client import get_pinecone_client

# PDF processing
import pypdf
from io import BytesIO

logger = logging.getLogger(__name__)

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

def process_file_simple(job_id: str, persona_id: str, files_data: List[Dict[str, Any]]):
    """
    Process files with own database session - threading-based approach
    
    This function runs in its own thread with its own database session
    to avoid the async database conflicts we had before.
    """
    thread_logger = logging.getLogger(f"processor-{job_id[:8]}")
    db = SessionLocal()
    
    try:
        thread_logger.info(f"=== STARTING SIMPLE PROCESSING {job_id} ===")
        thread_logger.info(f"Persona ID: {persona_id}")
        thread_logger.info(f"Number of files: {len(files_data)}")
        
        # Step 1: Update status to processing
        job = db.query(IngestionJob).filter_by(id=job_id).first()
        if not job:
            thread_logger.error(f"Job {job_id} not found")
            return
            
        job.status = JobStatus.PROCESSING
        db.commit()
        thread_logger.info(f"Started processing job {job_id}")
        
        # Step 2: Get persona info
        persona = db.query(Persona).filter_by(id=persona_id).first()
        if not persona:
            raise ValueError(f"Persona {persona_id} not found")
        
        # Step 3: Initialize processor and services
        processor = FileProcessor()
        
        # Get Pinecone client
        pinecone_client = get_pinecone_client()
        namespace = persona.namespace
        
        processed_files = 0
        total_chunks = 0
        processed_hashes = set()  # For deduplication
        
        # Step 4: Process each file
        for i, file_data in enumerate(files_data):
            try:
                filename = file_data['filename']
                # Decode base64 content back to bytes
                content_bytes = base64.b64decode(file_data['content'])
                
                thread_logger.info(f"Processing file {i+1}/{len(files_data)}: {filename}")
                
                # Parse file content
                parsed_data = processor.parse_file(filename, content_bytes)
                file_hash = parsed_data['hash']
                
                # Check for duplicates
                if file_hash in processed_hashes:
                    thread_logger.info(f"Skipping duplicate file: {filename} (hash: {file_hash[:8]})")
                    continue
                
                processed_hashes.add(file_hash)
                
                # Step 5: Chunk text
                chunks = processor.chunker.chunk_text(
                    parsed_data['content'], 
                    source=filename
                )
                
                thread_logger.info(f"Created {len(chunks)} chunks for {filename}")
                
                # Step 6: Generate embeddings
                # Extract text content from chunk dictionaries
                chunk_texts = []
                for chunk in chunks:
                    if isinstance(chunk, dict):
                        chunk_texts.append(chunk.get('text', chunk.get('content', str(chunk))))
                    else:
                        chunk_texts.append(str(chunk))
                
                # Use async embedder in sync context
                import asyncio
                try:
                    # Check if we're already in an event loop
                    loop = asyncio.get_running_loop()
                    # If we're in a loop, we need to run in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, processor.embedder.embed_documents(chunk_texts))
                        embeddings = future.result()
                except RuntimeError:
                    # No event loop running, we can use asyncio.run directly
                    embeddings = asyncio.run(processor.embedder.embed_documents(chunk_texts))
                
                # Step 7: Store in vector database
                vectors_to_upsert = []
                for j, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    vector_id = f"{persona_id}_{file_hash[:8]}_{j}"
                    
                    # Extract chunk text properly
                    chunk_text = chunk.get('text', chunk.get('content', str(chunk))) if isinstance(chunk, dict) else str(chunk)
                    
                    vectors_to_upsert.append({
                        "id": vector_id,
                        "values": embedding,
                        "metadata": {
                            "content": chunk_text,
                            "filename": filename,
                            "file_type": parsed_data['file_type'],
                            "chunk_index": j,
                            "persona_id": persona_id,
                            "file_hash": file_hash
                        }
                    })
                
                # Batch upsert to Pinecone
                if vectors_to_upsert:
                    pinecone_client.index.upsert(
                        vectors=vectors_to_upsert,
                        namespace=namespace
                    )
                    thread_logger.info(f"Upserted {len(vectors_to_upsert)} vectors for {filename}")
                
                processed_files += 1
                total_chunks += len(chunks)
                
            except Exception as file_error:
                thread_logger.error(f"Error processing file {filename}: {str(file_error)}")
                # Continue with other files, don't fail the entire job
                continue
        
        # Step 8: Update job status to completed
        job.status = JobStatus.COMPLETED
        job.processed_files = processed_files
        
        # Update job metadata with results
        if job.job_metadata:
            job.job_metadata['chunks_created'] = total_chunks
            job.job_metadata['completed_at'] = datetime.utcnow().isoformat()
        
        db.commit()
        thread_logger.info(f"=== COMPLETED PROCESSING {job_id} ===")
        thread_logger.info(f"Processed {processed_files}/{len(files_data)} files")
        thread_logger.info(f"Created {total_chunks} total chunks")
        
    except Exception as e:
        thread_logger.error(f"Error processing job {job_id}: {str(e)}")
        
        # Update job status to failed with error message
        try:
            job = db.query(IngestionJob).filter_by(id=job_id).first()
            if job:
                job.status = JobStatus.FAILED
                # We'll add error_message field in migration
                if hasattr(job, 'error_message'):
                    job.error_message = str(e)[:500]  # Truncate long errors
                db.commit()
        except Exception as update_error:
            thread_logger.error(f"Failed to update job status: {update_error}")
            
    finally:
        db.close()
        thread_logger.info(f"Database session closed for job {job_id}")

def start_processing_thread(job_id: str, persona_id: str, files_data: List[Dict[str, Any]]):
    """
    Start processing in background thread
    
    This replaces the asyncio.create_task() approach that was causing database conflicts.
    Each thread gets its own database session and runs independently.
    """
    thread = threading.Thread(
        target=process_file_simple,
        args=(job_id, persona_id, files_data),
        name=f"processor-{job_id[:8]}"
    )
    thread.daemon = True
    thread.start()
    
    logger.info(f"Started processing thread for job {job_id}")
    
    return thread 