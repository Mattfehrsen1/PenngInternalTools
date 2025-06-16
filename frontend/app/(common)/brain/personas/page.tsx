'use client';

import { useRouter } from 'next/navigation';

export default function BrainPersonasPage() {
  const router = useRouter();

  const handleBackToBrain = () => {
    router.push('/brain');
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-sm text-gray-500">
        <button
          onClick={handleBackToBrain}
          className="hover:text-gray-700 transition-colors"
        >
          🧠 Brain
        </button>
        <span>/</span>
        <span className="text-gray-900">Personas</span>
      </nav>

      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Manage Personas</h1>
        <p className="text-gray-600">Create, edit, and organize your AI personas and their knowledge bases</p>
      </div>

      {/* Coming Soon */}
      <div className="bg-white rounded-lg shadow-sm p-12 text-center">
        <div className="mb-4">
          <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">Persona Management Coming Soon</h3>
        <p className="text-gray-500 mb-6 max-w-md mx-auto">
          This feature will allow you to create and manage your AI personas directly from the Brain dashboard. 
          For now, you can create personas through the chat interface.
        </p>
        <div className="space-x-4">
          <button
            onClick={() => router.push('/brain/upload')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Upload Documents
          </button>
          <button
            onClick={() => router.push('/chat')}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            Go to Chat
          </button>
        </div>
      </div>
    </div>
  );
} 