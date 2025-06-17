'use client';

import { useState, useEffect } from 'react';

interface AgentStatus {
  status: 'active' | 'not_found' | 'error' | 'unavailable' | 'not_configured';
  agent_id?: string;
  name?: string;
  voice_id?: string;
  created_at?: string;
  error?: string;
}

interface AgentManagerProps {
  personaId: string;
  personaName: string;
  onAgentUpdate?: (agentId: string | null) => void;
}

export default function AgentManager({ personaId, personaName, onAgentUpdate }: AgentManagerProps) {
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load agent status on component mount
  useEffect(() => {
    loadAgentStatus();
  }, [personaId]);

  const getAuthToken = () => {
    return localStorage.getItem('auth_token') || localStorage.getItem('token');
  };

  const loadAgentStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await fetch(`/api/personas/${personaId}/agent/status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAgentStatus(data);
        
        // Notify parent component of agent status
        if (onAgentUpdate) {
          onAgentUpdate(data.agent_id || null);
        }
      } else {
        const errorData = await response.json().catch(() => ({ message: 'Failed to load agent status' }));
        setError(errorData.message || `HTTP ${response.status}`);
      }
    } catch (err) {
      console.error('Error loading agent status:', err);
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setLoading(false);
    }
  };

  const createAgent = async () => {
    try {
      setActionLoading('create');
      setError(null);
      setSuccess(null);

      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await fetch(`/api/personas/${personaId}/agent/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          voice_id: null, // Use default voice
          system_prompt: null // Use default prompt
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSuccess(`✅ Created ElevenLabs agent: ${data.agent_id}`);
          await loadAgentStatus(); // Reload status
        } else {
          setError(data.message || 'Failed to create agent');
        }
      } else {
        const errorData = await response.json().catch(() => ({ message: 'Failed to create agent' }));
        setError(errorData.message || `HTTP ${response.status}`);
      }
    } catch (err) {
      console.error('Error creating agent:', err);
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setActionLoading(null);
    }
  };

  const recreateAgent = async () => {
    try {
      setActionLoading('recreate');
      setError(null);
      setSuccess(null);

      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await fetch(`/api/personas/${personaId}/agent/recreate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSuccess(`✅ Recreated ElevenLabs agent: ${data.agent_id}`);
          await loadAgentStatus(); // Reload status
        } else {
          setError(data.message || 'Failed to recreate agent');
        }
      } else {
        const errorData = await response.json().catch(() => ({ message: 'Failed to recreate agent' }));
        setError(errorData.message || `HTTP ${response.status}`);
      }
    } catch (err) {
      console.error('Error recreating agent:', err);
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setActionLoading(null);
    }
  };

  const deleteAgent = async () => {
    if (!confirm(`Are you sure you want to delete the ElevenLabs agent for "${personaName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setActionLoading('delete');
      setError(null);
      setSuccess(null);

      const token = getAuthToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await fetch(`/api/personas/${personaId}/agent`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSuccess(`✅ Deleted ElevenLabs agent`);
          await loadAgentStatus(); // Reload status
        } else {
          setError(data.message || 'Failed to delete agent');
        }
      } else {
        const errorData = await response.json().catch(() => ({ message: 'Failed to delete agent' }));
        setError(errorData.message || `HTTP ${response.status}`);
      }
    } catch (err) {
      console.error('Error deleting agent:', err);
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'not_configured': return 'bg-yellow-100 text-yellow-800';
      case 'not_found': return 'bg-red-100 text-red-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'unavailable': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return '✅';
      case 'not_configured': return '⚠️';
      case 'not_found': return '❌';
      case 'error': return '💥';
      case 'unavailable': return '🔌';
      default: return '❓';
    }
  };

  const getStatusMessage = (status: AgentStatus) => {
    switch (status.status) {
      case 'active':
        return `Agent active (ID: ${status.agent_id})`;
      case 'not_configured':
        return 'No ElevenLabs agent configured';
      case 'not_found':
        return 'Agent not found in ElevenLabs';
      case 'error':
        return `Error: ${status.error}`;
      case 'unavailable':
        return 'ElevenLabs API unavailable';
      default:
        return 'Unknown status';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🎙️ Voice Agent Status</h3>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">🎙️ Voice Agent Management</h3>
      
      {/* Status Display */}
      {agentStatus && (
        <div className="mb-6">
          <div className="flex items-center space-x-3 mb-3">
            <span className="text-xl">{getStatusIcon(agentStatus.status)}</span>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(agentStatus.status)}`}
            >
              {agentStatus.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          
          <p className="text-gray-600 mb-2">
            {getStatusMessage(agentStatus)}
          </p>
          
          {agentStatus.agent_id && (
            <div className="text-sm text-gray-500 space-y-1">
              <div><strong>Agent ID:</strong> {agentStatus.agent_id}</div>
              {agentStatus.name && <div><strong>Name:</strong> {agentStatus.name}</div>}
              {agentStatus.voice_id && <div><strong>Voice ID:</strong> {agentStatus.voice_id}</div>}
              {agentStatus.created_at && <div><strong>Created:</strong> {new Date(agentStatus.created_at).toLocaleString()}</div>}
            </div>
          )}
        </div>
      )}

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-800 text-sm">❌ {error}</p>
        </div>
      )}
      
      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <p className="text-green-800 text-sm">{success}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3">
        {(!agentStatus || agentStatus.status === 'not_configured') && (
          <button
            onClick={createAgent}
            disabled={actionLoading === 'create'}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading === 'create' ? '⏳ Creating...' : '🎤 Create Agent'}
          </button>
        )}
        
        {agentStatus && (agentStatus.status === 'not_found' || agentStatus.status === 'error') && (
          <button
            onClick={recreateAgent}
            disabled={actionLoading === 'recreate'}
            className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading === 'recreate' ? '⏳ Recreating...' : '🔄 Recreate Agent'}
          </button>
        )}
        
        {agentStatus && agentStatus.agent_id && (
          <button
            onClick={deleteAgent}
            disabled={actionLoading === 'delete'}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading === 'delete' ? '⏳ Deleting...' : '🗑️ Delete Agent'}
          </button>
        )}
        
        <button
          onClick={loadAgentStatus}
          disabled={loading}
          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '⏳ Loading...' : '🔄 Refresh Status'}
        </button>
      </div>

      {/* Quick Test Section */}
      {agentStatus && agentStatus.status === 'active' && (
        <div className="mt-6 pt-6 border-t border-gray-100">
          <h4 className="font-medium text-gray-900 mb-3">🧪 Quick Test</h4>
          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              Agent is active and ready for voice conversations! You can test it by:
            </p>
            <ul className="text-sm text-gray-600 space-y-1 ml-4">
              <li>• Using the voice chat interface</li>
              <li>• Calling the webhook: <code className="bg-gray-100 px-2 py-1 rounded">/elevenlabs/function-call/{personaId}</code></li>
              <li>• Testing knowledge queries with voice responses</li>
            </ul>
          </div>
        </div>
      )}

      {/* Development Info */}
      <div className="mt-6 pt-6 border-t border-gray-100">
        <details className="text-sm text-gray-500">
          <summary className="cursor-pointer font-medium">🔧 Developer Info</summary>
          <div className="mt-2 space-y-1">
            <div><strong>Persona ID:</strong> {personaId}</div>
            <div><strong>API Endpoints:</strong></div>
            <ul className="ml-4 space-y-1">
              <li>• GET /api/personas/{personaId}/agent/status</li>
              <li>• POST /api/personas/{personaId}/agent/create</li>
              <li>• POST /api/personas/{personaId}/agent/recreate</li>
              <li>• DELETE /api/personas/{personaId}/agent</li>
            </ul>
          </div>
        </details>
      </div>
    </div>
  );
} 