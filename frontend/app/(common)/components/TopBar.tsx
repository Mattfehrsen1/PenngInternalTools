'use client';

import { useState, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { usePersona } from '@/lib/contexts/PersonaContext';

export default function TopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { selectedPersona, personas, setSelectedPersona, loading } = usePersona();
  const [searchQuery, setSearchQuery] = useState('');
  const [showPersonaDropdown, setShowPersonaDropdown] = useState(false);

  const currentModel = 'gpt-4o';
  const tokenCount = '2.1K';
  const testCount = '12/15';

  // Handle persona selection with navigation
  const handlePersonaSelect = (persona: any) => {
    setSelectedPersona(persona);
    setShowPersonaDropdown(false);
    
    // If we're on a persona-specific route, navigate to the same route with new persona
    const currentRoute = pathname?.match(/\/(chat|prompts|files|voice)/)?.[1];
    if (currentRoute && persona) {
      router.push(`/${currentRoute}/${persona.slug}`);
    } else if (persona) {
      // Default to chat if we're not on a persona-specific route
      router.push(`/chat/${persona.slug}`);
    }
  };

  // Handle "All Clones" selection
  const handleAllClonesSelect = () => {
    setSelectedPersona(null);
    setShowPersonaDropdown(false);
    router.push('/clones');
  };

  // Filter personas based on search
  const filteredPersonas = personas.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4">
      {/* Left Section - Brand and Persona */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <h1 className="text-lg font-semibold text-gray-900">Penng</h1>
          <span className="text-sm text-gray-500">Clone Studio</span>
        </div>
        
        {/* Enhanced Persona Selector */}
        <div className="relative">
          <button
            onClick={() => setShowPersonaDropdown(!showPersonaDropdown)}
            className="flex items-center space-x-2 px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 min-w-[180px]"
            disabled={loading}
          >
            <span className="text-gray-600">▾</span>
            <span className="text-gray-900 truncate">
              {loading ? 'Loading...' : selectedPersona ? selectedPersona.name : 'All Clones'}
            </span>
          </button>
          
          {showPersonaDropdown && !loading && (
            <div className="absolute top-full left-0 mt-1 w-72 bg-white border border-gray-200 rounded-md shadow-lg z-50">
              {/* Search Input */}
              <div className="p-2 border-b">
                <input
                  type="text"
                  placeholder="Search personas..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>
              
              <div className="max-h-60 overflow-y-auto">
                {/* All Clones Option */}
                <button
                  onClick={handleAllClonesSelect}
                  className={`w-full text-left px-3 py-3 hover:bg-gray-50 border-b transition-colors ${
                    !selectedPersona ? 'bg-orange-50 border-l-4 border-l-orange-500' : ''
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-gray-400 to-gray-600 rounded-lg flex items-center justify-center text-white font-semibold text-sm">
                      📋
                    </div>
                    <div>
                      <div className="font-medium text-sm">All Clones</div>
                      <div className="text-xs text-gray-500">Manage all your personas</div>
                    </div>
                  </div>
                </button>

                {/* Personas List */}
                {filteredPersonas.length > 0 ? (
                  filteredPersonas.map(persona => (
                    <button
                      key={persona.id}
                      onClick={() => handlePersonaSelect(persona)}
                      className={`w-full text-left px-3 py-3 hover:bg-gray-50 border-b last:border-b-0 transition-colors ${
                        selectedPersona?.id === persona.id ? 'bg-orange-50 border-l-4 border-l-orange-500' : ''
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-semibold text-sm">
                          {persona.name.charAt(0)}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-sm">{persona.name}</div>
                          <div className="text-xs text-gray-500">{persona.description}</div>
                        </div>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="px-3 py-4 text-sm text-gray-500 text-center">
                    No personas found matching "{searchQuery}"
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Breadcrumb for selected persona */}
        {selectedPersona && (
          <div className="text-sm text-gray-500">
            <span>Persona: {selectedPersona.name}</span>
            {pathname?.match(/\/(chat|prompts|files|voice)/) && (
              <span> &gt; {pathname.match(/\/(chat|prompts|files|voice)/)?.[1]?.charAt(0).toUpperCase()}{pathname.match(/\/(chat|prompts|files|voice)/)?.[1]?.slice(1)}</span>
            )}
          </div>
        )}
      </div>

      {/* Right Section - Status Indicators */}
      <div className="flex items-center space-x-4">
        {/* Voice Chat Button */}
        <button
          onClick={() => router.push('/test-conversational-ai')}
          className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all transform hover:scale-105 shadow-sm"
        >
          <span className="text-lg">🎙️</span>
          <span className="font-medium">Voice Chat</span>
        </button>

        {/* Model Status */}
        <div className="text-sm text-gray-600">
          <span className="bg-gray-100 px-2 py-1 rounded text-xs">
            Model: gpt-4o
          </span>
        </div>

        {/* Token Usage */}
        <div className="text-sm text-gray-600">
          <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs">
            Tokens: 12.3k
          </span>
        </div>

        {/* Test Status */}
        <div className="text-sm text-gray-600">
          <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
            Tests: 80%
          </span>
        </div>
      </div>
    </div>
  );
} 