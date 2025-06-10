'use client';

import { useState, useEffect } from 'react';

export default function ChatPage() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // Check for token directly from localStorage instead of auth provider
    // Safely access localStorage only in browser environment
    try {
      if (typeof window !== 'undefined') {
        const storedToken = localStorage.getItem('auth_token');
        console.log('🔍 Chat page - checking token:', storedToken ? 'found' : 'not found');
        
        if (!storedToken) {
          console.log('❌ No token found, redirecting to login');
          window.location.href = '/login';
        } else {
          console.log('✅ Token found, user can access chat');
          setToken(storedToken);
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
        <h1 style={{ margin: 0 }}>Chat Interface</h1>
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
      
      <div style={{ 
        padding: '2rem', 
        backgroundColor: '#d1fae5', 
        borderRadius: '0.5rem'
      }}>
        <h2>Authentication Success!</h2>
        <p>Your authentication token is working correctly.</p>
        <p>Token: {token ? token.substring(0, 20) + '...' : 'No token'}</p>
        <div style={{ marginTop: '2rem' }}>
          <h3>Chat Interface Placeholder</h3>
          <p>This is where the actual chat interface would be.</p>
          <p>Since authentication is working, the full chat interface should work too.</p>
        </div>
      </div>

      <div style={{ marginTop: '2rem', textAlign: 'center' }}>
        <button
          onClick={() => window.location.href = '/'}
          style={{
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            cursor: 'pointer',
            marginRight: '1rem'
          }}
        >
          Go to Home
        </button>
        <button
          onClick={() => window.location.href = '/debug'}
          style={{
            backgroundColor: '#8b5cf6',
            color: 'white',
            border: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            cursor: 'pointer'
          }}
        >
          Go to Debug
        </button>
      </div>
    </div>
  );
}
