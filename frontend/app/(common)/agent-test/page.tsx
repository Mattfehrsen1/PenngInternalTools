'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import AgentManager from '../../../components/agent/AgentManager';
import AgentStatusBadge from '../../../components/agent/AgentStatusBadge';

interface Persona {
  id: string;
  name: string;
  description: string;
  chunk_count: number;
}

export default function AgentTestPage() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<string | null>(null);

  useEffect(() => {
    loadPersonas();
  }, []);

  const loadPersonas = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token') || localStorage.getItem('token');
      if (!token) {
        setError('Authentication required - please login');
        return;
      }

      const response = await fetch('/api/personas/list', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPersonas(data.personas || []);
        
        // Auto-select first persona if available
        if (data.personas && data.personas.length > 0) {
          setSelectedPersona(data.personas[0].id);
        }
      } else {
        const errorData = await response.json().catch(() => ({ message: 'Failed to load personas' }));
        setError(errorData.message || `HTTP ${response.status}`);
      }
    } catch (err) {
      console.error('Error loading personas:', err);
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setLoading(false);
    }
  };

  const selectedPersonaData = personas.find(p => p.id === selectedPersona);

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="bg-white rounded-lg border p-6">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen overflow-y-auto p-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">🧪 Agent Testing Lab</h1>
        <p className="text-gray-600">
          Test Sprint 7 Phase 2: Automatic ElevenLabs Agent Creation & Management
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="text-red-800">
            <strong>❌ Error:</strong> {error}
          </div>
          <button
            onClick={loadPersonas}
            className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* Sprint 7 Phase 2 Overview */}
      <div className="mb-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-3">🚀 Sprint 7 Phase 2 Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <h3 className="font-medium text-blue-800 mb-2">✅ Implemented:</h3>
            <ul className="space-y-1 text-blue-700">
              <li>• Automatic agent creation via API</li>
              <li>• Agent lifecycle management (CRUD)</li>
              <li>• Dynamic webhook routing by persona</li>
              <li>• Agent status monitoring</li>
              <li>• Error handling & retry logic</li>
              <li>• Frontend testing interface</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-blue-800 mb-2">🧪 Testing Features:</h3>
            <ul className="space-y-1 text-blue-700">
              <li>• Manual agent creation/deletion</li>
              <li>• Agent status verification</li>
              <li>• Webhook URL generation</li>
              <li>• Real-time status updates</li>
              <li>• Cross-persona isolation</li>
              <li>• Error recovery testing</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Persona Selection */}
      {personas.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Select Persona to Test</h2>
            <div className="text-sm text-gray-500 flex items-center">
              <span className="mr-1">👇</span>
              Scroll down for agent management
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {personas.map((persona) => (
              <div
                key={persona.id}
                onClick={() => setSelectedPersona(persona.id)}
                className={`cursor-pointer border rounded-lg p-4 transition-all ${
                  selectedPersona === persona.id
                    ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{persona.name}</h3>
                  <AgentStatusBadge personaId={persona.id} />
                </div>
                <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                  {persona.description || 'No description available'}
                </p>
                <div className="text-xs text-gray-500">
                  <strong>ID:</strong> {persona.id.substring(0, 8)}...
                  <br />
                  <strong>Chunks:</strong> {persona.chunk_count || 0}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Agent Management Interface */}
      {selectedPersonaData && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Agent Management: {selectedPersonaData.name}
          </h2>
          <AgentManager
            personaId={selectedPersonaData.id}
            personaName={selectedPersonaData.name}
            onAgentUpdate={(agentId) => {
              console.log(`Agent updated for ${selectedPersonaData.name}:`, agentId);
            }}
          />
        </div>
      )}

      {/* Testing Instructions */}
      <div className="mb-8 bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🔧 Testing Instructions</h2>
        <div className="space-y-4 text-sm text-gray-700">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">1. Test Agent Creation:</h3>
            <ul className="ml-4 space-y-1">
              <li>• Select a persona above that shows "No Voice" status</li>
              <li>• Click "🎤 Create Agent" to test automatic agent creation</li>
              <li>• Watch for success message with agent ID</li>
              <li>• Status should change to "ACTIVE" with green checkmark</li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-2">2. Test Agent Management:</h3>
            <ul className="ml-4 space-y-1">
              <li>• Use "🔄 Refresh Status" to verify agent exists in ElevenLabs</li>
              <li>• Try "🔄 Recreate Agent" to test recreation functionality</li>
              <li>• Use "🗑️ Delete Agent" to test cleanup (confirm in popup)</li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-2">3. Test Voice Integration:</h3>
            <ul className="ml-4 space-y-1">
              <li>• Once agent is active, test webhook URL is displayed</li>
              <li>• Voice conversations should route to correct persona knowledge</li>
              <li>• Knowledge base isolation should prevent cross-persona access</li>
            </ul>
          </div>
        </div>
      </div>

      {/* API Endpoints Reference */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">📡 API Endpoints</h2>
        <div className="space-y-2 text-sm font-mono">
          <div><span className="text-green-600">GET</span> /api/personas/list</div>
          <div><span className="text-blue-600">GET</span> /api/personas/{'{persona_id}'}/agent/status</div>
          <div><span className="text-orange-600">POST</span> /api/personas/{'{persona_id}'}/agent/create</div>
          <div><span className="text-orange-600">POST</span> /api/personas/{'{persona_id}'}/agent/recreate</div>
          <div><span className="text-red-600">DELETE</span> /api/personas/{'{persona_id}'}/agent</div>
          <div><span className="text-purple-600">POST</span> /elevenlabs/function-call/{'{persona_id}'}</div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          href="/clones"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          📋 View All Clones
        </Link>
        {selectedPersonaData && (
          <>
            <Link
              href={`/clones/${selectedPersonaData.id}`}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              ✏️ Edit Persona
            </Link>
            <Link
              href={`/voice/${selectedPersonaData.id}`}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              🎤 Voice Settings
            </Link>
            <Link
              href={`/test-conversational-ai`}
              className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors"
            >
              🗣️ Test Voice Chat
            </Link>
          </>
        )}
      </div>
    </div>
  );
} 