'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { usePersona } from '@/lib/contexts/PersonaContext';
import { useConversation } from '@elevenlabs/react';

// Types for conversation state
interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export default function CallPage() {
  const params = useParams();
  const { selectedPersona, personas } = usePersona();
  const personaSlug = params.persona as string;

  // Find persona by slug
  const persona = personas.find(p => p.slug === personaSlug) || selectedPersona;

  const [isConnected, setIsConnected] = useState(false);
  const [agentStatus, setAgentStatus] = useState('listening');
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [agentId, setAgentId] = useState<string | null>(null);
  const [loadingAgent, setLoadingAgent] = useState(true);

  // Load agent ID for persona
  useEffect(() => {
    const loadAgentId = async () => {
      if (!persona?.id) return;

      try {
        setLoadingAgent(true);
        const token = localStorage.getItem('auth_token') || localStorage.getItem('token');
        
        const response = await fetch(`/api/personas/${persona.id}/agent/status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.status === 'active' && data.agent_id) {
            setAgentId(data.agent_id);
          } else {
            setError(`No voice agent configured for ${persona.name}. Please create an agent first.`);
          }
        } else {
          setError('Failed to load agent information');
        }
      } catch (err) {
        console.error('Error loading agent:', err);
        setError('Failed to connect to agent service');
      } finally {
        setLoadingAgent(false);
      }
    };

    loadAgentId();
  }, [persona?.id]);

  // Real ElevenLabs Conversational AI integration
  const conversation = useConversation({
    onConnect: () => {
      console.log('🎙️ Connected to ElevenLabs Conversational AI');
      setIsConnected(true);
      setError(null);
    },
    onDisconnect: (reason) => {
      console.log('📞 Disconnected from ElevenLabs:', reason);
      setIsConnected(false);
      setAgentStatus('listening');
    },
    onMessage: (props: { message: string; source: any }) => {
      console.log('💬 Message received:', props);
      const message: ConversationMessage = {
        role: props.source === 'user' ? 'user' : 'assistant',
        content: props.message
      };
      setMessages(prev => [...prev, message]);
    },
    onModeChange: (mode: { mode: 'speaking' | 'listening' }) => {
      console.log('🔄 Mode changed:', mode);
      setAgentStatus(mode.mode === 'speaking' ? 'speaking' : 'listening');
    },
    onError: (message: string, context?: any) => {
      console.error('❌ Conversation error:', message, context);
      setError(message);
    },
    // Client-side tools configuration
    clientTools: {
      show_business_framework: (parameters: any) => {
        console.log('🎯 Client Tool: Show Business Framework', parameters);
        setMessages(prev => [...prev, {
          role: 'system',
          content: `📊 Displaying: ${parameters.framework_name}\n${parameters.steps?.join('\n• ') || ''}`
        }]);
      },
      highlight_sources: (parameters: any) => {
        console.log('📚 Client Tool: Highlight Sources', parameters);
        setMessages(prev => [...prev, {
          role: 'system', 
          content: `📖 Referenced Sources:\n${parameters.documents?.join('\n• ') || ''}`
        }]);
      },
      display_persona_info: (parameters: any) => {
        console.log('🎭 Client Tool: Display Persona Info', parameters);
        setMessages(prev => [...prev, {
          role: 'system',
          content: `🎭 ${persona?.name || 'Persona'} Profile:\n• Expertise: ${parameters.expertise || 'Knowledge Base'}\n• Focus: ${parameters.focus || 'Helpful Responses'}`
        }]);
      },
      navigate_to_feature: (parameters: any) => {
        console.log('🧭 Client Tool: Navigate to Feature', parameters);
        setMessages(prev => [...prev, {
          role: 'system',
          content: `🔗 Navigate to: ${parameters.feature} (Demo - would redirect in full app)`
        }]);
      }
    }
  });

  const startConversation = useCallback(async () => {
    if (isConnecting || isConnected || !agentId) {
      console.log('⚠️ Cannot start: connecting/connected or no agent ID');
      return;
    }
    
    try {
      setIsConnecting(true);
      setError(null);
      
      console.log('🎤 Requesting microphone permission...');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      });
      
      console.log('✅ Microphone access granted');
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Use persona-specific agent ID
      const conversationId = await conversation.startSession({
        agentId: agentId
      });
      
      console.log('✅ Conversation started with persona agent:', agentId);
      
    } catch (error) {
      console.error('Failed to start conversation:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setError(`Failed to start conversation: ${errorMessage}`);
      
      if (errorMessage.includes('microphone') || errorMessage.includes('audio')) {
        setError('Microphone permission required. Please allow microphone access and try again.');
      } else if (errorMessage.includes('agent')) {
        setError('Agent configuration issue. Please check the agent setup.');
      }
    } finally {
      setIsConnecting(false);
    }
  }, [conversation, isConnecting, isConnected, agentId]);

  const stopConversation = useCallback(async () => {
    try {
      await conversation.endSession();
      setMessages([]);
    } catch (error) {
      console.error('Error stopping conversation:', error);
    }
  }, [conversation]);

  if (loadingAgent) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading voice agent...</p>
        </div>
      </div>
    );
  }

  if (!persona) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center text-red-600 text-4xl mx-auto mb-4">
            ⚠️
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Persona Not Found</h1>
          <p className="text-gray-600">The requested persona could not be found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          🎙️ Talk to {persona.name} - Voice AI
        </h1>
        
        {/* Persona Info */}
        <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">💼 {persona.name}</h2>
          <p className="text-gray-700 mb-3">
            {persona.description || `Speak directly with ${persona.name}'s AI clone using voice conversation.`}
          </p>
          <div className="flex flex-wrap gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">Voice Chat</span>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">Knowledge Base</span>
            <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">Real-time</span>
                         {(persona as any).chunk_count > 0 && (
               <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm">
                 {(persona as any).chunk_count} documents
               </span>
             )}
          </div>
        </div>
        
        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h3 className="text-red-800 font-medium mb-2">⚠️ Error</h3>
            <p className="text-red-700">{error}</p>
          </div>
        )}
        
        {/* Status Panel */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Connection Status</h2>
          <div className="flex items-center gap-4">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="font-medium">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
            {isConnected && (
              <span className="text-sm text-gray-600">
                Agent Status: {agentStatus}
              </span>
            )}
          </div>
          
          {agentId && (
            <p className="text-sm text-gray-600 mt-2">
              Agent ID: {agentId}
            </p>
          )}
        </div>
        
        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Voice Controls</h2>
          <div className="flex gap-3">
            <button
              onClick={startConversation}
              disabled={isConnecting || isConnected || !agentId}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                isConnecting || isConnected || !agentId
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              {isConnecting ? 'Connecting...' : '🎙️ Start Voice Chat'}
            </button>
            
            <button
              onClick={stopConversation}
              disabled={!isConnected}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                !isConnected
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-red-600 text-white hover:bg-red-700'
              }`}
            >
              📞 End Call
            </button>
          </div>
          
          {!agentId && (
            <p className="text-sm text-orange-600 mt-3">
              ⚠️ No voice agent configured for this persona. Create an agent in the Clones management page.
            </p>
          )}
        </div>

        {/* Messages Display */}
        {messages.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Conversation</h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-50 text-blue-900 ml-8'
                      : message.role === 'system'
                      ? 'bg-yellow-50 text-yellow-900'
                      : 'bg-gray-50 text-gray-900 mr-8'
                  }`}
                >
                  <div className="font-medium text-sm mb-1">
                    {message.role === 'user' ? '👤 You' : 
                     message.role === 'system' ? '⚙️ System' : 
                     `🤖 ${persona.name}`}
                  </div>
                  <div className="whitespace-pre-wrap">{message.content}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 