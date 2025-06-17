'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { usePersona } from '@/lib/contexts/PersonaContext';
import AgentStatusBadge from '../../../components/agent/AgentStatusBadge';

interface Clone {
  id: string;
  name: string;
  description: string;
  chunks: number;
  status: 'active' | 'training' | 'draft';
  isProduction?: boolean;
}

export default function ClonesPage() {
  const router = useRouter();
  const { setSelectedPersona } = usePersona();
  const [clones, setClones] = useState<Clone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadClones = async () => {
      try {
        // Get auth token
        const token = localStorage.getItem('auth_token') || localStorage.getItem('token');
        if (!token) {
          setError('Please login to view clones');
          setLoading(false);
          return;
        }

        // Call real API
        const response = await fetch('/api/personas/list', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to load clones: ${response.status}`);
        }

        const data = await response.json();
        
        // Filter for production clones only (Alex Hormozi and Rory Sutherland)
        const productionClones = data.personas.filter((persona: any) => 
          persona.name.toLowerCase().includes('alex') && persona.name.toLowerCase().includes('hormozi') ||
          persona.name.toLowerCase().includes('rory') && persona.name.toLowerCase().includes('sutherland')
        );

        // Transform API data to match component interface
        const transformedClones: Clone[] = productionClones.map((persona: any) => ({
          id: persona.id,
          name: persona.name,
          description: persona.description || 'Business insights and expertise at your fingertips',
          chunks: persona.chunk_count || 0,
          status: persona.chunk_count > 0 ? 'active' : 'draft',
          isProduction: true
        }));

        setClones(transformedClones);
        setError(null);
      } catch (err) {
        console.error('Error loading clones:', err);
        setError(err instanceof Error ? err.message : 'Failed to load clones');
      } finally {
        setLoading(false);
      }
    };

    loadClones();
  }, []);

  const handleCloneSelect = (clone: Clone) => {
    // Set the selected persona in context
    setSelectedPersona({
      id: clone.id,
      name: clone.name,
      description: clone.description,
      slug: clone.name.toLowerCase().replace(/\s+/g, '-'),
      chunks: clone.chunks
    });
    
    // Navigate to chat
    router.push(`/chat/${clone.id}`);
  };

  const getCloneIcon = (name: string) => {
    if (name.toLowerCase().includes('hormozi')) return '💪';
    if (name.toLowerCase().includes('rory') || name.toLowerCase().includes('sutherland')) return '🧠';
    return '🎭';
  };

  const getCloneGradient = (name: string) => {
    if (name.toLowerCase().includes('hormozi')) return 'from-orange-500 to-red-600';
    if (name.toLowerCase().includes('rory') || name.toLowerCase().includes('sutherland')) return 'from-purple-500 to-indigo-600';
    return 'from-blue-500 to-purple-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse">
            <div className="h-10 bg-gray-200 rounded w-80 mb-2"></div>
            <div className="h-5 bg-gray-200 rounded w-96 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2].map(i => (
                <div key={i} className="bg-white rounded-xl border p-8">
                  <div className="h-16 w-16 bg-gray-200 rounded-full mb-4"></div>
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-3"></div>
                  <div className="h-4 bg-gray-200 rounded w-full mb-6"></div>
                  <div className="h-10 bg-gray-200 rounded w-32"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-20">
            <div className="w-32 h-32 bg-red-100 rounded-2xl mx-auto mb-6 flex items-center justify-center">
              <span className="text-5xl">⚠️</span>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Unable to Load Clones</h3>
            <p className="text-red-600 mb-8 max-w-md mx-auto">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="inline-flex px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors font-medium"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Page Header */}
        <div className="mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Choose Your AI Clone</h1>
          <p className="text-gray-600 text-lg">
            Select a business expert to chat with. Each clone has unique knowledge and expertise.
          </p>
        </div>

        {/* Clones Grid */}
        {clones.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-32 h-32 bg-gray-100 rounded-2xl mx-auto mb-6 flex items-center justify-center">
              <span className="text-5xl">🎭</span>
            </div>
            <h3 className="text-xl font-medium text-gray-900 mb-3">No Clones Available</h3>
            <p className="text-gray-600 max-w-md mx-auto">
              No business expert clones are currently configured. Please contact support.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {clones.map((clone) => (
              <div
                key={clone.id}
                onClick={() => handleCloneSelect(clone)}
                className="bg-white rounded-xl border border-gray-200 p-8 hover:shadow-lg transition-all duration-200 cursor-pointer group hover:-translate-y-1"
              >
                {/* Clone Avatar & Header */}
                <div className="flex items-center mb-6">
                  <div className={`w-16 h-16 bg-gradient-to-br ${getCloneGradient(clone.name)} rounded-2xl flex items-center justify-center text-white text-2xl mr-4 group-hover:scale-110 transition-transform`}>
                    {getCloneIcon(clone.name)}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-1">{clone.name}</h3>
                    <div className="flex items-center space-x-2">
                      <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                        clone.status === 'active' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {clone.status === 'active' ? '🟢 Ready' : '🟡 Training'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {clone.chunks} knowledge chunks
                      </span>
                    </div>
                  </div>
                </div>

                {/* Clone Description */}
                <p className="text-gray-600 mb-6 leading-relaxed">
                  {clone.description}
                </p>

                {/* Agent Status */}
                <div className="mb-6">
                  <AgentStatusBadge personaId={clone.id} />
                </div>

                {/* Action Button */}
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    Click to start chatting
                  </div>
                  <div className="flex items-center text-orange-600 font-semibold group-hover:text-orange-700">
                    <span className="mr-2">Start Chat</span>
                    <span className="text-lg group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Help Section */}
        <div className="mt-16 bg-white rounded-xl border border-gray-200 p-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-2xl mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl">❓</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Need Help?</h3>
            <p className="text-gray-600 mb-4">
              Each AI clone has been trained on extensive business knowledge. Use the chat interface to ask questions, 
              upload documents to their knowledge base, and customize their prompts for your specific needs.
            </p>
            <div className="flex flex-wrap justify-center gap-2 text-sm">
              <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full">💬 Chat Interface</span>
              <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full">🧠 Knowledge Base</span>
              <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full">📝 Prompt Management</span>
              <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full">🎯 Business Expertise</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 