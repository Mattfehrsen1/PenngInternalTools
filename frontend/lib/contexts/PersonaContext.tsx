'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export interface Persona {
  id: string;
  name: string;
  description: string;
  slug: string; // URL-friendly version of name
  chunks: number; // Number of knowledge chunks
}

interface ApiPersona {
  id: string;
  name: string;
  description?: string;
  chunk_count: number; // API uses 'chunk_count', not 'chunks'
  source_type?: string;
  created_at?: string;
}

interface PersonaContextType {
  selectedPersona: Persona | null;
  personas: Persona[];
  setSelectedPersona: (persona: Persona | null) => void;
  loadPersonas: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

const PersonaContext = createContext<PersonaContextType | undefined>(undefined);

interface PersonaProviderProps {
  children: ReactNode;
}

export function PersonaProvider({ children }: PersonaProviderProps) {
  const [selectedPersona, setSelectedPersonaState] = useState<Persona | null>(null);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  // API-only approach - no mock data fallback

  // Load personas from API
  const loadPersonas = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.log('[PersonaContext] No auth token found, user needs to log in');
        setError('No authentication token found. Please log in.');
        setLoading(false);
        return;
      }

      console.log('[PersonaContext] Loading personas from API: /api/personas/list');
      const response = await fetch('/api/personas/list', {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
      });

      console.log('[PersonaContext] API response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('[PersonaContext] API response data:', data);
        const apiPersonas: ApiPersona[] = data.personas || [];
        
        // Transform API personas to match our interface
        const transformedPersonas = apiPersonas.map((p) => ({
          id: p.id,
          name: p.name,
          description: p.description || 'AI Assistant',
          slug: generateSlug(p.name),
          chunks: p.chunk_count || 0, // Fix: Use 'chunk_count' from API
        }));
        
        console.log('[PersonaContext] Transformed personas:', transformedPersonas);
        
        if (transformedPersonas.length > 0) {
          setPersonas(transformedPersonas);
          
          // Restore last selected persona from localStorage
          const savedPersonaId = localStorage.getItem('selectedPersonaId');
          if (savedPersonaId) {
            const savedPersona = transformedPersonas.find(p => p.id === savedPersonaId);
            if (savedPersona) {
              console.log('[PersonaContext] Restored saved persona:', savedPersona.name);
              setSelectedPersonaState(savedPersona);
            } else {
              console.log('[PersonaContext] Saved persona not found, selecting first persona');
              localStorage.removeItem('selectedPersonaId');
              setSelectedPersonaState(transformedPersonas[0]);
              localStorage.setItem('selectedPersonaId', transformedPersonas[0].id);
            }
          } else {
            console.log('[PersonaContext] No saved persona, selecting first persona');
            setSelectedPersonaState(transformedPersonas[0]);
            localStorage.setItem('selectedPersonaId', transformedPersonas[0].id);
          }
        } else {
          console.log('[PersonaContext] No personas found in API response');
          setError('No personas found. Create a persona first.');
        }
      } else {
        const errorText = await response.text();
        console.error('[PersonaContext] API call failed:', response.status, errorText);
        setError(`Failed to load personas: ${response.status} ${errorText}`);
      }
    } catch (err) {
      console.error('[PersonaContext] Error loading personas:', err);
      setError('Failed to load personas: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Set selected persona and persist to localStorage
  const setSelectedPersona = (persona: Persona | null) => {
    setSelectedPersonaState(persona);
    
    if (persona) {
      localStorage.setItem('selectedPersonaId', persona.id);
    } else {
      localStorage.removeItem('selectedPersonaId');
    }
  };

  // Extract persona from URL on route changes
  useEffect(() => {
    if (personas.length === 0) return;
    
    const personaMatch = pathname?.match(/\/(chat|prompts|files|voice)\/([^\/]+)/);
    if (personaMatch && personaMatch[2]) {
      const personaSlug = personaMatch[2];
      const persona = personas.find(p => p.slug === personaSlug || p.id === personaSlug);
      if (persona && (!selectedPersona || selectedPersona.id !== persona.id)) {
        setSelectedPersonaState(persona);
        localStorage.setItem('selectedPersonaId', persona.id);
      }
    }
  }, [pathname, personas, selectedPersona]);

  // Load personas on mount
  useEffect(() => {
    loadPersonas();
  }, []);

  const value: PersonaContextType = {
    selectedPersona,
    personas,
    setSelectedPersona,
    loadPersonas,
    loading,
    error,
  };

  return (
    <PersonaContext.Provider value={value}>
      {children}
    </PersonaContext.Provider>
  );
}

export function usePersona() {
  const context = useContext(PersonaContext);
  if (context === undefined) {
    throw new Error('usePersona must be used within a PersonaProvider');
  }
  return context;
}

// Utility function to generate slug from name
export function generateSlug(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
} 