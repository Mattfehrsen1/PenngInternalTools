'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { usePersona } from '@/lib/contexts/PersonaContext';

export default function ChatV2Demo() {
  const router = useRouter();
  const { selectedPersona, personas } = usePersona();

  const features = [
    {
      icon: '⚡',
      title: 'Optimistic UI',
      description: 'Messages appear instantly while sending in background'
    },
    {
      icon: '📱',
      title: 'Mobile-First',
      description: 'Perfect responsive design on all screen sizes'
    },
    {
      icon: '🔄',
      title: 'Clean SSE Streaming',
      description: 'Simple, reliable real-time message streaming'
    },
    {
      icon: '🛡️',
      title: 'Error Recovery',
      description: 'Graceful handling of all failure cases'
    },
    {
      icon: '🧹',
      title: 'Memory Management',
      description: 'Proper cleanup of intervals and listeners'
    },
    {
      icon: '🎯',
      title: 'Simple Codebase',
      description: '<200 lines per component, easy to understand'
    }
  ];

  const handleTryNow = () => {
    if (selectedPersona) {
      router.push(`/chat/${selectedPersona.slug}`);
    } else if (personas.length > 0) {
      router.push(`/chat/${personas[0].slug}`);
    } else {
      router.push('/clones');
    }
  };

  const handleCompareSideBySide = () => {
    // Open both in new tabs for comparison
    if (selectedPersona) {
      window.open(`/chat/${selectedPersona.slug}`, '_blank');
      window.open(`/chat/${selectedPersona.slug}`, '_blank');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block p-3 bg-blue-600 text-white rounded-2xl mb-6">
            <div className="text-4xl">✨</div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            ChatV2: The Future of AI Conversations
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            A complete rebuild of the chat experience focused on reliability, speed, and simplicity.
            Built alongside the existing system for seamless A/B testing.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {features.map((feature, index) => (
            <div key={index} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="text-3xl mb-3">{feature.icon}</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600 text-sm">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Performance Metrics */}
        <div className="bg-white rounded-xl p-8 mb-12 shadow-sm border border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Performance Targets</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Message Send</span>
                <span className="font-mono text-green-600">&lt;500ms p99</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Thread Switch</span>
                <span className="font-mono text-green-600">&lt;200ms p95</span>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Mobile Responsive</span>
                <span className="font-mono text-green-600">All sizes ✓</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Zero Crashes</span>
                <span className="font-mono text-green-600">Error boundaries ✓</span>
              </div>
            </div>
          </div>
        </div>

        {/* Technical Implementation */}
        <div className="bg-white rounded-xl p-8 mb-12 shadow-sm border border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Technical Implementation</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Architecture</h3>
              <ul className="space-y-2 text-gray-600">
                <li>• 4 core components (all &lt;200 lines)</li>
                <li>• Same API endpoints as ChatV1</li>
                <li>• React Error Boundaries</li>
                <li>• Optimistic UI patterns</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Improvements</h3>
              <ul className="space-y-2 text-gray-600">
                <li>• No page refreshes during chat</li>
                <li>• Simple SSE event parsing</li>
                <li>• Mobile-first responsive design</li>
                <li>• Proper memory cleanup</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center space-y-4">
          <button
            onClick={handleTryNow}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-semibold transition-colors shadow-lg hover:shadow-xl text-lg"
          >
            Try ChatV2 Now ✨
          </button>
          
          {selectedPersona && (
            <div>
              <button
                onClick={handleCompareSideBySide}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg font-medium transition-colors ml-4"
              >
                Compare Side-by-Side
              </button>
            </div>
          )}

          <div className="text-sm text-gray-500 mt-4">
            {selectedPersona ? (
              <>Using persona: <span className="font-medium">{selectedPersona.name}</span></>
            ) : (
              'Select a persona to get started'
            )}
          </div>
        </div>

        {/* Status */}
        <div className="mt-12 p-4 bg-green-50 border border-green-200 rounded-xl">
          <div className="flex items-center justify-center gap-2 text-green-700">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="font-medium">ChatV2 is ready for testing</span>
          </div>
        </div>
      </div>
    </div>
  );
} 