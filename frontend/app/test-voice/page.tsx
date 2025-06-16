'use client';

import React, { useState } from 'react';
import { useVoiceContext } from '@/lib/contexts/VoiceContext';
import { usePersonaAgent } from '@/lib/hooks/usePersonaAgent';
import { VoiceChat } from '@/components/voice/VoiceChat';
import { TranscriptDisplay } from '@/components/voice/TranscriptDisplay';

interface TranscriptMessage {
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export default function TestVoicePage() {
  const { isVoiceEnabled, apiKey } = useVoiceContext();
  const [selectedPersonaId, setSelectedPersonaId] = useState<string>('test-persona');
  const { agentId, loading, error } = usePersonaAgent(selectedPersonaId);
  const [transcriptMessages, setTranscriptMessages] = useState<TranscriptMessage[]>([]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-2xl font-bold mb-6">ElevenLabs Voice Chat Test</h1>
          
          {/* Status Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="space-y-2">
              <h2 className="text-lg font-semibold">Voice Status</h2>
              <div className={`p-3 rounded-lg ${isVoiceEnabled ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                <p className="font-medium">
                  {isVoiceEnabled ? '✅ Voice Enabled' : '❌ Voice Disabled'}
                </p>
                <p className="text-sm">
                  API Key: {apiKey ? '✅ Present' : '❌ Missing'}
                </p>
              </div>
            </div>
            
            <div className="space-y-2">
              <h2 className="text-lg font-semibold">Agent Status</h2>
              <div className={`p-3 rounded-lg ${agentId ? 'bg-green-50 text-green-800' : 'bg-amber-50 text-amber-800'}`}>
                {loading ? (
                  <p>🔄 Loading agent...</p>
                ) : error ? (
                  <p>❌ Error: {error}</p>
                ) : agentId ? (
                  <p>✅ Agent ID: {agentId}</p>
                ) : (
                  <p>⚠️ No agent configured</p>
                )}
              </div>
            </div>
          </div>

          {/* Environment Setup Instructions */}
          {!isVoiceEnabled && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h3 className="font-semibold text-blue-900 mb-2">Setup Instructions</h3>
              <div className="text-sm text-blue-800 space-y-2">
                <p>1. Create a <code className="bg-blue-100 px-1 rounded">.env.local</code> file in the frontend directory</p>
                <p>2. Add voice configuration:</p>
                <pre className="bg-blue-100 p-2 rounded mt-1">
{`NEXT_PUBLIC_ENABLE_VOICE=true`}
                </pre>
                <p className="text-sm">API key is configured server-side for security.</p>
                <p>3. Restart the development server</p>
              </div>
            </div>
          )}

          {/* Persona Selection */}
          <div className="mb-6">
            <label htmlFor="persona-select" className="block text-sm font-medium text-gray-700 mb-2">
              Test Persona ID
            </label>
            <input
              id="persona-select"
              type="text"
              value={selectedPersonaId}
              onChange={(e) => setSelectedPersonaId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter persona ID (e.g., test-persona)"
            />
            <p className="text-xs text-gray-500 mt-1">
              In production, this would be selected from your personas list
            </p>
          </div>

          {/* Voice Chat Component */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">Voice Chat Interface</h2>
            <VoiceChat
              personaId={selectedPersonaId}
              agentId={agentId || 'test-agent'}
              onTranscript={(text, isUser) => {
                console.log('[TestVoice] Transcript:', { text, isUser });
                setTranscriptMessages(prev => [...prev, {
                  text,
                  isUser,
                  timestamp: new Date()
                }]);
              }}
              onError={(error) => {
                console.error('[TestVoice] Voice error:', error);
                alert(`Voice Error: ${error}`);
              }}
            />
          </div>

          {/* Transcript Display */}
          {transcriptMessages.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-3">Voice Transcript</h2>
              <TranscriptDisplay messages={transcriptMessages} />
              <button
                onClick={() => setTranscriptMessages([])}
                className="mt-2 text-sm text-gray-500 hover:text-gray-700"
              >
                Clear Transcript
              </button>
            </div>
          )}

          {/* Integration Notes */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-2">Integration Notes</h3>
            <div className="text-sm text-gray-600 space-y-1">
              <p>• Voice chat is integrated into the main chat interface at <code>/chat/[persona]</code></p>
              <p>• Toggle voice chat using the microphone button in the chat header</p>
              <p>• Voice conversations use function calling to query the persona's knowledge base</p>
              <p>• Transcripts appear alongside regular text messages</p>
              <p>• All voice features require a valid ElevenLabs API key and configured agents</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 