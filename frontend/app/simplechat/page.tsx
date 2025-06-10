'use client';

import { useState, useEffect } from 'react';

export default function SimpleChatPage() {
  const [token, setToken] = useState<string | null>(null);
  const [message, setMessage] = useState('Loading...');

  useEffect(() => {
    try {
      // Get token from localStorage
      const storedToken = localStorage.getItem('auth_token');
      setToken(storedToken);
      
      if (storedToken) {
        setMessage('Authentication successful! You can use the chat now.');
      } else {
        setMessage('No authentication token found. Please login first.');
      }
    } catch (error) {
      setMessage(`Error: ${error instanceof Error ? error.message : String(error)}`);
    }
  }, []);

  const handleLogout = () => {
    try {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    } catch (error) {
      setMessage(`Error logging out: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  return (
    <div style={{ 
      padding: '2rem', 
      maxWidth: '800px', 
      margin: '0 auto',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <header style={{ 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
        padding: '1rem',
        backgroundColor: '#f3f4f6',
        borderRadius: '0.5rem'
      }}>
        <h1 style={{ margin: 0 }}>Simple Chat Interface</h1>
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
      </header>
      
      {!token ? (
        <div style={{ 
          padding: '2rem', 
          backgroundColor: '#fee2e2', 
          borderRadius: '0.5rem',
          textAlign: 'center'
        }}>
          <p>{message}</p>
          <button
            onClick={() => window.location.href = '/login'}
            style={{
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              marginTop: '1rem'
            }}
          >
            Go to Login
          </button>
        </div>
      ) : (
        <div style={{ 
          padding: '2rem', 
          backgroundColor: '#d1fae5', 
          borderRadius: '0.5rem'
        }}>
          <h2>Authentication Success!</h2>
          <p>Your authentication token is working correctly.</p>
          <p>Token: {token.substring(0, 20)}...</p>
          <div style={{ marginTop: '2rem' }}>
            <h3>Chat Interface Placeholder</h3>
            <p>This is where the actual chat interface would be.</p>
            <p>Since authentication is working, the full chat interface should work too.</p>
          </div>
        </div>
      )}
    </div>
  );
}
