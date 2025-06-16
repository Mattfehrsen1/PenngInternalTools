'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import FileUploader from '@/components/FileUploader';
import { API_URL } from '@/lib/api';

interface Persona {
  id: string;
  name: string;
  description?: string;
  chunk_count: number;
  created_at: string;
}

export default function UploadPage() {
  const router = useRouter();
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selectedPersona, setSelectedPersona] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadComplete, setUploadComplete] = useState(false);
  const [token, setToken] = useState<string>('');

  // Check authentication and load personas
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    if (!storedToken) {
      router.push('/login');
      return;
    }
    setToken(storedToken);
    loadPersonas(storedToken);
  }, [router]);

  const loadPersonas = async (authToken: string) => {
    try {
      const response = await fetch(`${API_URL}/personas/list`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load personas');
      }

      const data = await response.json();
      setPersonas(data.personas || []);
      
      // Auto-select first persona if available
      if (data.personas && data.personas.length > 0) {
        setSelectedPersona(data.personas[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load personas');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadComplete = (totalChunks: number) => {
    setUploadComplete(true);
    // Refresh persona list to show updated chunk counts
    if (token) {
      loadPersonas(token);
    }
  };

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error);
    setError(error);
  };

  const handleCreateNewPersona = () => {
    router.push('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading personas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Files</h1>
          <p className="text-gray-600">Add documents to your personas for enhanced AI interactions</p>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          {/* Persona Selection */}
          <div className="mb-8">
            <label htmlFor="persona-select" className="block text-sm font-medium text-gray-700 mb-2">
              Select Persona
            </label>
            <div className="flex gap-4">
              <select
                id="persona-select"
                value={selectedPersona}
                onChange={(e) => setSelectedPersona(e.target.value)}
                className="flex-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
                disabled={personas.length === 0}
              >
                {personas.length === 0 ? (
                  <option value="">No personas available</option>
                ) : (
                  <>
                    <option value="">Choose a persona...</option>
                    {personas.map((persona) => (
                      <option key={persona.id} value={persona.id}>
                        {persona.name} ({persona.chunk_count} chunks)
                      </option>
                    ))}
                  </>
                )}
              </select>
              {personas.length === 0 && (
                <button
                  onClick={handleCreateNewPersona}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Create New Persona
                </button>
              )}
            </div>
            {selectedPersona && (
              <p className="mt-2 text-sm text-gray-500">
                Selected: {personas.find(p => p.id === selectedPersona)?.description || 'No description'}
              </p>
            )}
          </div>

          {/* File Uploader */}
          {selectedPersona ? (
            <FileUploader
              personaId={selectedPersona}
              token={token}
              onUploadComplete={handleUploadComplete}
              onUploadError={handleUploadError}
            />
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="mt-2 text-sm text-gray-600">Please select a persona to upload files</p>
            </div>
          )}

          {/* Success Message */}
          {uploadComplete && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800">
                    Upload completed successfully!
                  </p>
                  <div className="mt-2 text-sm text-green-700">
                    <button
                      onClick={() => router.push('/chat')}
                      className="font-medium underline hover:text-green-600"
                    >
                      Go to chat →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-red-800">
                    {error}
                  </p>
                  <button
                    onClick={() => setError(null)}
                    className="mt-2 text-sm text-red-700 underline"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="mt-6 flex justify-between">
          <button
            onClick={() => router.push('/')}
            className="text-gray-600 hover:text-gray-900"
          >
            ← Back to Home
          </button>
          <button
            onClick={() => router.push('/chat')}
            className="text-blue-600 hover:text-blue-800"
          >
            Go to Chat →
          </button>
        </div>
      </div>
    </div>
  );
} 