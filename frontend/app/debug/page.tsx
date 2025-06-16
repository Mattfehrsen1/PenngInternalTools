'use client';

import { useState } from 'react';

export default function DebugPage() {
  const [filesResult, setFilesResult] = useState<string>('');
  const [chatResult, setChatResult] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const testFiles = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/personas/cd35a4a9-31ad-44f5-9de7-cc7dc3196541/files', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setFilesResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setFilesResult(`Error: ${error}`);
    }
    setLoading(false);
  };

  const testChat = async () => {
    setLoading(true);
    setChatResult('');
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          persona_id: 'cd35a4a9-31ad-44f5-9de7-cc7dc3196541',
          question: 'hello test',
          model: 'gpt-4o',
          k: 3
        }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let result = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          result += chunk;
          setChatResult(result);
        }
      }
    } catch (error) {
      setChatResult(`Error: ${error}`);
    }
    setLoading(false);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Debug API Tests</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Files Test */}
        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4">Files API Test</h2>
          <button
            onClick={testFiles}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 mb-4"
          >
            Test Files API
          </button>
          <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-64">
            {filesResult || 'Click button to test...'}
          </pre>
        </div>

        {/* Chat Test */}
        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-4">Chat API Test</h2>
          <button
            onClick={testChat}
            disabled={loading}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 mb-4"
          >
            Test Chat API
          </button>
          <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-64">
            {chatResult || 'Click button to test...'}
          </pre>
        </div>
      </div>

      <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
        <h3 className="font-semibold text-yellow-800">Instructions:</h3>
        <ol className="list-decimal list-inside text-yellow-700 mt-2">
          <li>Make sure you're logged in (go to /login first)</li>
          <li>Test Files API - should show list of uploaded files</li>
          <li>Test Chat API - should show streaming SSE response</li>
        </ol>
      </div>
    </div>
  );
}
