'use client';

import { useState, useEffect } from 'react';

interface AgentStatusBadgeProps {
  personaId: string;
  className?: string;
}

export default function AgentStatusBadge({ personaId, className = '' }: AgentStatusBadgeProps) {
  const [status, setStatus] = useState<'loading' | 'active' | 'not_configured' | 'error'>('loading');

  useEffect(() => {
    const checkAgentStatus = async () => {
      try {
        const token = localStorage.getItem('auth_token') || localStorage.getItem('token');
        if (!token) {
          setStatus('error');
          return;
        }

        const response = await fetch(`/api/personas/${personaId}/agent/status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          setStatus(data.status === 'active' ? 'active' : 'not_configured');
        } else {
          setStatus('error');
        }
      } catch (err) {
        setStatus('error');
      }
    };

    checkAgentStatus();
  }, [personaId]);

  const getStatusConfig = () => {
    switch (status) {
      case 'loading':
        return { icon: '⏳', text: 'Checking', color: 'bg-gray-100 text-gray-600' };
      case 'active':
        return { icon: '🎙️', text: 'Voice Ready', color: 'bg-green-100 text-green-700' };
      case 'not_configured':
        return { icon: '⚠️', text: 'No Voice', color: 'bg-yellow-100 text-yellow-700' };
      case 'error':
        return { icon: '❌', text: 'Error', color: 'bg-red-100 text-red-700' };
      default:
        return { icon: '❓', text: 'Unknown', color: 'bg-gray-100 text-gray-600' };
    }
  };

  const config = getStatusConfig();

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.color} ${className}`}>
      <span className="mr-1">{config.icon}</span>
      {config.text}
    </span>
  );
} 