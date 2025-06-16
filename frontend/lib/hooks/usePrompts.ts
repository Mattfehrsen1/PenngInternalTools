import { useState, useEffect, useCallback } from 'react';

export interface PromptInfo {
  name: string;
  layer: string;
  active_version?: number;
  active_version_id?: string;
  total_versions: number;
  last_updated?: string;
}

export interface CreatePromptData {
  layer: string;
  name: string;
  content: string;
  commit_message: string;
}

interface UsePromptsReturn {
  prompts: Record<string, PromptInfo[]>;
  loading: boolean;
  error: string | null;
  fetchPrompts: () => Promise<void>;
  createPrompt: (data: CreatePromptData) => Promise<boolean>;
  refreshPrompts: () => Promise<void>;
}

export function usePrompts(token: string | null): UsePromptsReturn {
  const [prompts, setPrompts] = useState<Record<string, PromptInfo[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrompts = useCallback(async () => {
    if (!token) {
      console.log('🔧 usePrompts: No token provided');
      return;
    }

    console.log('🔧 usePrompts: Fetching prompts with token:', token.substring(0, 20) + '...');
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/prompts', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('🔧 usePrompts: Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('🔧 usePrompts: Response data:', data);
        setPrompts(data.prompts || {});
      } else {
        const errorText = await response.text();
        console.error('🔧 usePrompts: Error response:', errorText);
        throw new Error(`Failed to load prompts: ${response.status} ${errorText}`);
      }
    } catch (err) {
      console.error('🔧 usePrompts: Catch error:', err);
      setError(err instanceof Error ? err.message : 'Error loading prompts');
    } finally {
      setLoading(false);
    }
  }, [token]);

  const createPrompt = useCallback(async (data: CreatePromptData): Promise<boolean> => {
    if (!token) return false;

    try {
      const response = await fetch('/api/prompts', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        await fetchPrompts(); // Refresh the list
        return true;
      } else {
        const errorData = await response.text();
        throw new Error(`Failed to create prompt: ${errorData}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error creating prompt');
      return false;
    }
  }, [token, fetchPrompts]);

  const refreshPrompts = useCallback(async () => {
    await fetchPrompts();
  }, [fetchPrompts]);

  // Load prompts when token becomes available
  useEffect(() => {
    if (token) {
      fetchPrompts();
    }
  }, [token, fetchPrompts]);

  return {
    prompts,
    loading,
    error,
    fetchPrompts,
    createPrompt,
    refreshPrompts,
  };
} 