'use client';

import React from 'react';

interface TranscriptMessage {
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface TranscriptDisplayProps {
  messages: TranscriptMessage[];
  className?: string;
}

export function TranscriptDisplay({ messages, className = '' }: TranscriptDisplayProps) {
  if (messages.length === 0) {
    return (
      <div className={`transcript-display p-4 border rounded-lg bg-gray-50 ${className}`}>
        <p className="text-sm text-gray-500 text-center">
          Voice transcript will appear here...
        </p>
      </div>
    );
  }

  return (
    <div className={`transcript-display max-h-64 overflow-y-auto p-4 border rounded-lg bg-gray-50 ${className}`}>
      <div className="space-y-3">
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div className="max-w-xs lg:max-w-md">
              <div
                className={`inline-block p-3 rounded-lg ${
                  message.isUser 
                    ? 'bg-blue-500 text-white rounded-br-sm' 
                    : 'bg-white border border-gray-200 text-gray-900 rounded-bl-sm'
                }`}
              >
                <p className="text-sm">{message.text}</p>
              </div>
              <div className={`mt-1 text-xs text-gray-500 ${
                message.isUser ? 'text-right' : 'text-left'
              }`}>
                <span className="mr-2">
                  {message.isUser ? 'You' : 'AI'}
                </span>
                <span>
                  {message.timestamp.toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 