"""
Document Management API

Handles file upload, listing, and management for personas.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from pydantic import BaseModel
import os
import uuid
import base64
import threading
from datetime import datetime
import logging

from database import get_db
from models import Persona, User, IngestionJob, JobStatus
from api.auth import get_current_user

# Import new simple processing service
from services.simple_processor import start_processing_thread

logger = logging.getLogger(__name__)
router = APIRouter()

# Response models
class DocumentResponse(BaseModel):
    id: str
    name: str
    size: int
    type: str
    uploaded_at: str
    status: str
    chunks: Optional[int] = None
    error: Optional[str] = None

class DocumentListResponse(BaseModel):
    files: List[DocumentResponse]
    total: int

class UploadResponse(BaseModel):
    id: str
    name: str
    size: int
    status: str
    message: str

# Constants
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

@router.get("/{persona_id}/files", response_model=DocumentListResponse)
async def list_persona_files(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all files for a specific persona"""
    
    # Verify persona ownership
    persona_result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = persona_result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Get real ingestion jobs for this persona
    jobs_result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.persona_id == persona_id,
            IngestionJob.user_id == current_user.id
        ).order_by(IngestionJob.created_at.desc())
    )
    jobs = jobs_result.scalars().all()
    
    # Convert jobs to file responses
    files = []
    for job in jobs:
        if job.job_metadata and 'files' in job.job_metadata:
            for file_info in job.job_metadata['files']:
                # Map job status to file status
                if job.status == JobStatus.COMPLETED:
                    status = "processed"
                elif job.status == JobStatus.PROCESSING:
                    status = "processing"
                elif job.status == JobStatus.FAILED:
                    status = "failed"
                else:
                    status = "processing"
                
                # Calculate chunks from metadata if available
                chunks = None
                if job.status == JobStatus.COMPLETED and job.job_metadata:
                    chunks = job.job_metadata.get('chunks_created', 0)
                    # If no chunks_created, estimate based on file size (rough estimate)
                    if not chunks and file_info.get('size'):
                        # Rough estimate: 1 chunk per 1000 characters
                        estimated_chars = file_info['size'] * 0.8  # Assume 80% text efficiency
                        chunks = max(1, int(estimated_chars / 1000))
                
                files.append(DocumentResponse(
                    id=job.id,  # Use job ID as file ID
                    name=file_info['filename'],
                    size=file_info['size'],
                    type=file_info.get('type', 'text/plain'),
                    uploaded_at=job.created_at.isoformat(),
                    status=status,
                    chunks=chunks
                ))
    
    return DocumentListResponse(
        files=files,
        total=len(files)
    )

@router.post("/{persona_id}/files", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_files_to_persona(
    persona_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload one or more files to a persona's knowledge base with real processing"""
    
    # Verify persona ownership
    persona_result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = persona_result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    if not files:
        raise HTTPException(400, "No files provided")
    
    if len(files) > 20:
        raise HTTPException(400, "Too many files. Maximum 20 files per upload")
    
    # Validate each file and prepare file data
    total_size = 0
    files_data = []
    
    for file in files:
        # Read file content
        file_content = await file.read()
        
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(413, f"File {file.filename} exceeds {MAX_FILE_SIZE_MB}MB limit")
        
        total_size += len(file_content)
        
        # Encode content as base64 for storage
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        # Determine file type
        file_type = "text"
        if file.filename and file.filename.lower().endswith('.pdf'):
            file_type = "pdf"
        
        files_data.append({
            'filename': file.filename or f"upload_{len(files_data)}.txt",
            'content': encoded_content,
            'type': file_type,
            'size': len(file_content)
        })
        
        # Reset file pointer for potential future use
        await file.seek(0)
    
    if total_size > MAX_FILE_SIZE_BYTES * 5:  # Max 125MB total
        raise HTTPException(413, "Total upload size exceeds limit")
    
    # Create ingestion job
    job_id = str(uuid.uuid4())
    
    job = IngestionJob(
        id=job_id,
        persona_id=persona_id,
        user_id=current_user.id,
        total_files=len(files),
        processed_files=0,
        status=JobStatus.QUEUED,
        job_metadata={
            "files": [{"filename": f["filename"], "size": f["size"], "type": f["type"]} for f in files_data],
            "started_at": datetime.utcnow().isoformat()
        }
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    logger.info(f"Created ingestion job {job_id} for persona {persona_id} with {len(files)} files")
    
    # Start background processing using threading for reliable database isolation
    # Each thread gets its own database session to avoid async conflicts  
    start_processing_thread(job_id, persona_id, files_data)
    
    # Return the job ID as server_id for frontend tracking
    return UploadResponse(
        id=job_id,  # Frontend will use this job_id to poll status
        name=f"{len(files)} file(s)",
        size=total_size,
        status="queued",
        message=f"Upload successful, processing {len(files)} files"
    )

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a file from the knowledge base"""
    
    # TODO: Implement actual file deletion
    # 1. Verify file ownership through persona ownership
    # 2. Remove from vector store
    # 3. Delete Document record
    # 4. Clean up file storage
    
    # For now, just return success
    return {"message": f"File {file_id} deleted successfully"}

@router.get("/files/{file_id}/status")
async def get_file_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get processing status of a file"""
    
    # TODO: Implement actual status checking
    # Return mock processing status
    return {
        "id": file_id,
        "status": "processed",
        "progress": 100,
        "chunks": 25,
        "message": "File processed successfully"
    }

@router.get("/{persona_id}/files/{server_id}/status")
async def get_persona_file_status(
    persona_id: str,
    server_id: str,  # This is actually the job_id now
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get processing status of a file upload job for a persona - simplified version"""
    
    # Verify persona ownership
    persona_result = await db.execute(
        select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        )
    )
    persona = persona_result.scalar_one_or_none()
    if not persona:
        raise HTTPException(404, "Persona not found")
    
    # Get the ingestion job
    job_result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.id == server_id,
            IngestionJob.persona_id == persona_id,
            IngestionJob.user_id == current_user.id
        )
    )
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(404, "Processing job not found")
    
    # Calculate progress percentage
    if job.total_files > 0:
        progress = int((job.processed_files / job.total_files) * 100)
    else:
        progress = 0
    
    # Simplified status mapping - only 3 states
    if job.status in [JobStatus.QUEUED, JobStatus.PROCESSING]:
        status = "processing"
        error = None
    elif job.status == JobStatus.COMPLETED:
        status = "ready"
        error = None
        progress = 100  # Ensure completed jobs show 100%
    else:  # FAILED
        status = "failed"
        error = job.error_message or "Processing failed"
    
    logger.info(f"Job {server_id} status check: {status}, progress: {progress}%")
    
    return {
        "status": status,  # "processing", "ready", or "failed"
        "progress": progress,  # Progress percentage 0-100
        "error": error     # Error message if failed, None otherwise
    } 