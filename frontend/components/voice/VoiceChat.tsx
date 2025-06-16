'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Loader2 } from 'lucide-react';
import { useConversation } from '@elevenlabs/react';

interface VoiceChatProps {
  personaId: string;
  agentId: string;
  onTranscript?: (text: string, isUser: boolean) => void;
  onError?: (error: string) => void;
}

interface ConversationMessage {
  text: string;
  source: 'user' | 'agent';
  timestamp: Date;
}

export function VoiceChat({ personaId, agentId, onTranscript, onError }: VoiceChatProps) {
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isMuted, setIsMuted] = useState(false);
  const [isStarting, setIsStarting] = useState(false);

  const handleError = useCallback((errorMessage: string) => {
    console.error('[VoiceChat] Error:', errorMessage);
    setError(errorMessage);
    onError?.(errorMessage);
  }, [onError]);

  // Real ElevenLabs conversation hook
  const conversation = useConversation({
    onConnect: () => {
      console.log('[VoiceChat] Voice conversation connected');
      setError(null);
    },
    onDisconnect: () => {
      console.log('[VoiceChat] Voice conversation disconnected');
    },
    onMessage: (message: any) => {
      console.log('[VoiceChat] Message received:', message);
      
      // Based on the WebSocket docs, messages can be user transcripts or agent responses
      let messageText = '';
      let messageSource: 'user' | 'agent' = 'agent';
      
      if (message.type === 'user_transcript' && message.user_transcription_event) {
        messageText = message.user_transcription_event.user_transcript;
        messageSource = 'user';
      } else if (message.type === 'agent_response' && message.agent_response_event) {
        messageText = message.agent_response_event.agent_response;
        messageSource = 'agent';
      } else if (typeof message === 'string') {
        // Fallback for simple string messages
        messageText = message;
      }
      
      if (messageText) {
        const conversationMessage: ConversationMessage = {
          text: messageText,
          source: messageSource,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, conversationMessage]);
        onTranscript?.(messageText, messageSource === 'user');
      }
    },
    onError: (error: any) => {
      handleError(error?.message || error?.toString() || 'Voice conversation error');
    }
  });

  const handleStartConversation = async () => {
    if (isStarting || conversation.status === 'connected') {
      console.log('[VoiceChat] Already starting or connected, ignoring click');
      return;
    }

    try {
      setIsStarting(true);
      setError(null);

      // Validate inputs
      if (!personaId || !agentId) {
        throw new Error('Missing persona ID or agent ID');
      }

      console.log('[VoiceChat] Starting voice conversation with agent:', agentId);
      console.log('[VoiceChat] Passing persona_id for function calls:', personaId);
      
      // Pass persona_id via session data that can be accessed by function calls
      await conversation.startSession({ 
        agentId,
        // Use any available override to pass context
        clientData: {
          persona_id: personaId
        }
      } as any); // Type assertion to bypass strict typing for now

    } catch (error) {
      handleError(error instanceof Error ? error.message : 'Failed to start conversation');
    } finally {
      setIsStarting(false);
    }
  };

  const handleEndConversation = useCallback(async () => {
    console.log('[VoiceChat] Ending voice conversation');
    setError(null);
    setIsStarting(false);
    try {
      await conversation.endSession();
    } catch (error) {
      console.error('[VoiceChat] Error ending conversation:', error);
    }
  }, [conversation]);

  const handleToggleMute = useCallback(() => {
    setIsMuted(prev => {
      const newMuted = !prev;
      console.log('[VoiceChat] Mute toggled:', newMuted);
      
      // The useConversation hook doesn't expose a setMuted method
      // We'll track mute state locally and use setVolume instead
      if (newMuted) {
        conversation.setVolume({ volume: 0 });
      } else {
        conversation.setVolume({ volume: 1 });
      }
      
      return newMuted;
    });
  }, [conversation]);

  // Cleanup on unmount only
  useEffect(() => {
    return () => {
      console.log('[VoiceChat] Component unmounting, ending conversation');
      if (conversation.status === 'connected') {
        conversation.endSession();
      }
    };
  }, []); // Empty deps - only run on unmount

  return (
    <div className="voice-chat-container p-4 border rounded-lg bg-white shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {conversation.status === 'disconnected' && !isStarting ? (
            <button
              onClick={handleStartConversation}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              disabled={!agentId}
            >
              <Mic className="w-4 h-4" />
              Start Voice Chat
            </button>
          ) : (conversation.status === 'connecting' || isStarting) ? (
            <button
              disabled
              className="flex items-center gap-2 px-4 py-2 bg-gray-400 text-white rounded-lg cursor-not-allowed"
            >
              <Loader2 className="w-4 h-4 animate-spin" />
              Connecting...
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={handleEndConversation}
                className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
              >
                <MicOff className="w-4 h-4" />
                End Chat
              </button>
              <button
                onClick={handleToggleMute}
                className="p-2 border rounded-lg hover:bg-gray-100 transition-colors"
                title={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </button>
              {conversation.isSpeaking && (
                <div className="flex items-center gap-1 text-xs text-gray-600">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  Speaking
                </div>
              )}
            </div>
          )}
        </div>

        {!agentId && (
          <span className="text-sm text-amber-600 bg-amber-50 px-2 py-1 rounded">
            No agent configured
          </span>
        )}
      </div>

      {/* Connection Status */}
      {conversation.status === 'connected' && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-green-700">
              Voice chat active {isMuted && '(muted)'}
            </span>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-sm text-red-700">{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-600"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Message History */}
      {messages.length > 0 && (
        <div className="mt-4 p-3 bg-gray-50 border rounded-lg max-h-32 overflow-y-auto">
          <div className="text-sm text-gray-600 mb-2">Voice Transcript:</div>
          {messages.map((msg, idx) => (
            <div key={idx} className={`text-xs mb-1 ${msg.source === 'user' ? 'text-blue-600' : 'text-green-600'}`}>
              <span className="font-medium">{msg.source === 'user' ? 'You' : 'AI'}:</span> {msg.text}
            </div>
          ))}
        </div>
      )}

      {/* Instructions */}
      {conversation.status === 'disconnected' && !error && (
        <div className="mt-4 text-sm text-gray-600">
          <p>Click "Start Voice Chat" to begin speaking with {personaId || 'the AI'}.</p>
          <p className="text-xs text-gray-500 mt-1">
            Voice chat uses ElevenLabs Conversational AI with your persona's knowledge base.
          </p>
        </div>
      )}
    </div>
  );
} 