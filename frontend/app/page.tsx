'use client';

import { useState, useEffect } from 'react';

export default function Home() {
  const [hasToken, setHasToken] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for token on client side
    try {
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('auth_token');
        setHasToken(!!token);
      }
    } catch (error) {
      console.error('Error checking authentication:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#f3f4f6',
      fontFamily: 'sans-serif'
    }}>
      <div style={{
        background: 'white',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        textAlign: 'center',
        maxWidth: '400px'
      }}>
        <h1 style={{ margin: '0 0 1rem 0', fontSize: '2rem' }}>🤖 Clone Advisor</h1>
        <p style={{ margin: '0 0 1rem 0', color: '#6b7280' }}>MVP is running!</p>
        
        {loading ? (
          <p>Checking authentication status...</p>
        ) : (
          <>
            <div style={{
              padding: '0.75rem',
              borderRadius: '4px',
              backgroundColor: hasToken ? '#d1fae5' : '#fee2e2',
              marginBottom: '1rem'
            }}>
              <p style={{ margin: '0', fontSize: '0.875rem' }}>
                Authentication Status: {hasToken ? '✅ Logged In' : '❌ Not Logged In'}
              </p>
            </div>
            
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
              {!hasToken ? (
                <button 
                  onClick={() => window.location.href = '/login'}
                  style={{
                    background: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    padding: '0.5rem 1rem',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '1rem'
                  }}
                >
                  Go to Login
                </button>
              ) : (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button 
                    onClick={() => window.location.href = '/chat'}
                    style={{
                      background: '#10b981',
                      color: 'white',
                      border: 'none',
                      padding: '0.5rem 1rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '1rem'
                    }}
                  >
                    Go to Chat
                  </button>
                  <button 
                    onClick={() => window.location.href = '/basicchat'}
                    style={{
                      background: '#059669',
                      color: 'white',
                      border: 'none',
                      padding: '0.5rem 1rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '1rem'
                    }}
                  >
                    Go to Basic Chat
                  </button>
                  <button 
                    onClick={() => window.location.href = '/fullchat'}
                    style={{
                      background: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      padding: '0.5rem 1rem',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '1rem'
                    }}
                  >
                    Go to Full Chat (MVP)
                  </button>
                </div>
              )}
              
              <button 
                onClick={() => window.location.href = '/debug'}
                style={{
                  background: '#6366f1',
                  color: 'white',
                  border: 'none',
                  padding: '0.5rem 1rem',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '1rem'
                }}
              >
                Debug Tools
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
