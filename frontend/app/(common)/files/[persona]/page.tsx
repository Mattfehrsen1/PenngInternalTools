'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { usePersona } from '@/lib/contexts/PersonaContext';
import PersonaSelector from '@/components/PersonaSelector';

interface FileItem {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
  status: 'processed' | 'processing' | 'failed';
  chunks?: number;
}

interface UploadingFile {
  id: string;
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  serverId?: string;
  error?: string;
}

// Error Boundary Component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Files page error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

function FilesPageContent() {
  const params = useParams();
  const router = useRouter();
  const personaSlug = params.persona as string;
  const { selectedPersona, personas, setSelectedPersona } = usePersona();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const intervalsRef = useRef<Set<NodeJS.Timeout>>(new Set());

  const [files, setFiles] = useState<FileItem[]>([]);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);

  // Check authentication on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('auth_token');
      if (!storedToken) {
        router.push('/login');
      } else {
        setToken(storedToken);
      }
    }
  }, [router]);

  // Set persona based on URL parameter
  useEffect(() => {
    if (personaSlug && personas.length > 0) {
      const persona = personas.find(p => p.slug === personaSlug || p.id === personaSlug);
      if (persona && (!selectedPersona || selectedPersona.slug !== persona.slug)) {
        setSelectedPersona(persona);
      } else if (!persona) {
        router.push('/clones');
        return;
      }
    }
  }, [personaSlug, personas, selectedPersona, setSelectedPersona, router]);

  // Load files for the selected persona
  useEffect(() => {
    if (selectedPersona && token) {
      loadFiles();
    }
  }, [selectedPersona, token]);

  const loadFiles = useCallback(async () => {
    console.log('[FilesPage] loadFiles - start for persona:', selectedPersona?.id);
    if (!selectedPersona || !token) return;
    
    try {
      setLoading(true);
      setError(null);

      console.log('[FilesPage] loadFiles - fetching from API:', `/api/personas/${selectedPersona.id}/files`);
      const response = await fetch(`/api/personas/${selectedPersona.id}/files`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log('[FilesPage] loadFiles - response.ok:', response.ok);
      if (!response.ok) {
        if (response.status === 401) {
          router.push('/login');
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('[FilesPage] loadFiles - data.files raw:', data.files);
      
      // Transform backend response to match frontend interface
      const transformedFiles: FileItem[] = (data.files || []).map((file: any) => ({
        id: file.id,
        name: file.name,
        size: file.size,
        type: file.type || 'application/octet-stream',
        uploadedAt: file.uploaded_at || new Date().toISOString(),
        status: file.status || 'processed',
        chunks: file.chunks
      }));
      console.log('[FilesPage] loadFiles - transformedFiles:', transformedFiles);

      setFiles(transformedFiles);
    } catch (err) {
      setError('Failed to load files');
      console.error('Error loading files:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedPersona, token, router]);

  const formatFileSize = (bytes: number): string => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    } catch {
      return 'Unknown date';
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    console.log('[FilesPage] handleFileSelect, files:', event.target.files);
    event.preventDefault();
    const files = event.target.files;
    if (files) {
      console.log('[FilesPage] fileList to upload:', Array.from(files).map(f => f.name));
      handleFiles(Array.from(files));
    }
  };

  const handleFiles = useCallback(async (fileList: File[]) => {
    console.log('[FilesPage] handleFiles called with:', fileList.map(f => f.name));
    if (!selectedPersona || !token) return;

    // Initialize upload entries
    const newFiles: UploadingFile[] = fileList.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      progress: 0,
      status: 'uploading',
    }));
    setUploadingFiles(prev => [...prev, ...newFiles]);

    // Upload and poll status for each file
    for (const uf of newFiles) {
      console.log('[FilesPage] upload start for:', uf.id, uf.file.name);
      try {
        const formData = new FormData();
        formData.append('files', uf.file);
        console.log('[FilesPage] posting to API:', `/api/personas/${selectedPersona.id}/files`);
        const uploadRes = await fetch(`/api/personas/${selectedPersona.id}/files`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData,
        });
        if (!uploadRes.ok) throw new Error(`Upload failed: ${uploadRes.status}`);
        const { id: serverId } = await uploadRes.json();
        console.log(`[FilesPage] upload POST response serverId=${serverId}`);

        // Switch to processing state
        setUploadingFiles(prev => prev.map(f => f.id === uf.id
          ? { ...f, status: 'processing', serverId, progress: 0 }
          : f
        ));
        console.log('[FilesPage] polling status for serverId:', serverId);
        const interval = setInterval(async () => {
          console.log('[FilesPage] polling for serverId:', serverId);
          try {
            const statusRes = await fetch(`/api/personas/${selectedPersona.id}/files/${serverId}/status`, {
              headers: { 'Authorization': `Bearer ${token}` },
            });
            if (!statusRes.ok) throw new Error(`Status check failed: ${statusRes.status}`);
            const data = await statusRes.json();
            console.log(`[FilesPage] status for ${serverId}:`, data.status, 'progress:', data.progress);
            if (data.status === 'ready' || data.status === 'processed' || data.status === 'completed' || data.status === 'failed') {
              clearInterval(interval);
              intervalsRef.current.delete(interval);
              if (data.status === 'ready' || data.status === 'processed' || data.status === 'completed') {
                setUploadingFiles(prev => prev.filter(x => x.id !== uf.id));
                await loadFiles();
                console.log(`[FilesPage] file ${serverId} processed, reloaded files`);
              } else {
                setUploadingFiles(prev => prev.map(x => x.id === uf.id
                  ? { ...x, status: 'failed', error: data.message || 'Processing failed' }
                  : x
                ));
                console.warn(`[FilesPage] processing failed for ${serverId}`, data.message);
              }
            } else {
              setUploadingFiles(prev => prev.map(x => x.id === uf.id
                ? { ...x, status: 'processing', progress: data.progress ?? x.progress }
                : x
              ));
            }
          } catch (err) {
            clearInterval(interval);
            intervalsRef.current.delete(interval);
            console.error('[FilesPage] polling error for serverId:', serverId, err);
          }
        }, 1000);
        
        // Track the interval for cleanup
        intervalsRef.current.add(interval);
      } catch (err) {
        console.error('[FilesPage] upload error for fileId:', uf.id, err);
        setUploadingFiles(prev => prev.map(x => x.id === uf.id
          ? { ...x, status: 'failed', error: err instanceof Error ? err.message : 'Upload failed' }
          : x
        ));
      }
    }
  }, [selectedPersona, token, loadFiles]);

  const handleDeleteFile = useCallback(async (fileId: string) => {
    if (!selectedPersona || !token) return;

    try {
      // Optimistic update
      setFiles(prev => prev.filter(f => f.id !== fileId));

      const response = await fetch(`/api/personas/files/${fileId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        // Revert on error
        await loadFiles();
        throw new Error(`Delete failed: ${response.status}`);
      }
    } catch (error) {
      console.error('Delete failed:', error);
      setError('Failed to delete file');
    }
  }, [selectedPersona, token, loadFiles]);

  const handleRetryUpload = (uploadingFileId: string) => {
    const uploadingFile = uploadingFiles.find(f => f.id === uploadingFileId);
    if (uploadingFile) {
      setUploadingFiles(prev => prev.filter(f => f.id !== uploadingFileId));
      handleFiles([uploadingFile.file]);
    }
  };

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  // Cleanup intervals on unmount or persona change
  useEffect(() => {
    return () => {
      // Clear all intervals when component unmounts
      intervalsRef.current.forEach(interval => clearInterval(interval));
      intervalsRef.current.clear();
    };
  }, []);

  // Clear intervals when persona changes
  useEffect(() => {
    intervalsRef.current.forEach(interval => clearInterval(interval));
    intervalsRef.current.clear();
    setUploadingFiles([]);
  }, [selectedPersona?.id]);

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="h-4 bg-gray-200 rounded w-96 mb-8"></div>
          <div className="space-y-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="bg-gray-200 rounded-lg h-16"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!selectedPersona) {
    return (
      <div className="p-6 text-center">
        <div className="text-gray-500 mb-4">No persona selected</div>
        <button
          onClick={() => router.push('/clones')}
          className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600"
        >
          Select a Persona
        </button>
      </div>
    );
  }

  const totalChunks = files.reduce((sum, file) => sum + (file.chunks || 0), 0);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center text-white font-semibold">
              {selectedPersona.name.charAt(0)}
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {selectedPersona.name} Files
              </h1>
              <p className="text-sm text-gray-600">
                {selectedPersona.description} • {files.length} files • {totalChunks} knowledge chunks
              </p>
            </div>
          </div>
          
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 text-sm"
          >
            📁 Upload Files
          </button>
        </div>

        {/* Persona Selector */}
        <div className="mb-2">
          <PersonaSelector currentPath="files" className="max-w-md" />
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}
      </div>

      {/* Upload Area */}
      <div className="p-6">
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive 
              ? 'border-orange-400 bg-orange-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="space-y-2">
            <div className="text-4xl">📁</div>
            <div className="text-lg font-medium text-gray-900">
              Drop files here or click to upload
            </div>
            <div className="text-sm text-gray-500">
              Supports PDF, DOCX, TXT, and more
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="mt-4 px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              Choose Files
            </button>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept=".pdf,.doc,.docx,.txt,.md"
        />
      </div>

      {/* Uploading Files */}
      {uploadingFiles.length > 0 && (
        <div className="px-6 pb-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Uploading</h3>
          <div className="space-y-2">
            {uploadingFiles.map(uploadingFile => (
              <div key={uploadingFile.id} className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium text-gray-900">
                    {uploadingFile.file.name}
                  </div>
                  <div className="text-xs text-gray-500">
                    {uploadingFile.status === 'failed' ? (
                      <button
                        onClick={() => handleRetryUpload(uploadingFile.id)}
                        className="text-orange-600 hover:text-orange-700"
                      >
                        Retry
                      </button>
                    ) : (
                      `${uploadingFile.progress}%`
                    )}
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      uploadingFile.status === 'failed' 
                        ? 'bg-red-500' 
                        : uploadingFile.status === 'processing'
                          ? 'bg-blue-500 animate-pulse'
                          : 'bg-orange-500'
                    }`}
                    style={{ width: `${uploadingFile.progress}%` }}
                  />
                </div>
                {uploadingFile.error && (
                  <div className="text-xs text-red-600 mt-1">{uploadingFile.error}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Files List */}
      <div className="flex-1 px-6 pb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-900">
            Knowledge Base ({files.length} files)
          </h3>
        </div>

        {files.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📄</div>
            <div>No files uploaded yet</div>
            <div className="text-sm mt-1">Upload your first document to get started</div>
          </div>
        ) : (
          <div className="space-y-2">
            {files.map(file => (
              <div key={file.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">
                      {file.type.includes('pdf') ? '📄' : 
                       file.type.includes('word') ? '📝' : 
                       file.type.includes('text') ? '📃' : '📁'}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{file.name}</div>
                      <div className="text-sm text-gray-500">
                        {formatFileSize(file.size)} • {formatDate(file.uploadedAt)}
                        {file.chunks && ` • ${file.chunks} chunks`}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <div className={`px-2 py-1 text-xs rounded-full ${
                      file.status === 'processed' 
                        ? 'bg-green-100 text-green-800'
                        : file.status === 'processing'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-red-100 text-red-800'
                    }`}>
                      {file.status === 'processed' ? 'Ready' :
                       file.status === 'processing' ? 'Processing...' : 'Failed'}
                    </div>
                    
                    <button
                      onClick={() => handleDeleteFile(file.id)}
                      className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete file"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function FilesPage() {
  return (
    <ErrorBoundary
      fallback={
        <div className="h-full flex items-center justify-center">
          <div className="text-center">
            <div className="text-red-500 text-4xl mb-4">⚠️</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Something went wrong</h3>
            <p className="text-gray-600 mb-6">The files interface encountered an error</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Reload Page
            </button>
          </div>
        </div>
      }
    >
      <FilesPageContent />
    </ErrorBoundary>
  );
} 