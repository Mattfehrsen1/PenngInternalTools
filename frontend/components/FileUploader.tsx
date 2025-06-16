'use client';

import { useState, useRef, useCallback } from 'react';
import { API_URL } from '@/lib/api';

// Simplified interface - no progress percentage, just simple states
interface UploadFile {
  id: string;
  file: File;
  status: 'idle' | 'uploading' | 'processing' | 'ready' | 'failed';
  error?: string;
  chunks?: number;
}

interface FileUploaderProps {
  personaId: string;
  token: string;
  onUploadComplete: (totalChunks: number) => void;
  onUploadError: (error: string) => void;
}

export default function FileUploader({
  personaId,
  token,
  onUploadComplete,
  onUploadError
}: FileUploaderProps) {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [customTag, setCustomTag] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadAbortControllers = useRef<Map<string, AbortController>>(new Map());

  const MAX_FILE_SIZE_MB = 25; // Match backend limit
  const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

  // Predefined topic tags
  const PREDEFINED_TAGS = [
    'Business', 'Technical', 'Creative', 'Educational', 'Legal', 
    'Marketing', 'Research', 'Personal', 'Finance', 'Health',
    'Science', 'Technology', 'Product', 'Strategy', 'Training'
  ];

  const generateFileId = () => Math.random().toString(36).substr(2, 9);

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File size exceeds ${MAX_FILE_SIZE_MB}MB limit`;
    }
    
    const fileName = file.name.toLowerCase();
    if (!fileName.endsWith('.pdf') && !fileName.endsWith('.txt')) {
      return 'Only PDF and TXT files are supported';
    }
    
    return null;
  };

  const addTag = (tag: string) => {
    const trimmedTag = tag.trim();
    if (trimmedTag && !selectedTags.includes(trimmedTag)) {
      setSelectedTags(prev => [...prev, trimmedTag]);
    }
  };

  const removeTag = (tagToRemove: string) => {
    setSelectedTags(prev => prev.filter(tag => tag !== tagToRemove));
  };

  const handleCustomTagKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag(customTag);
      setCustomTag('');
    }
  };

  const addFiles = useCallback((fileList: FileList) => {
    const newFiles: UploadFile[] = [];
    const errors: string[] = [];

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      const error = validateFile(file);
      
      if (error) {
        errors.push(`${file.name}: ${error}`);
        continue;
      }

      // Check for duplicates
      const isDuplicate = files.some(f => 
        f.file.name === file.name && f.file.size === file.size
      );
      
      if (isDuplicate) {
        errors.push(`${file.name}: File already added`);
        continue;
      }

      newFiles.push({
        id: generateFileId(),
        file,
        status: 'idle'
      });
    }

    if (errors.length > 0) {
      onUploadError(errors.join('\n'));
    }

    if (newFiles.length > 0) {
      setFiles(prev => [...prev, ...newFiles]);
    }
  }, [files, onUploadError]);

  const removeFile = (fileId: string) => {
    // Cancel upload if in progress
    const controller = uploadAbortControllers.current.get(fileId);
    if (controller) {
      controller.abort();
      uploadAbortControllers.current.delete(fileId);
    }
    
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const clearAllFiles = () => {
    // Cancel all uploads
    uploadAbortControllers.current.forEach(controller => controller.abort());
    uploadAbortControllers.current.clear();
    
    setFiles([]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFiles = e.dataTransfer.files;
    addFiles(droppedFiles);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles) {
      addFiles(selectedFiles);
    }
  };

  const uploadSingleFile = async (fileInfo: UploadFile): Promise<void> => {
    const abortController = new AbortController();
    uploadAbortControllers.current.set(fileInfo.id, abortController);

    try {
      // Update status to uploading
      setFiles(prev => prev.map(f => 
        f.id === fileInfo.id ? { ...f, status: 'uploading' } : f
      ));

      // Upload file directly - simplified, no chunking
      const formData = new FormData();
      formData.append('files', fileInfo.file);
      
      // Add topic tags if selected
      if (selectedTags.length > 0) {
        formData.append('topic_tags', JSON.stringify(selectedTags));
      }

      const response = await fetch(`${API_URL}/personas/${personaId}/files`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
        signal: abortController.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Upload failed' }));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const result = await response.json();
      
      // Update status to processing and start polling
      setFiles(prev => prev.map(f => 
        f.id === fileInfo.id ? { ...f, status: 'processing' } : f
      ));

      // Start simplified polling
      await pollStatus(fileInfo.id, result.id); // result.id is the job_id
      
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Upload was cancelled
        return;
      }
      
      setFiles(prev => prev.map(f => 
        f.id === fileInfo.id 
          ? { ...f, status: 'failed', error: error instanceof Error ? error.message : 'Upload failed' }
          : f
      ));
    } finally {
      uploadAbortControllers.current.delete(fileInfo.id);
    }
  };

  // Simplified polling - only check for processing/ready/failed
  const pollStatus = async (fileId: string, jobId: string) => {
    const maxAttempts = 150; // 5 minutes at 2-second intervals
    let attempts = 0;
    
    const poll = async (): Promise<void> => {
      if (attempts >= maxAttempts) {
        setFiles(prev => prev.map(f => 
          f.id === fileId 
            ? { ...f, status: 'failed', error: 'Processing timeout' }
            : f
        ));
        return;
      }

      try {
        const response = await fetch(`${API_URL}/personas/${personaId}/files/${jobId}/status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to check status');
        }

        const statusData = await response.json();
        
        if (statusData.status === 'ready') {
          // File is ready!
          setFiles(prev => prev.map(f => 
            f.id === fileId 
              ? { ...f, status: 'ready', chunks: statusData.chunks || 0 }
              : f
          ));
          return;
        } else if (statusData.status === 'failed') {
          // File processing failed
          setFiles(prev => prev.map(f => 
            f.id === fileId 
              ? { ...f, status: 'failed', error: statusData.error || 'Processing failed' }
              : f
          ));
          return;
        }
        
        // Still processing, continue polling
        attempts++;
        setTimeout(poll, 2000); // Poll every 2 seconds
        
      } catch (error) {
        setFiles(prev => prev.map(f => 
          f.id === fileId 
            ? { ...f, status: 'failed', error: error instanceof Error ? error.message : 'Status check failed' }
            : f
        ));
      }
    };

    // Start polling
    setTimeout(poll, 2000); // First check after 2 seconds
  };

  const startUpload = async () => {
    if (files.length === 0) {
      onUploadError('Please select at least one file');
      return;
    }

    setIsProcessing(true);
    
    // Process files in parallel
    const filesToUpload = files.filter(f => f.status === 'idle' || f.status === 'failed');
    
    // Upload all files simultaneously
    const uploadPromises = filesToUpload.map(file => uploadSingleFile(file));
    
    try {
      await Promise.all(uploadPromises);
    } catch (error) {
      console.error('Some uploads failed:', error);
      // Individual file errors are already handled in uploadSingleFile
    }
    
    // Calculate total chunks
    const totalChunks = files.reduce((sum, f) => sum + (f.chunks || 0), 0);
    const hasErrors = files.some(f => f.status === 'failed');
    
    setIsProcessing(false);
    
    if (!hasErrors && totalChunks > 0) {
      onUploadComplete(totalChunks);
    }
  };

  const retryFailed = async () => {
    const failedFiles = files.filter(f => f.status === 'failed');
    
    setIsProcessing(true);
    
    for (const file of failedFiles) {
      // Reset status
      setFiles(prev => prev.map(f => 
        f.id === file.id ? { ...f, status: 'idle', error: undefined } : f
      ));
      
      await uploadSingleFile(file);
    }
    
    setIsProcessing(false);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Simplified status icons
  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'ready': return '✓';
      case 'failed': return '✗';
      case 'processing': return '⟳';
      case 'uploading': return '↑';
      default: return '○';
    }
  };

  const getStatusColor = (status: UploadFile['status']) => {
    switch (status) {
      case 'ready': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'processing': return 'text-yellow-600';
      case 'uploading': return 'text-blue-600';
      default: return 'text-gray-400';
    }
  };

  const getStatusText = (status: UploadFile['status'], fileName: string) => {
    switch (status) {
      case 'ready': return `${fileName} ready`;
      case 'failed': return `${fileName} failed`;
      case 'processing': return `Processing ${fileName}...`;
      case 'uploading': return `Uploading ${fileName}...`;
      default: return fileName;
    }
  };

  const hasFailedFiles = files.some(f => f.status === 'failed');
  const readyCount = files.filter(f => f.status === 'ready').length;
  const totalSize = files.reduce((sum, f) => sum + f.file.size, 0);

  return (
    <div className="space-y-6">
      {/* Drag and Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all
          ${isDragOver 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 bg-gray-50 hover:border-gray-400'
          }
        `}
      >
        <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
          />
        </svg>
        <p className="mt-4 text-lg font-medium text-gray-900">
          Drag files here or click to browse
        </p>
        <p className="mt-2 text-sm text-gray-600">
          Supports PDF and TXT files (up to {MAX_FILE_SIZE_MB}MB each)
        </p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.txt"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Topic Tag Picker */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Topic Tags (Optional)</h3>
        <p className="text-sm text-gray-600 mb-4">
          Add tags to help categorize and find your documents later
        </p>
        
        {/* Predefined Tags */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select from common tags:
          </label>
          <div className="flex flex-wrap gap-2">
            {PREDEFINED_TAGS.map((tag) => (
              <button
                key={tag}
                onClick={() => selectedTags.includes(tag) ? removeTag(tag) : addTag(tag)}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  selectedTags.includes(tag)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>

        {/* Custom Tag Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Or add a custom tag:
          </label>
          <input
            type="text"
            value={customTag}
            onChange={(e) => setCustomTag(e.target.value)}
            onKeyPress={handleCustomTagKeyPress}
            placeholder="Type and press Enter"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Selected Tags */}
        {selectedTags.length > 0 && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Selected tags:
            </label>
            <div className="flex flex-wrap gap-2">
              {selectedTags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                >
                  {tag}
                  <button
                    onClick={() => removeTag(tag)}
                    className="ml-2 hover:text-blue-600"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Files ({files.length})
            </h3>
            <button
              onClick={clearAllFiles}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-3">
            {files.map((fileInfo) => (
              <div key={fileInfo.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <span className={`text-lg ${getStatusColor(fileInfo.status)}`}>
                    {getStatusIcon(fileInfo.status)}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {getStatusText(fileInfo.status, fileInfo.file.name)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(fileInfo.file.size)}
                      {fileInfo.chunks !== undefined && ` • ${fileInfo.chunks} chunks`}
                    </p>
                    {fileInfo.error && (
                      <p className="text-xs text-red-600 mt-1">{fileInfo.error}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => removeFile(fileInfo.id)}
                  className="text-gray-400 hover:text-red-600"
                  disabled={fileInfo.status === 'uploading' || fileInfo.status === 'processing'}
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          {/* File Summary */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Total size: {formatFileSize(totalSize)}</span>
              <span>{readyCount}/{files.length} files ready</span>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between items-center">
        <div className="text-sm text-gray-600">
          {files.filter(f => f.status === 'uploading' || f.status === 'processing').length > 0 && (
            <span>
              Processing {files.filter(f => f.status === 'uploading' || f.status === 'processing').length} files...
            </span>
          )}
        </div>
        
        <div className="flex space-x-3">
          {hasFailedFiles && (
            <button
              onClick={retryFailed}
              disabled={isProcessing}
              className="px-4 py-2 text-sm font-medium text-orange-700 bg-orange-100 border border-orange-300 rounded-md hover:bg-orange-200 disabled:opacity-50"
            >
              Retry Failed
            </button>
          )}
          
          <button
            onClick={startUpload}
            disabled={files.length === 0 || isProcessing}
            className="px-6 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isProcessing ? 'Processing...' : `Upload ${files.length} Files`}
          </button>
        </div>
      </div>
    </div>
  );
} 