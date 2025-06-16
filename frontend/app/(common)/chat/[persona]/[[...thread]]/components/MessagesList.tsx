'use client';

import React, { useEffect, useRef, useState } from 'react';
import { usePersona } from '@/lib/contexts/PersonaContext';
import { useAudioStream } from '@/lib/hooks/useAudioStream';
import type { Message } from '../page';

interface MessagesListProps {
  messages: Message[];
}

export default function MessagesList({ messages }: MessagesListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { selectedPersona } = usePersona();
  const [token, setToken] = useState<string | null>(null);
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);
  
  const { state: audioState, error: audioError, playText, stop: stopAudio } = useAudioStream();

  // Initialize auth token
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    setToken(storedToken);
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle voice play/stop
  const handleVoicePlay = async (messageId: string, text: string) => {
    if (!selectedPersona || !token) {
      console.warn('[MessagesList] Missing persona or token for voice play');
      return;
    }

    try {
      // If this message is already playing, stop it
      if (playingMessageId === messageId && audioState === 'playing') {
        stopAudio();
        setPlayingMessageId(null);
        return;
      }

      // Stop any currently playing audio
      if (playingMessageId && audioState === 'playing') {
        stopAudio();
      }

      // Start playing this message
      setPlayingMessageId(messageId);
      console.log(`[MessagesList] Playing voice for message ${messageId}`);
      await playText(text, selectedPersona.id, token);
      
    } catch (error) {
      console.error('[MessagesList] Voice play failed:', error);
      setPlayingMessageId(null);
    }
  };

  // Reset playing message when audio stops
  useEffect(() => {
    if (audioState === 'idle' || audioState === 'error') {
      setPlayingMessageId(null);
    }
  }, [audioState]);

  // Voice button component
  const VoiceButton = ({ messageId, text, className = "" }: { 
    messageId: string; 
    text: string; 
    className?: string; 
  }) => {
    const isThisMessagePlaying = playingMessageId === messageId;
    const isLoading = isThisMessagePlaying && audioState === 'loading';
    const isPlaying = isThisMessagePlaying && audioState === 'playing';
    const isPaused = isThisMessagePlaying && audioState === 'paused';
    const hasError = isThisMessagePlaying && audioState === 'error';

    // Don't show button if no persona/token
    if (!selectedPersona || !token) {
      return null;
    }

    return (
      <button
        onClick={() => handleVoicePlay(messageId, text)}
        className={`inline-flex items-center justify-center w-6 h-6 rounded-full hover:bg-gray-100 transition-colors ${className}`}
        title={isPlaying ? "Stop voice" : hasError ? "Voice error - click to retry" : "Play voice"}
        disabled={isLoading}
      >
        {isLoading ? (
          // Loading spinner
          <svg className="w-4 h-4 animate-spin text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        ) : isPlaying ? (
          // Stop button (when playing)
          <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
          </svg>
        ) : hasError ? (
          // Error/retry button
          <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        ) : (
          // Play button (default)
          <svg className="w-4 h-4 text-gray-500 hover:text-blue-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        )}
      </button>
    );
  };

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-2">💬</div>
          <p className="text-lg font-medium mb-1">Start a conversation</p>
          <p className="text-sm">Ask a question to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* Audio error notification */}
      {audioError && playingMessageId && (
        <div className="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded-lg shadow-lg z-50">
          <p className="text-sm">Voice error: {audioError}</p>
        </div>
      )}

      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[85%] sm:max-w-md md:max-w-lg lg:max-w-xl rounded-2xl px-4 py-3 ${
              message.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-white border border-gray-200 text-gray-900 shadow-sm'
            }`}
          >
            {/* Message Content with Voice Button */}
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  {message.content}
                  
                  {/* Loading indicator for streaming messages */}
                  {message.status === 'sending' && message.role === 'assistant' && (
                    <span className="inline-flex items-center ml-2">
                      <div className="flex space-x-1">
                        <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </span>
                  )}
                </div>
                
                {/* Voice Button - Only for assistant messages with content */}
                {message.role === 'assistant' && message.content.trim() && message.status !== 'sending' && (
                  <div className="flex-shrink-0 mt-1">
                    <VoiceButton 
                      messageId={message.id} 
                      text={message.content}
                      className="ml-2" 
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Citations */}
            {message.citations && message.citations.length > 0 && (
              <div className="mt-3 pt-2 border-t border-gray-200">
                <details className="group">
                  <summary className="cursor-pointer text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
                    📚 {message.citations.length} source{message.citations.length !== 1 ? 's' : ''}
                    <svg 
                      className="w-3 h-3 transition-transform group-open:rotate-180" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <div className="mt-2 space-y-1">
                    {message.citations.map((citation, index) => (
                      <div key={index} className="text-xs text-gray-600 bg-gray-50 rounded px-2 py-1">
                        {citation}
                      </div>
                    ))}
                  </div>
                </details>
              </div>
            )}

            {/* Status indicator */}
            {message.status === 'error' && (
              <div className="mt-2 flex items-center gap-1 text-xs text-red-500">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                Failed to send
              </div>
            )}

            {/* Timestamp */}
            <div className={`text-xs mt-2 ${
              message.role === 'user' ? 'text-blue-100' : 'text-gray-400'
            }`}>
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </div>
      ))}
      
      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  );
} 