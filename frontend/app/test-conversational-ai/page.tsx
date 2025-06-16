'use client';

import React, { useState, useCallback } from 'react';
import { useConversation } from '@elevenlabs/react';

// Types for conversation state
interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function TestConversationalAI() {
  const [isConnected, setIsConnected] = useState(false);
  const [agentStatus, setAgentStatus] = useState('listening');
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

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
      
      // Log disconnect reason for debugging
      if (reason) {
        console.warn('Disconnect reason:', reason);
      }
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
    }
  });

  const startConversation = useCallback(async () => {
    // Prevent multiple connection attempts
    if (isConnecting || isConnected) {
      console.log('⚠️ Already connecting or connected, ignoring request');
      return;
    }
    
    try {
      setIsConnecting(true);
      setError(null);
      
      // Enhanced microphone permission with specific constraints
      console.log('🎤 Requesting microphone permission...');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      });
      
      // Test that we can actually access the microphone
      console.log('✅ Microphone access granted');
      
      // Give a small delay to ensure browser audio context is ready
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Start conversation with production agent
      const conversationId = await conversation.startSession({
        agentId: 'agent_01jxmeyxz2fh0v3cqx848qk1e0' 
      });
      
      console.log('✅ Conversation started with ID:', conversationId);
      
      // Note: Function calling will be configured in the ElevenLabs dashboard
      // The agent will call our webhook at https://clone-api.fly.dev/elevenlabs/function-call
      
    } catch (error) {
      console.error('Failed to start conversation:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setError(`Failed to start conversation: ${errorMessage}`);
      
      // Specific error handling for common issues
      if (errorMessage.includes('microphone') || errorMessage.includes('audio')) {
        setError('Microphone permission required. Please allow microphone access and try again.');
      } else if (errorMessage.includes('agent')) {
        setError('Agent configuration issue. Please check the agent ID.');
      }
    } finally {
      setIsConnecting(false);
    }
  }, [conversation, isConnecting, isConnected]);

  const stopConversation = useCallback(async () => {
    try {
      await conversation.endSession();
      setMessages([]); // Clear messages on disconnect
    } catch (error) {
      console.error('Error stopping conversation:', error);
    }
  }, [conversation]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          🎙️ Talk to Alex Hormozi - Voice AI
        </h1>
        
        {/* Alex Hormozi Persona Info */}
        <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">💼 Alex Hormozi Business Mentor</h2>
          <p className="text-gray-700 mb-3">
            Speak directly with Alex Hormozi's AI clone about getting rich, business strategy, and entrepreneurship. 
            This AI has been trained on Alex's business frameworks and teachings.
          </p>
          <div className="flex flex-wrap gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">Grand Slam Offers</span>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">Customer Acquisition</span>
            <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">Business Scaling</span>
            <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm">Pricing Strategy</span>
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
              disabled={isConnected || isConnecting}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
            >
              {isConnecting ? 'Connecting to Alex...' : isConnected ? 'Connected to Alex' : 'Start Talking to Alex'}
            </button>
            <button
              onClick={stopConversation}
              disabled={!isConnected}
              className="px-6 py-3 bg-red-500 text-white rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-red-600 transition-colors"
            >
              Stop Conversation
            </button>
          </div>
          
          {/* Instructions */}
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium text-blue-900 mb-2">📋 Instructions</h3>
            <ol className="text-sm text-blue-800 space-y-1">
              <li>1. Click "Start Talking to Alex" and allow microphone access</li>
              <li>2. Ask Alex about business strategy: "How do I create a grand slam offer?"</li>
              <li>3. Try questions about scaling: "What's the best way to acquire customers?"</li>
              <li>4. Speak naturally - Alex will respond with voice and business insights</li>
              <li>5. Alex has access to his business frameworks and teachings</li>
            </ol>
          </div>
        </div>

        {/* ElevenLabs Agent Configuration */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <h3 className="text-green-800 font-medium mb-2">✅ Agent Configuration</h3>
          <p className="text-green-700 mb-2">Alex Hormozi agent is configured with:</p>
          <div className="text-sm text-green-800 space-y-1">
            <p>• <strong>Agent ID:</strong> <code className="bg-green-100 px-1 py-0.5 rounded">agent_01jxmeyxz2fh0v3cqx848qk1e0</code></p>
            <p>• <strong>Webhook:</strong> <code className="bg-green-100 px-1 py-0.5 rounded">https://clone-api.fly.dev/elevenlabs/function-call</code></p>
            <p>• <strong>Persona ID:</strong> <code className="bg-green-100 px-1 py-0.5 rounded">3bb69586-e59b-43a6-a067-61730d7c0f3a</code></p>
            <p>• <strong>Knowledge Base:</strong> Business frameworks, scaling strategies, customer acquisition</p>
          </div>
          <p className="text-green-600 text-xs mt-2">
            ⚠️ Make sure your ElevenLabs agent uses persona_id "3bb69586-e59b-43a6-a067-61730d7c0f3a" in the webhook calls
          </p>
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

        {/* Technical Details */}
        <div className="mt-6 bg-gray-100 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-2">🔧 Technical Details</h3>
          <div className="text-sm text-gray-600 space-y-1">
            <p><strong>Backend:</strong> https://clone-api.fly.dev</p>
            <p><strong>Function Endpoint:</strong> /elevenlabs/function-call</p>
            <p><strong>RAG Integration:</strong> Active with Redis caching</p>
            <p><strong>Service Token:</strong> Configured ✅</p>
            <p><strong>Agent ID:</strong> {isConnected ? 'Connected' : 'Needs configuration'}</p>
          </div>
        </div>
      </div>
    </div>
  );
} 