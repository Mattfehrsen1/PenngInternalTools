'use client';

import React from 'react';
import type { Conversation } from '@/lib/hooks/useConversations';

interface ThreadSidebarProps {
  conversations: Conversation[];
  currentThreadId: string | null;
  onThreadSelect: (threadId: string) => void;
  onNewChat: () => void;
  loading: boolean;
}

export default function ThreadSidebar({ 
  conversations, 
  currentThreadId, 
  onThreadSelect, 
  onNewChat, 
  loading 
}: ThreadSidebarProps) {
  
  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  const truncateTitle = (title: string, maxLength: number = 40) => {
    if (title.length <= maxLength) return title;
    return title.substring(0, maxLength) + '...';
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b">
        <button
          onClick={onNewChat}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2.5 font-medium transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {loading && conversations.length === 0 ? (
          <div className="p-4 space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="h-3 bg-gray-100 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <div className="text-2xl mb-2">💭</div>
            <p className="text-sm">No conversations yet</p>
            <p className="text-xs text-gray-400 mt-1">Start a new chat to begin</p>
          </div>
        ) : (
          <div className="py-2">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => onThreadSelect(conversation.id)}
                className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors border-l-2 ${
                  currentThreadId === conversation.id
                    ? 'bg-blue-50 border-l-blue-600'
                    : 'border-l-transparent'
                }`}
              >
                <div className="space-y-1">
                  {/* Title */}
                  <h3 className={`text-sm font-medium line-clamp-2 ${
                    currentThreadId === conversation.id
                      ? 'text-blue-900'
                      : 'text-gray-900'
                  }`}>
                    {truncateTitle(conversation.title)}
                  </h3>
                  
                  {/* Metadata */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{conversation.persona_name}</span>
                    <span>{conversation.message_count} msg{conversation.message_count !== 1 ? 's' : ''}</span>
                  </div>
                  
                  {/* Date */}
                  <div className="text-xs text-gray-400">
                    {conversation.last_message_at 
                      ? formatDate(new Date(conversation.last_message_at))
                      : formatDate(new Date(conversation.created_at))
                    }
                  </div>
                </div>
              </button>
            ))}
            
            {/* Load more indicator */}
            {loading && conversations.length > 0 && (
              <div className="p-4 text-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t bg-gray-50">
        <div className="text-xs text-gray-500 text-center">
          Chat • {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
} 