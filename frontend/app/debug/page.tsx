'use client';

import { useState, useEffect } from 'react';

export default function DebugPage() {
  const [token, setToken] = useState<string | null>(null);
  const [message, setMessage] = useState('Checking token...');

  useEffect(() => {
    try {
      // Get token from localStorage
      const storedToken = localStorage.getItem('auth_token');
      setToken(storedToken);
      
      if (storedToken) {
        setMessage('Token found! Authentication should work.');
      } else {
        setMessage('No token found. You need to login first.');
      }
    } catch (error) {
      setMessage(`Error: ${error instanceof Error ? error.message : String(error)}`);
    }
  }, []);

  const handleLogin = () => {
    window.location.href = '/login';
  };

  const handleSetToken = () => {
    try {
      localStorage.setItem('auth_token', 'test_token_' + Date.now());
      setToken(localStorage.getItem('auth_token'));
      setMessage('Test token set successfully!');
    } catch (error) {
      setMessage(`Error setting token: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const handleClearToken = () => {
    try {
      localStorage.removeItem('auth_token');
      setToken(null);
      setMessage('Token cleared successfully!');
    } catch (error) {
      setMessage(`Error clearing token: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const handleGoToChat = () => {
    window.location.href = '/chat';
  };

  return (
    <div style={{ 
      padding: '2rem', 
      maxWidth: '600px', 
      margin: '0 auto',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <h1 style={{ marginBottom: '1rem' }}>Authentication Debug Page</h1>
      
      <div style={{ 
        padding: '1rem', 
        border: '1px solid #ccc', 
        borderRadius: '8px',
        marginBottom: '1rem',
        backgroundColor: token ? '#d1fae5' : '#fee2e2'
      }}>
        <h2>Token Status</h2>
        <p><strong>Message:</strong> {message}</p>
        <p><strong>Token:</strong> {token ? `${token.substring(0, 20)}...` : 'No token'}</p>
      </div>
      
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button 
          onClick={handleLogin}
          style={{
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            cursor: 'pointer'
          }}
        >
          Go to Login
        </button>
        <button 
          onClick={handleSetToken}
          style={{
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            cursor: 'pointer'
          }}
        >
          Set Test Token
        </button>
        <button 
          onClick={handleClearToken}
          style={{
            backgroundColor: '#ef4444',
            color: 'white',
            border: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            cursor: 'pointer'
          }}
        >
          Clear Token
        </button>
      </div>
      
      <div style={{ marginBottom: '1rem' }}>
        <button 
          onClick={handleGoToChat}
          style={{
            backgroundColor: '#8b5cf6',
            color: 'white',
            border: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            cursor: 'pointer',
            width: '100%'
          }}
        >
          Go to Chat Page (with current token)
        </button>
      </div>
      
      <div style={{ 
        padding: '1rem', 
        border: '1px solid #ccc', 
        borderRadius: '8px',
        backgroundColor: '#f3f4f6'
      }}>
        <h3>Debugging Instructions</h3>
        <ol style={{ paddingLeft: '1.5rem' }}>
          <li>Click "Set Test Token" to manually set a test token</li>
          <li>Then click "Go to Chat Page" to test if the chat page accepts the token</li>
          <li>If you're redirected back to login, there's an issue with the chat page</li>
          <li>If you see the chat interface, authentication is working</li>
        </ol>
      </div>
    </div>
  );
}
