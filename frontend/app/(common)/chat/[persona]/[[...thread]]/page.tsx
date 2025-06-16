'use client';

import React, { useState, useEffect, useCallback, Component, ReactNode } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Mic } from 'lucide-react';
import { usePersona } from '@/lib/contexts/PersonaContext';
import { useConversations } from '@/lib/hooks/useConversations';
import { useVoiceContext } from '@/lib/contexts/VoiceContext';
import { usePersonaAgent } from '@/lib/hooks/usePersonaAgent';
import { VoiceChat } from '@/components/voice/VoiceChat';
import { TranscriptDisplay } from '@/components/voice/TranscriptDisplay';
import MessagesList from './components/MessagesList';
import MessageInput from './components/MessageInput';
import ThreadSidebar from './components/ThreadSidebar';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error';
}

// Proper React Error Boundary
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<{ children: ReactNode; fallback?: ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode; fallback?: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex items-center justify-center h-screen p-4">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
            <p className="text-gray-600 mb-4">Please refresh the page to continue</p>
            <button 
              onClick={() => { 
                this.setState({ hasError: false });
                window.location.reload(); 
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default function ChatV2() {
  const params = useParams();
  const router = useRouter();
  const personaSlug = params.persona as string;
  const threadId = params.thread?.[0] as string | undefined;
  
  const { selectedPersona, personas, loading: personaLoading } = usePersona();
  const { isVoiceEnabled } = useVoiceContext();
  const { agentId, loading: agentLoading, error: agentError } = usePersonaAgent(selectedPersona?.id || null);
  const [token, setToken] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(threadId || null);
  
  // Voice chat state
  const [showVoiceChat, setShowVoiceChat] = useState(false);
  const [transcriptMessages, setTranscriptMessages] = useState<Array<{
    text: string;
    isUser: boolean;
    timestamp: Date;
  }>>([]);

  const { conversations, loading: conversationsLoading, loadConversationById, refreshConversations } = useConversations(token);

  // Debug usePersonaAgent results
  useEffect(() => {
    console.log('[ChatV2] usePersonaAgent state:', {
      agentId,
      agentLoading,
      agentError,
      personaId: selectedPersona?.id,
      personaName: selectedPersona?.name
    });
  }, [agentId, agentLoading, agentError, selectedPersona?.id, selectedPersona?.name]);

  // Initialize auth token
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    if (!storedToken) {
      router.push('/login');
      return;
    }
    setToken(storedToken);
  }, [router]);

  // Find persona by slug or redirect
  useEffect(() => {
    if (personaLoading || !personas.length) return;
    
    const persona = personas.find(p => p.slug === personaSlug || p.id === personaSlug);
    if (!persona) {
      router.push('/clones');
      return;
    }
  }, [personaSlug, personas, personaLoading, router]);

  // Load conversation if threadId exists
  useEffect(() => {
    if (!token || !threadId || !selectedPersona) return;
    
    loadConversationById(threadId).then(data => {
      if (data) {
        const formattedMessages = data.messages.map(msg => ({
          id: msg.id,
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          citations: msg.citations?.map((citation: any) => 
            typeof citation === 'string' ? citation : citation.source || 'Unknown source'
          ) || [],
          timestamp: new Date(msg.created_at),
          status: 'sent' as const
        }));
        
        setMessages(formattedMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime()));
        setCurrentThreadId(threadId);
      }
    }).catch(err => {
      console.error('Failed to load conversation:', err);
      setError('Failed to load conversation');
    });
  }, [token, threadId, selectedPersona, loadConversationById]);

  // Handle sending messages with optimistic UI
  const handleSendMessage = useCallback(async (content: string) => {
    if (!selectedPersona || !token || isStreaming) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      status: 'sent'
    };

    // Optimistic UI - add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setIsStreaming(true);
    setError(null);

    // Prepare assistant message placeholder
    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      citations: [],
      timestamp: new Date(),
      status: 'sending'
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      // Send to chat API with SSE
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          persona_id: selectedPersona.id,
          question: content,
          model: 'gpt-4o',
          k: 3,
          thread_id: currentThreadId || undefined
        }),
      });

      if (!response.ok) {
        throw new Error(`Chat API error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      let accumulatedContent = '';
      let receivedCitations: string[] = [];
      let newThreadId: string | null = null;

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = new TextDecoder().decode(value);
          const lines = chunk.split('\n').filter(line => line.trim());
          
          // Debug logging
          console.log('[ChatV2] SSE chunk received:', lines);

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              // Track current event type
              const eventType = line.slice(7).trim();
              continue;
            }
            
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                // Handle different event types based on data content
                if (data.thread_id && !currentThreadId) {
                  // thread_info event
                  console.log('[ChatV2] Thread info received:', data);
                  newThreadId = data.thread_id;
                  setCurrentThreadId(newThreadId);
                } else if (data.token) {
                  // token event
                  console.log('[ChatV2] Token received:', data.token);
                  accumulatedContent += data.token;
                  // Update message in real-time
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { ...msg, content: accumulatedContent, status: 'sending' }
                      : msg
                  ));
                } else if (Array.isArray(data) && data.length > 0 && data[0].id) {
                  // citations event
                  console.log('[ChatV2] Citations received:', data);
                  receivedCitations = data.map(citation => 
                    `[${citation.id}] ${citation.source || 'Unknown source'}`
                  );
                } else if (data.status === 'complete') {
                  // done event
                  console.log('[ChatV2] Stream complete');
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessageId 
                      ? { ...msg, citations: receivedCitations, status: 'sent' }
                      : msg
                  ));
                  break;
                } else if (data.error) {
                  // error event
                  console.log('[ChatV2] Error received:', data.error);
                  throw new Error(data.error);
                } else {
                  console.log('[ChatV2] Unknown SSE data:', data);
                }
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', line, parseError);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      // Update URL if we got a new thread ID
      if (newThreadId && !currentThreadId) {
        const newUrl = `/chat/${personaSlug}/${newThreadId}`;
        window.history.replaceState(null, '', newUrl);
      }

      // Refresh conversations list
      refreshConversations();

    } catch (error) {
      console.error('Chat error:', error);
      setError('Failed to send message. Please try again.');
      
      // Mark assistant message as error
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessageId 
          ? { ...msg, content: 'Sorry, I encountered an error. Please try again.', status: 'error' }
          : msg
      ));
    } finally {
      setIsStreaming(false);
    }
  }, [selectedPersona, token, isStreaming, currentThreadId, personaSlug, refreshConversations]);

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setCurrentThreadId(null);
    setError(null);
    router.push(`/chat/${personaSlug}`);
  }, [personaSlug, router]);

  const handleThreadSelect = useCallback((threadId: string) => {
    router.push(`/chat/${personaSlug}/${threadId}`);
    setSidebarOpen(false);
  }, [personaSlug, router]);

  if (personaLoading || !token) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!selectedPersona) {
    return (
      <div className="flex items-center justify-center h-screen p-4">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Persona not found</h2>
          <button 
            onClick={() => router.push('/clones')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Go to Clones
          </button>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary fallback={<div>Chat error occurred</div>}>
      <div className="h-screen flex bg-gray-50">
        {/* Thread Sidebar - Desktop */}
        <div className="hidden md:block w-80 border-r bg-white">
          <ThreadSidebar
            conversations={conversations}
            currentThreadId={currentThreadId}
            onThreadSelect={handleThreadSelect}
            onNewChat={handleNewChat}
            loading={conversationsLoading}
          />
        </div>

        {/* Mobile Sidebar Overlay */}
        {sidebarOpen && (
          <div className="md:hidden fixed inset-0 z-50 bg-black bg-opacity-50" onClick={() => setSidebarOpen(false)}>
            <div className="w-80 h-full bg-white" onClick={e => e.stopPropagation()}>
              <ThreadSidebar
                conversations={conversations}
                currentThreadId={currentThreadId}
                onThreadSelect={handleThreadSelect}
                onNewChat={handleNewChat}
                loading={conversationsLoading}
              />
            </div>
          </div>
        )}

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <div className="border-b bg-white px-4 py-3 flex items-center justify-between sticky top-0 z-10">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="md:hidden p-2 -ml-2 hover:bg-gray-100 rounded-lg"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <div>
                <h1 className="font-semibold text-gray-900">{selectedPersona.name}</h1>
                <p className="text-sm text-gray-500">{selectedPersona.description}</p>
              </div>
            </div>

                                  {/* Voice Chat Toggle */}
            {isVoiceEnabled && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    console.log('[ChatV2] Voice Chat button clicked!');
                    console.log('[ChatV2] Current agentId:', agentId);
                    console.log('[ChatV2] Selected persona ID:', selectedPersona?.id);
                    console.log('[ChatV2] ShowVoiceChat before toggle:', showVoiceChat);
                    setShowVoiceChat(!showVoiceChat);
                  }}
                  className={`flex items-center gap-2 px-3 py-2 border rounded-lg transition-colors ${
                    showVoiceChat 
                      ? 'bg-blue-50 border-blue-200 text-blue-700' 
                      : 'hover:bg-gray-100'
                  }`}
                  disabled={agentLoading || !agentId}
                  title={agentLoading ? 'Loading agent...' : !agentId ? 'Voice chat requires agent configuration' : 'Toggle voice chat'}
                >
                  <Mic className="w-4 h-4" />
                  <span className="hidden sm:inline">
                    {showVoiceChat ? 'Hide Voice' : 'Voice Chat'}
                  </span>
                </button>
                
                {/* Debug indicator */}
                <div className="text-xs text-gray-500">
                  {agentLoading ? 'Loading...' : agentId ? '✓' : '✗'}
                </div>
              </div>
            )}
          </div>

          {/* Error Banner */}
          {error && (
            <div className="bg-red-50 border-b border-red-200 px-4 py-2">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Voice Chat Section */}
          {showVoiceChat && isVoiceEnabled && (
            <div className="border-b bg-gray-50 p-4 space-y-4">
              <VoiceChat
                personaId={selectedPersona?.id || ''}
                agentId={agentId || ''}
                onTranscript={(text, isUser) => {
                  console.log('[ChatV2] Voice transcript received:', { text, isUser });
                  setTranscriptMessages(prev => [...prev, {
                    text,
                    isUser,
                    timestamp: new Date()
                  }]);
                }}
                onError={(error) => {
                  console.error('[ChatV2] Voice chat error:', error);
                  setError(`Voice chat error: ${error}`);
                }}
              />
              
              {transcriptMessages.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium mb-2 text-gray-700">Voice Transcript</h3>
                  <TranscriptDisplay messages={transcriptMessages} />
                </div>
              )}
            </div>
          )}

          {/* Messages */}
          <MessagesList messages={messages} />

          {/* Input */}
          <MessageInput 
            onSendMessage={handleSendMessage}
            disabled={isStreaming}
            placeholder={`Message ${selectedPersona.name}...`}
          />
        </div>
      </div>
    </ErrorBoundary>
  );
} 