'use client';

import { useState, useEffect } from 'react';
import { API_URL } from '@/lib/api';
import UploadBox from '../../components/UploadBox';
import PersonaManager from '../../components/PersonaManager';
// MultiFileUpload component removed - now using dedicated /upload page

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
  timestamp: Date;
}

interface Persona {
  id: string;
  name: string;
  description?: string;
  chunks: number;
  created_at?: string;
  source_type?: string;
}

export default function FullChatPage() {
  const [token, setToken] = useState<string | null>(null);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showUpload, setShowUpload] = useState(true);
  const [showMultiUpload, setShowMultiUpload] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState('auto');

  // Check authentication
  useEffect(() => {
    try {
      if (typeof window !== 'undefined') {
        const storedToken = localStorage.getItem('auth_token');
        console.log('🔍 FullChat page - checking token:', storedToken ? 'found' : 'not found');
        console.log('🔍 FullChat page - token preview:', storedToken ? storedToken.substring(0, 20) + '...' : 'none');
        
        if (!storedToken) {
          console.log('❌ No token found, redirecting to login');
          window.location.href = '/login';
        } else {
          console.log('✅ Token found, user can access chat');
          setToken(storedToken);
          loadPersonas(storedToken);
        }
      }
    } catch (error) {
      console.error('Error accessing localStorage:', error);
      window.location.href = '/login';
    }
  }, []);

  const loadPersonas = async (authToken: string) => {
    try {
      console.log('📋 Loading personas with token:', authToken ? authToken.substring(0, 20) + '...' : 'none');
      
      const response = await fetch(`${API_URL}/personas/list`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      console.log('📋 Personas response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('📋 Personas loaded:', data.personas?.length || 0);
        
        // Map the backend data to include all needed fields
        const mappedPersonas = (data.personas || []).map((p: any) => ({
          id: p.id,
          name: p.name,
          description: p.description,
          chunks: p.chunk_count || 0,
          created_at: p.created_at,
          source_type: p.source_type,
        }));
        
        setPersonas(mappedPersonas);
        if (mappedPersonas.length > 0) {
          setShowUpload(false);
        }
      } else {
        const errorText = await response.text();
        console.error('❌ Failed to load personas:', response.status, errorText);
      }
    } catch (error) {
      console.error('Error loading personas:', error);
    }
  };

  const handleUploadSuccess = (personaId: string, personaName: string, chunks: number) => {
    const newPersona: Persona = {
      id: personaId,
      name: personaName,
      chunks: chunks
    };
    
    setPersonas(prev => [...prev, newPersona]);
    setSelectedPersona(newPersona);
    setShowUpload(false);
    setError(null);
    
    // Add welcome message
    const welcomeMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `Great! I've created your "${personaName}" persona with ${chunks} knowledge chunks. I'm ready to answer questions based on this content. What would you like to know?`,
      timestamp: new Date()
    };
    setMessages([welcomeMessage]);
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !selectedPersona || isLoading) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      // Create assistant message placeholder
      let assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        citations: [],
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Send request to chat endpoint
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          persona_id: selectedPersona.id,
          question: userMessage.content,
          model: selectedModel,
          k: 6
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.status}`);
      }

      // Process SSE stream with simplified logic
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body reader could not be created');
      }
      
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = '';
      
      // Process the stream
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer
        
        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) continue;
          
          if (trimmedLine.startsWith('event: ')) {
            currentEvent = trimmedLine.slice(7).trim();
          } else if (trimmedLine.startsWith('data: ')) {
            const dataStr = trimmedLine.slice(6).trim();
            
            try {
              const data = JSON.parse(dataStr);
              
              console.log(`Received ${currentEvent} event:`, data);
              
              if (currentEvent === 'citations') {
                // Backend sends citations as an array directly
                assistantMessage.citations = data.map((citation: any, index: number) => 
                  `[${index + 1}] ${citation.source}`
                );
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessage.id ? { ...assistantMessage } : msg
                ));
              } else if (currentEvent === 'token') {
                if (data.token) {
                  assistantMessage.content += data.token;
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantMessage.id ? { ...assistantMessage } : msg
                  ));
                }
              } else if (currentEvent === 'done') {
                console.log('Chat completed with', data.tokens || 'unknown', 'tokens');
              } else if (currentEvent === 'error') {
                setError(data.error || 'An error occurred');
                setMessages(prev => prev.filter(msg => msg.id !== assistantMessage.id));
                return;
              }
              
              // Reset event after processing
              currentEvent = '';
            } catch (e) {
              console.error('Error parsing SSE data:', dataStr, e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
      // Remove the assistant message placeholder if there was an error
      setMessages(prev => prev.filter(msg => msg.role !== 'assistant' || msg.content.trim() !== ''));
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    try {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  const selectPersona = (persona: Persona) => {
    setSelectedPersona(persona);
    setMessages([]);
    setError(null);
  };

  const handlePersonaUpdate = (updatedPersona: Persona) => {
    setPersonas(prev => prev.map(p => 
      p.id === updatedPersona.id ? updatedPersona : p
    ));
    
    // Update selected persona if it was the one being edited
    if (selectedPersona?.id === updatedPersona.id) {
      setSelectedPersona(updatedPersona);
    }
  };

  const handlePersonaDelete = (personaId: string) => {
    setPersonas(prev => prev.filter(p => p.id !== personaId));
    
    // Clear selection if the deleted persona was selected
    if (selectedPersona?.id === personaId) {
      setSelectedPersona(null);
      setMessages([]);
    }
    
    // Show upload if no personas left
    if (personas.length === 1) {
      setShowUpload(true);
    }
  };

  const handleShowMultiUpload = (personaId: string) => {
    setShowMultiUpload(personaId);
    setShowUpload(false);
  };

  const handleMultiUploadComplete = (totalChunks: number) => {
    // Reload personas to get updated chunk counts
    if (token) {
      loadPersonas(token);
    }
    setShowMultiUpload(null);
    setError(null);
  };

  const handleMultiUploadError = (errorMessage: string) => {
    setError(errorMessage);
  };

  return (
    <div style={{ 
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      fontFamily: 'system-ui, sans-serif'
    }}>
      {/* Header */}
      <header style={{ 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1rem',
        backgroundColor: '#f3f4f6',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <h1 style={{ margin: 0 }}>Clone Advisor MVP</h1>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {!showUpload && personas.length > 0 && (
            <button
              onClick={() => setShowUpload(true)}
              style={{
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '0.25rem',
                cursor: 'pointer'
              }}
            >
              Upload New
            </button>
          )}
          <button
            onClick={() => window.location.href = '/upload'}
            style={{
              backgroundColor: '#f59e0b',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              cursor: 'pointer'
            }}
          >
            Bulk Upload
          </button>
          <button
            onClick={() => window.location.href = '/'}
            style={{
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              cursor: 'pointer'
            }}
          >
            Home
          </button>
          <button
            onClick={handleLogout}
            style={{
              backgroundColor: '#ef4444',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        </div>
      </header>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Enhanced Persona Manager */}
        {personas.length > 0 && !showUpload && !showMultiUpload && (
          <PersonaManager
            personas={personas}
            selectedPersona={selectedPersona}
            onPersonaSelect={selectPersona}
            onPersonaUpdate={handlePersonaUpdate}
            onPersonaDelete={handlePersonaDelete}
            onShowUpload={() => setShowUpload(true)}
            onShowMultiUpload={handleShowMultiUpload}
            token={token || ''}
          />
        )}

        {/* Main content area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {showUpload ? (
            <div style={{ flex: 1, overflow: 'auto', padding: '2rem' }}>
              <UploadBox 
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
                token={token || undefined}
              />
              {error && (
                <div style={{
                  backgroundColor: '#fef2f2',
                  border: '1px solid #fecaca',
                  color: '#dc2626',
                  padding: '1rem',
                  borderRadius: '0.25rem',
                  marginTop: '1rem',
                  maxWidth: '600px',
                  margin: '1rem auto 0 auto'
                }}>
                  {error}
                </div>
              )}
            </div>
          ) : showMultiUpload ? (
            <div style={{ flex: 1, overflow: 'auto', padding: '2rem' }}>
              <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
                <div style={{ marginBottom: '2rem' }}>
                  <button
                    onClick={() => setShowMultiUpload(null)}
                    style={{
                      backgroundColor: 'transparent',
                      border: 'none',
                      fontSize: '1.5rem',
                      cursor: 'pointer',
                      marginRight: '1rem',
                      color: '#6b7280',
                      float: 'left'
                    }}
                  >
                    ←
                  </button>
                  <h2 style={{ margin: 0, fontSize: '1.5rem' }}>
                    Add Files to {personas.find(p => p.id === showMultiUpload)?.name}
                  </h2>
                </div>
                
                <div style={{ 
                  backgroundColor: '#f0f9ff', 
                  border: '2px dashed #3b82f6', 
                  borderRadius: '0.5rem', 
                  padding: '3rem 2rem',
                  marginBottom: '2rem'
                }}>
                  <svg style={{ width: '4rem', height: '4rem', margin: '0 auto 1rem auto', color: '#3b82f6' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <h3 style={{ margin: '0 0 1rem 0', color: '#1f2937' }}>Use the New Bulletproof Upload System</h3>
                  <p style={{ margin: '0 0 2rem 0', color: '#6b7280' }}>
                    We've built a much better upload experience with progress tracking, retry mechanisms, and support for larger files.
                  </p>
                  <button
                    onClick={() => window.location.href = '/upload'}
                    style={{
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      padding: '1rem 2rem',
                      borderRadius: '0.5rem',
                      cursor: 'pointer',
                      fontSize: '1rem',
                      fontWeight: 'bold'
                    }}
                  >
                    Go to Upload Page →
                  </button>
                </div>
                
                {error && (
                  <div style={{
                    backgroundColor: '#fef2f2',
                    border: '1px solid #fecaca',
                    color: '#dc2626',
                    padding: '1rem',
                    borderRadius: '0.25rem',
                    marginTop: '1rem',
                  }}>
                    {error}
                  </div>
                )}
              </div>
            </div>
          ) : selectedPersona ? (
            <>
              {/* Chat header */}
              <div style={{ 
                padding: '1rem',
                borderBottom: '1px solid #e5e7eb',
                backgroundColor: '#ffffff',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Chat with {selectedPersona.name}</h2>
                  <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
                    {selectedPersona.chunks} knowledge chunks available
                  </p>
                </div>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  style={{
                    padding: '0.5rem',
                    borderRadius: '0.25rem',
                    border: '1px solid #d1d5db'
                  }}
                >
                  <option value="auto">Auto</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="claude-3-opus">Claude-3 Opus</option>
                </select>
              </div>

              {/* Messages */}
              <div style={{ 
                flex: 1,
                padding: '1rem',
                overflowY: 'auto',
                backgroundColor: '#ffffff'
              }}>
                {messages.map((message) => (
                  <div 
                    key={message.id}
                    style={{
                      padding: '1rem',
                      marginBottom: '1rem',
                      borderRadius: '0.5rem',
                      backgroundColor: message.role === 'user' ? '#dbeafe' : '#f3f4f6',
                      marginLeft: message.role === 'user' ? '20%' : '0',
                      marginRight: message.role === 'user' ? '0' : '20%'
                    }}
                  >
                    <div style={{ 
                      fontSize: '0.875rem', 
                      color: '#6b7280',
                      marginBottom: '0.5rem'
                    }}>
                      {message.role === 'user' ? 'You' : selectedPersona.name}
                    </div>
                    <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
                    {message.citations && message.citations.length > 0 && (
                      <div style={{ 
                        marginTop: '0.5rem',
                        fontSize: '0.75rem',
                        color: '#6b7280'
                      }}>
                        Sources: {message.citations.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
                {isLoading && (
                  <div style={{
                    padding: '1rem',
                    marginBottom: '1rem',
                    borderRadius: '0.5rem',
                    backgroundColor: '#f3f4f6',
                    marginRight: '20%',
                    fontStyle: 'italic',
                    color: '#6b7280'
                  }}>
                    {selectedPersona.name} is thinking...
                  </div>
                )}
              </div>

              {/* Input area */}
              <div style={{ 
                padding: '1rem',
                borderTop: '1px solid #e5e7eb',
                backgroundColor: '#f9fafb',
                display: 'flex'
              }}>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder={`Ask ${selectedPersona.name} anything...`}
                  disabled={isLoading}
                  style={{
                    flex: 1,
                    padding: '0.75rem',
                    borderRadius: '0.25rem',
                    border: '1px solid #d1d5db',
                    marginRight: '0.5rem'
                  }}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!input.trim() || isLoading}
                  style={{
                    backgroundColor: '#10b981',
                    color: 'white',
                    border: 'none',
                    padding: '0.75rem 1.5rem',
                    borderRadius: '0.25rem',
                    cursor: !input.trim() || isLoading ? 'not-allowed' : 'pointer',
                    opacity: !input.trim() || isLoading ? 0.7 : 1
                  }}
                >
                  Send
                </button>
              </div>
            </>
          ) : (
            <div style={{ 
              flex: 1, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              color: '#6b7280'
            }}>
              <div style={{ textAlign: 'center' }}>
                <h2>Welcome to Clone Advisor!</h2>
                <p>Upload a document or select a persona to start chatting.</p>
                <button
                  onClick={() => setShowUpload(true)}
                  style={{
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    padding: '1rem 2rem',
                    borderRadius: '0.25rem',
                    cursor: 'pointer',
                    fontSize: '1rem'
                  }}
                >
                  Upload Your First Document
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {error && !showUpload && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          color: '#dc2626',
          padding: '1rem',
          margin: '1rem',
          borderRadius: '0.25rem'
        }}>
          {error}
        </div>
      )}
    </div>
  );
}
