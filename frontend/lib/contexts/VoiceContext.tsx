'use client';

import React, { createContext, useContext, ReactNode } from 'react';

interface VoiceContextType {
  isVoiceEnabled: boolean;
  apiKey: string | null;
}

const VoiceContext = createContext<VoiceContextType>({
  isVoiceEnabled: false,
  apiKey: null
});

export function VoiceContextProvider({ children }: { children: ReactNode }) {
  // Server-side only approach - no API key needed in frontend
  const isVoiceEnabled = process.env.NEXT_PUBLIC_ENABLE_VOICE === 'true';
  const apiKey = null; // Server-side only

  console.log('[VoiceContext] Voice enabled (server-side):', isVoiceEnabled);

  return (
    <VoiceContext.Provider value={{ isVoiceEnabled, apiKey }}>
      {children}
    </VoiceContext.Provider>
  );
}

export const useVoiceContext = () => {
  const context = useContext(VoiceContext);
  if (!context) {
    throw new Error('useVoiceContext must be used within a VoiceContextProvider');
  }
  return context;
}; 