'use client';

import { useEffect, useState } from 'react';

export function TestButton() {
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    // Check for token on client side
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      setHasToken(!!token);
      console.log('🔍 Test button - token found:', !!token);
    }
  }, []);

  const handleChatClick = () => {
    console.log('🚀 Navigating to chat page');
    window.location.href = '/chat';
  };

  return (
    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
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
        Back to Login
      </button>
      <button 
        onClick={handleChatClick}
        style={{
          background: '#16a34a',
          color: 'white',
          border: 'none',
          padding: '0.5rem 1rem',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '1rem'
        }}
      >
        Try Chat {hasToken ? '(Token Found)' : '(No Token)'}
      </button>
    </div>
  );
}
