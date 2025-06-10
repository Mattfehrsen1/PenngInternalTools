'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function BasicChatPage() {
  const [token, setToken] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
  const router = useRouter();

  // Check authentication
  useEffect(() => {
    try {
      if (typeof window !== 'undefined') {
        const storedToken = localStorage.getItem('auth_token');
        console.log('🔍 BasicChat page - checking token:', storedToken ? 'found' : 'not found');
        
        if (!storedToken) {
          console.log('❌ No token found, redirecting to login');
          window.location.href = '/login';
        } else {
          console.log('✅ Token found, user can access chat');
          setToken(storedToken);
          
          // Add welcome message
          setMessages([
            { 
              role: 'assistant', 
              content: 'Welcome to the basic chat interface! This is a simplified version of the chat that works with your authentication.' 
            }
          ]);
        }
      }
    } catch (error) {
      console.error('Error accessing localStorage:', error);
      window.location.href = '/login';
    }
  }, []);

  const handleLogout = () => {
    try {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  const handleSendMessage = () => {
    if (!input.trim()) return;
    
    // Add user message
    const userMessage = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    
    // Clear input
    setInput('');
    
    // Add mock response (in a real app, this would call the API)
    setTimeout(() => {
      const assistantMessage = { 
        role: 'assistant', 
        content: `You said: "${input.trim()}". This is a mock response since we're just testing the chat interface.` 
      };
      setMessages(prev => [...prev, assistantMessage]);
    }, 500);
  };

  return (
    <div style={{ 
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      maxWidth: '1000px',
      margin: '0 auto',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <header style={{ 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1rem',
        backgroundColor: '#f3f4f6',
        borderBottom: '1px solid #e5e7eb'
      }}>
        <h1 style={{ margin: 0 }}>Basic Chat Interface</h1>
        <div>
          <button
            onClick={() => window.location.href = '/'}
            style={{
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              marginRight: '0.5rem'
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
      
      <div style={{ 
        flex: 1,
        padding: '1rem',
        overflowY: 'auto',
        backgroundColor: '#ffffff'
      }}>
        {messages.map((message, index) => (
          <div 
            key={index}
            style={{
              padding: '1rem',
              marginBottom: '1rem',
              borderRadius: '0.5rem',
              backgroundColor: message.role === 'user' ? '#e9f5ff' : '#f3f4f6',
              alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%',
              marginLeft: message.role === 'user' ? 'auto' : '0'
            }}
          >
            <p style={{ margin: 0 }}>{message.content}</p>
          </div>
        ))}
      </div>

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
          placeholder="Type a message..."
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
          disabled={!input.trim()}
          style={{
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            padding: '0.75rem 1.5rem',
            borderRadius: '0.25rem',
            cursor: input.trim() ? 'pointer' : 'not-allowed',
            opacity: input.trim() ? 1 : 0.7
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
