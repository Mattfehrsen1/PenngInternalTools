'use client';

import { useParams } from 'next/navigation';
import { usePersona } from '@/lib/contexts/PersonaContext';

export default function VideoPage() {
  const params = useParams();
  const { selectedPersona } = usePersona();
  const personaSlug = params.persona as string;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center max-w-md">
        <div className="mb-8">
          <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center text-white text-4xl mx-auto mb-4">
            📹
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Video Calls</h1>
          <p className="text-gray-600">
            Face-to-face conversations with {selectedPersona?.name || personaSlug}
          </p>
        </div>
        
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Coming Soon</h2>
          <p className="text-gray-600 mb-4">
            Video calling functionality will be available in a future update with avatar integration.
          </p>
          <div className="space-y-2 text-sm text-gray-500">
            <p>🎥 Real-time video conversations</p>
            <p>👤 Persona avatar representation</p>
            <p>🎭 Synchronized voice and visuals</p>
          </div>
        </div>

        <div className="mt-6 text-sm text-gray-500">
          For now, use the <strong>Chat</strong> interface with voice playback
        </div>
      </div>
    </div>
  );
} 