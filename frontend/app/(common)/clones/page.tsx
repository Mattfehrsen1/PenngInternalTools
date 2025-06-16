'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Clone {
  id: string;
  name: string;
  description: string;
  avatar?: string;
  chunks: number;
  qualityScore: number;
  lastUsed: Date;
  status: 'active' | 'training' | 'draft';
}

export default function ClonesPage() {
  const [clones, setClones] = useState<Clone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadClones = async () => {
      try {
        // Get auth token
        const token = localStorage.getItem('token');
        if (!token) {
          setError('Please login to view your clones');
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
        
        // Transform API data to match component interface
        const transformedClones: Clone[] = data.personas.map((persona: any) => ({
          id: persona.id,
          name: persona.name,
          description: persona.description || 'No description available',
          chunks: persona.chunk_count || 0,
          qualityScore: persona.quality_score || 0,
          lastUsed: persona.last_used ? new Date(persona.last_used) : new Date(),
          status: persona.chunk_count > 0 ? 'active' : 'draft'
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'training': return 'bg-blue-100 text-blue-800';
      case 'draft': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getQualityColor = (score: number) => {
    if (score >= 9.5) return 'text-green-600';
    if (score >= 8.5) return 'text-blue-600';
    if (score >= 7.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-white rounded-lg border p-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
                <div className="h-3 bg-gray-200 rounded w-full mb-4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-red-100 rounded-lg mx-auto mb-4 flex items-center justify-center">
            <span className="text-4xl">⚠️</span>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Clones</h3>
          <p className="text-red-600 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="inline-flex px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">All Clones</h1>
            <p className="text-gray-600 mt-1">
              Manage your AI personas and their performance
            </p>
          </div>
          <Link
            href="/clones/new"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + Create Clone
          </Link>
        </div>
      </div>

      {/* Clones Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clones.map((clone) => (
          <Link
            key={clone.id}
            href={`/clones/${clone.id}`}
            className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            {/* Clone Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-semibold text-lg">
                  {clone.name.charAt(0)}
                </div>
                <div className="ml-3">
                  <h3 className="font-semibold text-gray-900">{clone.name}</h3>
                  <span
                    className={`text-xs px-2 py-1 rounded-full ${getStatusColor(clone.status)}`}
                  >
                    {clone.status}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-lg font-bold ${getQualityColor(clone.qualityScore)}`}>
                  {clone.qualityScore}/10
                </div>
                <div className="text-xs text-gray-500">Quality</div>
              </div>
            </div>

            {/* Clone Description */}
            <p className="text-gray-600 text-sm mb-4 line-clamp-2">
              {clone.description}
            </p>

            {/* Clone Stats */}
            <div className="flex justify-between text-sm text-gray-500">
              <div>
                <span className="font-medium text-gray-900">{clone.chunks}</span> chunks
              </div>
              <div>
                Last used {clone.lastUsed.toLocaleDateString()}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-4 pt-4 border-t border-gray-100 flex space-x-2">
              <button
                onClick={(e) => {
                  e.preventDefault();
                  // TODO: Navigate to chat
                }}
                className="flex-1 px-3 py-2 text-sm bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors"
              >
                💬 Chat
              </button>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  // TODO: Navigate to prompts
                }}
                className="flex-1 px-3 py-2 text-sm bg-gray-50 text-gray-600 rounded-md hover:bg-gray-100 transition-colors"
              >
                📝 Edit
              </button>
            </div>
          </Link>
        ))}
      </div>

      {/* Empty State */}
      {clones.length === 0 && !loading && (
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-gray-100 rounded-lg mx-auto mb-4 flex items-center justify-center">
            <span className="text-4xl">🎭</span>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No clones yet</h3>
          <p className="text-gray-600 mb-6">
            Create your first AI clone to get started
          </p>
          <Link
            href="/clones/new"
            className="inline-flex px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Create Your First Clone
          </Link>
        </div>
      )}
    </div>
  );
} 