'use client';

import React, { useState } from 'react';
import { usePersona } from '@/lib/contexts/PersonaContext';
import { useRouter } from 'next/navigation';

interface PersonaSelectorProps {
  currentPath?: string; // e.g., 'files', 'prompts', 'chat' 
  className?: string;
}

export default function PersonaSelector({ currentPath = '', className = '' }: PersonaSelectorProps) {
  const { selectedPersona, personas, setSelectedPersona, loading, error } = usePersona();
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  const handlePersonaSelect = (personaId: string) => {
    const persona = personas.find(p => p.id === personaId);
    if (persona) {
      setSelectedPersona(persona);
      setIsOpen(false);
      
      // Navigate to the same type of page but with new persona
      if (currentPath) {
        router.push(`/${currentPath}/${persona.slug}`);
      }
    }
  };

  if (loading) return <div className="text-sm text-gray-500">Loading personas...</div>;
  if (error) return <div className="text-sm text-red-500">Error: {error}</div>;
  if (personas.length === 0) return <div className="text-sm text-gray-500">No personas available</div>;

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-4 py-2 text-left bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
      >
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium text-indigo-600">
              {selectedPersona?.name.charAt(0).toUpperCase() || '?'}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-900 truncate">
              {selectedPersona?.name || 'Select Persona'}
            </p>
            <p className="text-xs text-gray-500 truncate">
              {selectedPersona?.description || 'No persona selected'}
            </p>
          </div>
        </div>
        
        <svg 
          className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {personas.map((persona) => (
            <button
              key={persona.id}
              onClick={() => handlePersonaSelect(persona.id)}
              className={`w-full px-4 py-3 text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50 ${
                selectedPersona?.id === persona.id ? 'bg-indigo-50 border-l-4 border-indigo-500' : ''
              }`}
            >
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  selectedPersona?.id === persona.id ? 'bg-indigo-100' : 'bg-gray-100'
                }`}>
                  <span className={`text-sm font-medium ${
                    selectedPersona?.id === persona.id ? 'text-indigo-600' : 'text-gray-600'
                  }`}>
                    {persona.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className={`text-sm font-medium truncate ${
                    selectedPersona?.id === persona.id ? 'text-indigo-900' : 'text-gray-900'
                  }`}>
                    {persona.name}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {persona.description}
                  </p>
                  {persona.chunks > 0 && (
                    <p className="text-xs text-gray-400">
                      {persona.chunks} knowledge chunks
                    </p>
                  )}
                </div>
                {/* Active persona checkmark */}
                {selectedPersona?.id === persona.id && (
                  <div className="text-indigo-600">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
            </button>
          ))}
          
          {/* Divider */}
          <div className="border-t border-gray-200 my-1"></div>
          
          {/* Management Options */}
          <button
            onClick={() => {
              setIsOpen(false);
              router.push('/clones');
            }}
            className="w-full px-4 py-3 text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50"
          >
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                <span className="text-sm text-gray-600">📋</span>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900">All Clones...</p>
                <p className="text-xs text-gray-500">Manage all your AI personas</p>
              </div>
            </div>
          </button>
          
          <button
            onClick={() => {
              setIsOpen(false);
              router.push('/clones?create=true');
            }}
            className="w-full px-4 py-3 text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50"
          >
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-sm text-green-600">➕</span>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900">Create New Clone</p>
                <p className="text-xs text-gray-500">Build a new AI persona</p>
              </div>
            </div>
          </button>
        </div>
      )}
    </div>
  );
} 