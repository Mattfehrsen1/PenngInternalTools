'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function BrainDashboard() {
  const router = useRouter();
  const [token, setToken] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication
  useEffect(() => {
    console.log('🧠 Brain page: Checking authentication...');
    
    try {
      const storedToken = localStorage.getItem('auth_token');
      console.log('🔍 Brain page - Token found:', !!storedToken);
      
      if (!storedToken) {
        console.log('❌ No token in Brain page, redirecting to login');
        router.push('/login');
        return;
      }
      
      console.log('✅ Token found in Brain page, showing dashboard');
      setToken(storedToken);
    } catch (error) {
      console.error('❌ Error checking auth in Brain page:', error);
      router.push('/login');
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Brain dashboard...</p>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <p className="text-gray-600">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">🧠 Brain</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Train your AI personas by uploading documents, managing knowledge, and monitoring performance.
        </p>
      </div>

      {/* Quick Actions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Upload Documents */}
        <div
          onClick={() => router.push('/brain/upload')}
          className="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition-shadow cursor-pointer group"
        >
          <div className="flex items-center mb-4">
            <div className="bg-blue-100 p-3 rounded-lg group-hover:bg-blue-200 transition-colors">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Documents</h3>
          <p className="text-gray-600 text-sm">
            Add new documents to your personas with our bulletproof parallel upload system.
          </p>
        </div>

        {/* Manage Personas */}
        <div
          onClick={() => router.push('/brain/personas')}
          className="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition-shadow cursor-pointer group"
        >
          <div className="flex items-center mb-4">
            <div className="bg-green-100 p-3 rounded-lg group-hover:bg-green-200 transition-colors">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Manage Personas</h3>
          <p className="text-gray-600 text-sm">
            Create, edit, and organize your AI personas and their knowledge bases.
          </p>
        </div>

        {/* Analytics */}
        <div
          onClick={() => router.push('/brain/analytics')}
          className="bg-white p-6 rounded-lg shadow-sm border hover:shadow-md transition-shadow cursor-pointer group"
        >
          <div className="flex items-center mb-4">
            <div className="bg-purple-100 p-3 rounded-lg group-hover:bg-purple-200 transition-colors">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Analytics</h3>
          <p className="text-gray-600 text-sm">
            Monitor AI performance, quality scores, and usage statistics.
          </p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">-</div>
            <div className="text-sm text-gray-600">Total Personas</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">-</div>
            <div className="text-sm text-gray-600">Documents Uploaded</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">-</div>
            <div className="text-sm text-gray-600">Knowledge Chunks</div>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-4 text-center">
          Detailed analytics available in the Analytics section
        </p>
      </div>

      {/* Debug Info */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-yellow-800 mb-2">🎉 Success! New Architecture Working</h3>
        <p className="text-sm text-yellow-700">
          You've successfully accessed the new Brain dashboard! The authentication and routing are working correctly.
          Navigate between 🧠 Brain and 💬 Chat using the top navigation.
        </p>
      </div>
    </div>
  );
} 