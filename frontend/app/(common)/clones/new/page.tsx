'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import UploadBox from '../../../../components/UploadBox';

export default function NewClonePage() {
  const router = useRouter();
  const [isCreated, setIsCreated] = useState(false);
  const [createdPersona, setCreatedPersona] = useState<{
    id: string;
    name: string;
    chunks: number;
  } | null>(null);

  const handleUploadSuccess = (personaId: string, personaName: string, chunks: number) => {
    console.log('✅ New Clone: Upload successful', { personaId, personaName, chunks });
    setCreatedPersona({ id: personaId, name: personaName, chunks });
    setIsCreated(true);
    
    // Redirect to clones list after a brief success message
    setTimeout(() => {
      router.push('/clones');
    }, 2000);
  };

  const handleUploadError = (error: string) => {
    console.error('❌ New Clone: Upload error', error);
    // Error handling is done by UploadBox component
  };

  if (isCreated && createdPersona) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Clone Created Successfully!</h2>
          <p className="text-gray-600 mb-4">
            <strong>{createdPersona.name}</strong> has been created with {createdPersona.chunks} chunks.
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Your ElevenLabs voice agent is being set up in the background.
          </p>
          <div className="text-sm text-gray-500">
            Returning to clones list...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/clones')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Clones
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Create New Clone</h1>
          <p className="text-gray-600 mt-2">
            Upload content or paste text to create a new AI persona with voice capabilities
          </p>
        </div>

        {/* Upload Form */}
        <div className="bg-white rounded-lg shadow-md">
          <UploadBox
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </div>

        {/* Help Section */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">📋 How to Create a Great Clone</h3>
          <ul className="space-y-2 text-blue-800">
            <li className="flex items-start">
              <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0"></span>
              <span><strong>Name your persona:</strong> Use a recognizable name like "Alex Hormozi" or "Marketing Expert"</span>
            </li>
            <li className="flex items-start">
              <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0"></span>
              <span><strong>Upload quality content:</strong> Books, articles, transcripts work best for authentic personality</span>
            </li>
            <li className="flex items-start">
              <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0"></span>
              <span><strong>Voice agent setup:</strong> An ElevenLabs voice agent will be created automatically</span>
            </li>
            <li className="flex items-start">
              <span className="w-2 h-2 bg-blue-600 rounded-full mt-2 mr-3 flex-shrink-0"></span>
              <span><strong>Processing time:</strong> Large documents may take a few minutes to process</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
} 