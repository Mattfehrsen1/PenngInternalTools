'use client';

import React, { useState, useCallback } from 'react';

// Types for ElevenLabs Conversational AI
interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ConversationMode {
  mode: 'speaking' | 'listening';
}

interface FunctionCall {
  name: string;
  parameters: Record<string, any>;
}

// Mock conversation hook for now - will be replaced with actual ElevenLabs SDK
const useConversation = (options: {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onMessage?: (message: ConversationMessage) => void;
  onModeChange?: (mode: ConversationMode) => void;
  onError?: (error: Error) => void;
}) => {
  const [isActive, setIsActive] = useState(false);

  const startSession = async (config: {
    agentId?: string;
    signedUrl?: string;
    onFunctionCall?: (functionCall: FunctionCall) => Promise<any>;
  }) => {
    console.log('Starting conversation with config:', config);
    setIsActive(true);
    options.onConnect?.();
    return 'mock-conversation-id';
  };

  const endSession = async () => {
    console.log('Ending conversation');
    setIsActive(false);
    options.onDisconnect?.();
  };

  return {
    startSession,
    endSession,
    isActive
  };
};

export default function TestConversationalAI() {
  const [isConnected, setIsConnected] = useState(false);
  const [agentStatus, setAgentStatus] = useState('listening');
  const [messages, setMessages] = useState<ConversationMessage[]>([]);

  const conversation = useConversation({
    onConnect: () => {
      console.log('🎙️ Connected to ElevenLabs Conversational AI');
      setIsConnected(true);
    },
    onDisconnect: () => {
      console.log('📞 Disconnected from ElevenLabs');
      setIsConnected(false);
      setAgentStatus('listening');
    },
    onMessage: (message: ConversationMessage) => {
      console.log('💬 Message received:', message);
      setMessages(prev => [...prev, message]);
    },
    onModeChange: (mode: ConversationMode) => {
      console.log('🔄 Mode changed:', mode);
      setAgentStatus(mode.mode === 'speaking' ? 'speaking' : 'listening');
    },
    onError: (error: Error) => {
      console.error('❌ Conversation error:', error);
    }
  });

  const startConversation = useCallback(async () => {
    try {
      // Request microphone permission first
      await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // For testing, we'll create a simple agent
      // In production, you'd get a signed URL from your backend
      const conversationId = await conversation.startSession({
        // Replace with your actual agent ID from ElevenLabs dashboard
        agentId: 'your-agent-id-here',
        
        // This is where we can integrate your RAG system
        onFunctionCall: async (functionCall: FunctionCall) => {
          console.log('🔧 Function call:', functionCall);
          
          if (functionCall.name === 'search_knowledge_base') {
            // Call your existing RAG system
            try {
              const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                },
                body: JSON.stringify({
                  message: functionCall.parameters.query,
                  persona_id: functionCall.parameters.persona_id,
                  use_rag: true
                })
              });
              
              const ragResult = await response.json();
              return {
                result: ragResult.response,
                citations: ragResult.citations
              };
            } catch (error) {
              console.error('RAG search failed:', error);
              return { error: 'Failed to search knowledge base' };
            }
          }
          
          return { error: 'Unknown function' };
        }
      });
      
      console.log('✅ Conversation started:', conversationId);
    } catch (error) {
      console.error('Failed to start conversation:', error);
      alert('Failed to start conversation. Check console for details.');
    }
  }, [conversation]);

  const stopConversation = useCallback(async () => {
    await conversation.endSession();
  }, [conversation]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          ElevenLabs Conversational AI Test
        </h1>
        
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
                Agent is {agentStatus}
              </span>
            )}
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Controls</h2>
          <div className="flex gap-4">
            <button
              onClick={startConversation}
              disabled={isConnected}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-blue-600"
            >
              Start Voice Conversation
            </button>
            <button
              onClick={stopConversation}
              disabled={!isConnected}
              className="px-6 py-3 bg-red-500 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-red-600"
            >
              Stop Conversation
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Conversation Log</h2>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {messages.length === 0 ? (
              <p className="text-gray-500 italic">No messages yet. Start a conversation to see the live transcript.</p>
            ) : (
              messages.map((message, index) => (
                <div key={index} className={`p-3 rounded-lg ${
                  message.role === 'user' 
                    ? 'bg-blue-50 border-l-4 border-blue-500' 
                    : 'bg-green-50 border-l-4 border-green-500'
                }`}>
                  <div className="font-medium text-sm mb-1">
                    {message.role === 'user' ? '🎤 You' : '🤖 Agent'}
                  </div>
                  <div className="text-gray-800">{message.content}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 rounded-lg p-6 mt-6">
          <h3 className="font-semibold text-blue-900 mb-2">Setup Instructions:</h3>
          <ol className="list-decimal list-inside text-blue-800 space-y-2">
            <li>Go to <a href="https://elevenlabs.io/conversational-ai" className="underline font-medium">ElevenLabs Conversational AI</a></li>
            <li>Sign up for an account (free tier available)</li>
            <li>Create a new agent in their dashboard</li>
            <li>Configure the agent with your persona prompt</li>
            <li>Add function calling for RAG integration</li>
            <li>Replace 'your-agent-id-here' with your actual agent ID</li>
            <li>Test the voice conversation!</li>
          </ol>
        </div>

        {/* RAG Integration Info */}
        <div className="bg-green-50 rounded-lg p-6 mt-6">
          <h3 className="font-semibold text-green-900 mb-2">✅ RAG Integration Confirmed:</h3>
          <ul className="list-disc list-inside text-green-800 space-y-1">
            <li><strong>Option 1:</strong> Use ElevenLabs built-in knowledge base (easiest)</li>
            <li><strong>Option 2:</strong> Function calling to your existing RAG system (shown above)</li>
            <li><strong>Option 3:</strong> Bring your own LLM server with RAG</li>
          </ul>
          <p className="text-green-700 mt-3 text-sm">
            The code above shows how to integrate with your existing Clone Advisor RAG system using function calling.
            When the agent needs knowledge, it calls your <code>/api/chat</code> endpoint with RAG enabled.
          </p>
        </div>
      </div>
    </div>
  );
} 