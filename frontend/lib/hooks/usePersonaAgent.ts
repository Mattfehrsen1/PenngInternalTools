import { useState, useEffect } from 'react';

export function usePersonaAgent(personaId: string | null) {
  const [agentId, setAgentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAgentId() {
      if (!personaId) {
        setAgentId(null);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const token = localStorage.getItem('auth_token');
        if (!token) {
          throw new Error('No authentication token found');
        }

        console.log('[usePersonaAgent] Fetching agent ID for persona:', personaId);
        const response = await fetch(`/api/personas/${personaId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch persona: ${response.status}`);
        }

        const persona = await response.json();
        console.log('[usePersonaAgent] Persona data:', persona);
        
        const agentId = persona.elevenlabs_agent_id || null;
        console.log('[usePersonaAgent] Agent ID:', agentId);
        
        setAgentId(agentId);
      } catch (err) {
        console.error('[usePersonaAgent] Error fetching agent ID:', err);
        setError(err instanceof Error ? err.message : 'Failed to load agent ID');
        setAgentId(null);
      } finally {
        setLoading(false);
      }
    }

    fetchAgentId();
  }, [personaId]);

  return { agentId, loading, error };
} 