'use client';

import { useState, useRef } from 'react';

interface UploadBoxProps {
  onUploadSuccess: (personaId: string, personaName: string, chunks: number) => void;
  onUploadError: (error: string) => void;
}

interface UploadResponse {
  persona_id: string;
  name: string;
  namespace: string;
  chunks: number;
  message: string;
}

export default function UploadBox({ onUploadSuccess, onUploadError }: UploadBoxProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [personaName, setPersonaName] = useState('');
  const [personaDescription, setPersonaDescription] = useState('');
  const [textContent, setTextContent] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_FILE_SIZE_MB = 10;
  const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

  const handleFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    const file = files[0];
    
    // Validate file type
    if (!file.type.includes('pdf') && !file.type.includes('text')) {
      onUploadError('Please upload a PDF or text file');
      return;
    }
    
    // Validate file size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      onUploadError(`File size must be less than ${MAX_FILE_SIZE_MB}MB`);
      return;
    }
    
    uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    if (!personaName.trim()) {
      onUploadError('Please enter a name for your persona');
      return;
    }

    setIsUploading(true);
    setUploadProgress(10);

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        onUploadError('Authentication token not found. Please log in again.');
        return;
      }

      const formData = new FormData();
      formData.append('name', personaName.trim());
      if (personaDescription.trim()) {
        formData.append('description', personaDescription.trim());
      }
      formData.append('file', file);

      setUploadProgress(30);

      const response = await fetch('http://127.0.0.1:8000/persona/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      setUploadProgress(70);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data: UploadResponse = await response.json();
      setUploadProgress(100);
      
      // Clear form
      setPersonaName('');
      setPersonaDescription('');
      setTextContent('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      onUploadSuccess(data.persona_id, data.name, data.chunks);
      
    } catch (error) {
      console.error('Upload error:', error);
      onUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const uploadText = async () => {
    if (!personaName.trim()) {
      onUploadError('Please enter a name for your persona');
      return;
    }

    if (!textContent.trim()) {
      onUploadError('Please enter some text content');
      return;
    }

    setIsUploading(true);
    setUploadProgress(10);

    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        onUploadError('Authentication token not found. Please log in again.');
        return;
      }

      const formData = new FormData();
      formData.append('name', personaName.trim());
      if (personaDescription.trim()) {
        formData.append('description', personaDescription.trim());
      }
      formData.append('text', textContent.trim());

      setUploadProgress(30);

      const response = await fetch('http://127.0.0.1:8000/persona/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      setUploadProgress(70);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data: UploadResponse = await response.json();
      setUploadProgress(100);
      
      // Clear form
      setPersonaName('');
      setPersonaDescription('');
      setTextContent('');

      onUploadSuccess(data.persona_id, data.name, data.chunks);
      
    } catch (error) {
      console.error('Upload error:', error);
      onUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  return (
    <div style={{ padding: '1rem', maxWidth: '600px', margin: '0 auto' }}>
      <h3 style={{ marginBottom: '1rem' }}>Create a New Persona</h3>
      
      {/* Persona Name */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Persona Name *
        </label>
        <input
          type="text"
          value={personaName}
          onChange={(e) => setPersonaName(e.target.value)}
          placeholder="e.g., Alex Hormozi, Marketing Expert, etc."
          disabled={isUploading}
          style={{
            width: '100%',
            padding: '0.75rem',
            borderRadius: '0.25rem',
            border: '1px solid #d1d5db',
            fontSize: '1rem'
          }}
        />
      </div>

      {/* Persona Description */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Description (optional)
        </label>
        <input
          type="text"
          value={personaDescription}
          onChange={(e) => setPersonaDescription(e.target.value)}
          placeholder="Brief description of this persona"
          disabled={isUploading}
          style={{
            width: '100%',
            padding: '0.75rem',
            borderRadius: '0.25rem',
            border: '1px solid #d1d5db',
            fontSize: '1rem'
          }}
        />
      </div>

      {/* File Upload */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Upload File (PDF or Text)
        </label>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: '2px dashed #d1d5db',
            borderColor: dragOver ? '#3b82f6' : '#d1d5db',
            borderRadius: '0.5rem',
            padding: '2rem',
            textAlign: 'center',
            cursor: isUploading ? 'not-allowed' : 'pointer',
            backgroundColor: dragOver ? '#eff6ff' : '#f9fafb',
            opacity: isUploading ? 0.6 : 1
          }}
        >
          <p style={{ margin: 0, color: '#6b7280' }}>
            {isUploading ? 'Uploading...' : 'Click to browse or drag & drop your file here'}
          </p>
          <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.875rem', color: '#9ca3af' }}>
            Supports PDF and text files up to {MAX_FILE_SIZE_MB}MB
          </p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          onChange={(e) => handleFileSelect(e.target.files)}
          disabled={isUploading}
          style={{ display: 'none' }}
        />
      </div>

      {/* OR divider */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        margin: '1.5rem 0',
        color: '#6b7280'
      }}>
        <hr style={{ flex: 1, border: 'none', borderTop: '1px solid #e5e7eb' }} />
        <span style={{ padding: '0 1rem', fontSize: '0.875rem' }}>OR</span>
        <hr style={{ flex: 1, border: 'none', borderTop: '1px solid #e5e7eb' }} />
      </div>

      {/* Text Input */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Paste Text Content
        </label>
        <textarea
          value={textContent}
          onChange={(e) => setTextContent(e.target.value)}
          placeholder="Paste your text content here..."
          disabled={isUploading}
          rows={8}
          style={{
            width: '100%',
            padding: '0.75rem',
            borderRadius: '0.25rem',
            border: '1px solid #d1d5db',
            fontSize: '1rem',
            fontFamily: 'monospace',
            resize: 'vertical'
          }}
        />
        {textContent && (
          <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.5rem 0 0 0' }}>
            {textContent.length} characters
          </p>
        )}
      </div>

      {/* Upload Text Button */}
      {textContent.trim() && (
        <button
          onClick={uploadText}
          disabled={isUploading || !personaName.trim()}
          style={{
            width: '100%',
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            padding: '0.75rem',
            borderRadius: '0.25rem',
            fontSize: '1rem',
            cursor: isUploading || !personaName.trim() ? 'not-allowed' : 'pointer',
            opacity: isUploading || !personaName.trim() ? 0.6 : 1,
            marginBottom: '1rem'
          }}
        >
          {isUploading ? 'Creating Persona...' : 'Create Persona from Text'}
        </button>
      )}

      {/* Progress Bar */}
      {isUploading && (
        <div style={{ marginTop: '1rem' }}>
          <div style={{ 
            width: '100%', 
            backgroundColor: '#e5e7eb', 
            borderRadius: '0.25rem',
            height: '8px'
          }}>
            <div
              style={{
                width: `${uploadProgress}%`,
                backgroundColor: '#3b82f6',
                height: '100%',
                borderRadius: '0.25rem',
                transition: 'width 0.3s ease'
              }}
            />
          </div>
          <p style={{ 
            textAlign: 'center', 
            fontSize: '0.875rem', 
            color: '#6b7280',
            margin: '0.5rem 0 0 0'
          }}>
            {uploadProgress}% complete
          </p>
        </div>
      )}
    </div>
  );
}
