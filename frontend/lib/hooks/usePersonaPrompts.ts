import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '@/lib/api';

export interface PromptVersion {
  id: string;
  layer: 'system' | 'rag' | 'user';
  name: string;
  content: string;
  version: number;
  is_active: boolean;
  created_at: string;
  commit_message?: string;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
}

export type PromptLayer = 'system' | 'rag' | 'user';

export interface PersonaPromptsState {
  prompts: Record<PromptLayer, PromptVersion | null>;
  templates: Template[];
  isLoading: boolean;
  isSaving: boolean;
  isApplyingTemplate: boolean;
  error: string | null;
}

export interface PersonaPromptsActions {
  loadPrompts: () => Promise<void>;
  loadTemplates: () => Promise<void>;
  savePrompt: (layer: PromptLayer, content: string, commitMessage?: string) => Promise<void>;
  applyTemplate: (templateName: string) => Promise<void>;
  clearError: () => void;
}

export function usePersonaPrompts(
  personaId: string,
  token: string | null
): PersonaPromptsState & PersonaPromptsActions {
  const [state, setState] = useState<PersonaPromptsState>({
    prompts: {
      system: null,
      rag: null,
      user: null,
    },
    templates: [],
    isLoading: false,
    isSaving: false,
    isApplyingTemplate: false,
    error: null,
  });

  const updateState = useCallback((updates: Partial<PersonaPromptsState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const clearError = useCallback(() => {
    updateState({ error: null });
  }, [updateState]);

  const loadPrompts = useCallback(async () => {
    if (!token || !personaId) return;

    try {
      updateState({ isLoading: true, error: null });

      const response = await fetch(`${API_URL}/personas/${personaId}/prompts`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error('Failed to load persona prompts');
      }

      const data = await response.json();
      
      // Convert API response to organized structure
      const organizedPrompts: Record<PromptLayer, PromptVersion | null> = {
        system: null,
        rag: null,
        user: null,
      };

      // Handle different response formats
      if (data.prompts) {
        // If prompts is an object with layers as keys
        Object.entries(data.prompts).forEach(([layer, versions]) => {
          const layerVersions = versions as PromptVersion[];
          const activePrompt = layerVersions?.find(v => v.is_active);
          if (activePrompt) {
            organizedPrompts[layer as PromptLayer] = activePrompt;
          }
        });
      }

      updateState({ prompts: organizedPrompts, isLoading: false });
    } catch (err) {
      updateState({ 
        error: err instanceof Error ? err.message : 'Failed to load prompts',
        isLoading: false,
      });
    }
  }, [token, personaId, updateState]);

  const loadTemplates = useCallback(async () => {
    if (!token) return;

    try {
      console.log('Loading templates from:', `${API_URL}/personas/templates`);
      
      const response = await fetch(`${API_URL}/personas/templates`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      console.log('Templates response status:', response.status);
      console.log('Templates response ok:', response.ok);

      if (response.ok) {
        const data = await response.json();
        console.log('Templates data received:', data);
        updateState({ templates: data.templates || [] });
      } else {
        const errorText = await response.text();
        console.error('Templates request failed:', response.status, errorText);
      }
    } catch (err) {
      console.error('Failed to load templates:', err);
      // Don't set error for template loading failures
    }
  }, [token, updateState]);

  const savePrompt = useCallback(async (
    layer: PromptLayer,
    content: string,
    commitMessage?: string
  ) => {
    if (!token || !personaId) return;

    try {
      updateState({ isSaving: true, error: null });

      const response = await fetch(
        `${API_URL}/personas/${personaId}/prompts/${layer}/main/versions`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content,
            commitMessage: commitMessage || `Updated ${layer} prompt via editor`,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save prompt');
      }

      const result = await response.json();
      
      // Update local state with new version
      updateState({
        prompts: {
          ...state.prompts,
          [layer]: result.version,
        },
        isSaving: false,
      });

    } catch (err) {
      updateState({
        error: err instanceof Error ? err.message : 'Failed to save prompt',
        isSaving: false,
      });
      throw err; // Re-throw for component handling
    }
  }, [token, personaId, updateState, state.prompts]);

  const applyTemplate = useCallback(async (templateName: string) => {
    if (!token || !personaId) return;

    try {
      console.log('Applying template:', templateName);
      console.log('Persona ID:', personaId);
      console.log('API URL:', `${API_URL}/personas/${personaId}/prompts/from-template`);
      
      updateState({ isApplyingTemplate: true, error: null });

      const requestBody = JSON.stringify({
        template_name: templateName,  // Backend expects snake_case
      });
      console.log('Request body:', requestBody);

      const response = await fetch(
        `${API_URL}/personas/${personaId}/prompts/from-template`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: requestBody,
        }
      );

      console.log('Template application response status:', response.status);
      console.log('Template application response ok:', response.ok);

      if (!response.ok) {
        const responseText = await response.text();
        console.error('Template application failed:', response.status, responseText);
        
        let errorMessage = 'Failed to apply template';
        try {
          const errorData = JSON.parse(responseText);
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // If we can't parse the error response, use status text
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('Template application result:', result);

      // Reload prompts after template application
      await loadPrompts();
      
      updateState({ isApplyingTemplate: false });

    } catch (err) {
      console.error('Template application error:', err);
      updateState({
        error: err instanceof Error ? err.message : 'Failed to apply template',
        isApplyingTemplate: false,
      });
      throw err; // Re-throw for component handling
    }
  }, [token, personaId, updateState, loadPrompts]);

  // Auto-load prompts and templates when dependencies change
  useEffect(() => {
    if (token && personaId) {
      loadPrompts();
      loadTemplates();
    }
  }, [token, personaId, loadPrompts, loadTemplates]);

  return {
    ...state,
    loadPrompts,
    loadTemplates,
    savePrompt,
    applyTemplate,
    clearError,
  };
} 