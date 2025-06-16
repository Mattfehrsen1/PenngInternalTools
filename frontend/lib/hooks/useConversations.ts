import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '@/lib/api';

export interface Conversation {
  id: string;
  title: string;
  persona_name: string;
  persona_id: string;
  last_message_at?: Date;
  message_count: number;
  created_at: Date;
}

export interface ConversationDetail {
  id: string;
  title: string;
  persona_id: string;
  persona_name: string;
  persona_description?: string;
  created_at: Date;
  updated_at: Date;
}

export interface Message {
  id: string;
  role: string;
  content: string;
  citations?: any[];
  token_count?: number;
  model?: string;
  created_at: Date;
}

export interface ConversationData {
  conversation: ConversationDetail;
  messages: Message[];
  persona: any;
}

interface UseConversationsReturn {
  conversations: Conversation[];
  loading: boolean;
  error: string | null;
  hasMore: boolean;
  loadConversations: () => Promise<void>;
  loadConversationById: (threadId: string) => Promise<ConversationData | null>;
  loadMoreConversations: () => Promise<void>;
  refreshConversations: () => Promise<void>;
}

export function useConversations(token: string | null): UseConversationsReturn {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [lastConversationId, setLastConversationId] = useState<string | null>(null);

  const loadConversations = useCallback(async () => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/conversations?limit=20`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const newConversations = data.conversations || [];
        
        setConversations(newConversations);
        setHasMore(data.has_more || false);
        setLastConversationId(
          newConversations.length > 0 
            ? newConversations[newConversations.length - 1].id 
            : null
        );
      } else {
        throw new Error('Failed to load conversations');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversations');
    } finally {
      setLoading(false);
    }
  }, [token]);

  const loadConversationById = useCallback(async (threadId: string): Promise<ConversationData | null> => {
    if (!token) return null;

    try {
      const response = await fetch(`${API_URL}/conversations/${threadId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        return data;
      } else {
        throw new Error('Conversation not found');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversation');
      return null;
    }
  }, [token]);

  const loadMoreConversations = useCallback(async () => {
    if (!token || !hasMore || loading || !lastConversationId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/conversations?limit=20&before=${lastConversationId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        const newConversations = data.conversations || [];
        
        setConversations(prev => [...prev, ...newConversations]);
        setHasMore(data.has_more || false);
        setLastConversationId(
          newConversations.length > 0 
            ? newConversations[newConversations.length - 1].id 
            : lastConversationId
        );
      } else {
        throw new Error('Failed to load more conversations');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load more conversations');
    } finally {
      setLoading(false);
    }
  }, [token, hasMore, loading, lastConversationId]);

  const refreshConversations = useCallback(async () => {
    setLastConversationId(null);
    setHasMore(true);
    await loadConversations();
  }, [loadConversations]);

  // Load conversations when token becomes available
  useEffect(() => {
    if (token) {
      loadConversations();
    }
  }, [token, loadConversations]);

  return {
    conversations,
    loading,
    error,
    hasMore,
    loadConversations,
    loadConversationById,
    loadMoreConversations,
    refreshConversations,
  };
} 