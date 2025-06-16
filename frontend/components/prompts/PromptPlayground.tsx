'use client';

import { useState, useEffect, useRef } from 'react';
import { X, Play, Square, RotateCcw, Zap, DollarSign, Clock, User, Bot } from 'lucide-react';

interface PromptPlaygroundProps {
  layer: string;
  name: string;
  content: string;
  token: string;
  onClose: () => void;
}

interface TestResponse {
  type: string;
  content?: string;
  citations?: Array<{
    text: string;
    source: string;
    page?: number;
  }>;
  token_count?: number;
  model?: string;
  cost_estimate?: number;
  latency_ms?: number;
  error?: string;
}

interface TestMetrics {
  tokenCount: number;
  costEstimate: number;
  latencyMs: number;
  model: string;
}

export default function PromptPlayground({
  layer,
  name,
  content,
  token,
  onClose
}: PromptPlaygroundProps) {
  const [testQuery, setTestQuery] = useState('');
  const [selectedPersona, setSelectedPersona] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt-4o');
  const [isStreaming, setIsStreaming] = useState(false);
  const [response, setResponse] = useState('');
  const [citations, setCitations] = useState<Array<{ text: string; source: string; page?: number }>>([]);
  const [metrics, setMetrics] = useState<TestMetrics>({
    tokenCount: 0,
    costEstimate: 0,
    latencyMs: 0,
    model: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [personas, setPersonas] = useState<Array<{ id: string; name: string; description: string }>>([]);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  const startTimeRef = useRef<number>(0);

  // Load available personas
  useEffect(() => {
    fetchPersonas();
  }, [token]);

  const fetchPersonas = async () => {
    try {
              const response = await fetch('/api/personas/list', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPersonas(data.personas || []);
        
        // Set first persona as default
        if (data.personas && data.personas.length > 0) {
          setSelectedPersona(data.personas[0].id);
        }
      }
    } catch (error) {
      console.error('Error fetching personas:', error);
    }
  };

  const handleTest = async () => {
    if (!testQuery.trim() || !selectedPersona || isStreaming) return;

    setIsStreaming(true);
    setResponse('');
    setCitations([]);
    setError(null);
    startTimeRef.current = Date.now();

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    try {
      const requestBody = {
        layer,
        name,
        content,
        test_query: testQuery,
        persona_id: selectedPersona,
        model: selectedModel
      };

      const response = await fetch('/api/prompts/test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body stream available');
      }

      let responseText = '';
      let finalMetrics: TestMetrics = {
        tokenCount: 0,
        costEstimate: 0,
        latencyMs: 0,
        model: selectedModel
      };

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        // Decode the chunk
        const chunk = new TextDecoder().decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data: TestResponse = JSON.parse(line.slice(6));
              
              switch (data.type) {
                case 'chunk':
                  if (data.content) {
                    responseText += data.content;
                    setResponse(responseText);
                  }
                  break;
                  
                case 'citations':
                  if (data.citations) {
                    setCitations(data.citations);
                  }
                  break;
                  
                case 'complete':
                  const latency = Date.now() - startTimeRef.current;
                  finalMetrics = {
                    tokenCount: data.token_count || 0,
                    costEstimate: data.cost_estimate || 0,
                    latencyMs: latency,
                    model: data.model || selectedModel
                  };
                  setMetrics(finalMetrics);
                  break;
                  
                case 'error':
                  setError(data.error || 'Unknown error occurred');
                  break;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        setError('Test cancelled by user');
      } else {
        setError(error instanceof Error ? error.message : 'An unexpected error occurred');
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const handleClear = () => {
    setResponse('');
    setCitations([]);
    setError(null);
    setMetrics({
      tokenCount: 0,
      costEstimate: 0,
      latencyMs: 0,
      model: ''
    });
  };

  // Calculate token/cost estimates
  const estimateTokens = (text: string) => {
    // Rough estimation: ~4 characters per token
    return Math.ceil(text.length / 4);
  };

  const estimateCost = (tokens: number, model: string) => {
    // Rough cost estimates (per 1K tokens)
    const rates: { [key: string]: number } = {
      'gpt-4o': 0.03,
      'gpt-4': 0.03,
      'gpt-3.5-turbo': 0.002,
      'claude-3': 0.025
    };
    return (tokens / 1000) * (rates[model] || 0.01);
  };

  const queryTokens = estimateTokens(testQuery + content);
  const estimatedCost = estimateCost(queryTokens, selectedModel);

  return (
    <div className="flex flex-col h-full max-h-[80vh]">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">🧪 Prompt Playground</h2>
          <p className="text-sm text-gray-600 mt-1">
            Test <span className="font-medium">{layer.toUpperCase()}</span> / {name} in real-time
          </p>
        </div>
        
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <X className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Test Configuration */}
        <div className="w-1/2 p-6 border-r border-gray-200 flex flex-col">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Test Configuration</h3>
          
          {/* Persona Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="w-4 h-4 inline mr-2" />
              Persona
            </label>
            <select
              value={selectedPersona}
              onChange={(e) => setSelectedPersona(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select a persona...</option>
              {personas.map((persona) => (
                <option key={persona.id} value={persona.id}>
                  {persona.name}
                </option>
              ))}
            </select>
            {selectedPersona && (
              <p className="text-xs text-gray-500 mt-1">
                {personas.find(p => p.id === selectedPersona)?.description}
              </p>
            )}
          </div>

          {/* Model Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Bot className="w-4 h-4 inline mr-2" />
              Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="gpt-4o">GPT-4o (Recommended)</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="claude-3">Claude-3</option>
            </select>
          </div>

          {/* Test Query */}
          <div className="mb-4 flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Test Query
            </label>
            <textarea
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              placeholder="Enter your test message here..."
              className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            />
          </div>

          {/* Estimates */}
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Estimates</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center">
                <Zap className="w-4 h-4 text-blue-500 mr-2" />
                <span className="text-gray-600">Tokens: ~{queryTokens}</span>
              </div>
              <div className="flex items-center">
                <DollarSign className="w-4 h-4 text-green-500 mr-2" />
                <span className="text-gray-600">Cost: ~${estimatedCost.toFixed(4)}</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <button
              onClick={handleTest}
              disabled={!testQuery.trim() || !selectedPersona || isStreaming}
              className="flex-1 flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isStreaming ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Test
                </>
              )}
            </button>
            
            {isStreaming && (
              <button
                onClick={handleCancel}
                className="px-4 py-3 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors"
              >
                <Square className="w-4 h-4" />
              </button>
            )}
            
            <button
              onClick={handleClear}
              disabled={isStreaming}
              className="px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right Panel - Response */}
        <div className="w-1/2 p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Response</h3>
            
            {/* Metrics */}
            {metrics.tokenCount > 0 && (
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <div className="flex items-center">
                  <Zap className="w-4 h-4 mr-1" />
                  {metrics.tokenCount} tokens
                </div>
                <div className="flex items-center">
                  <DollarSign className="w-4 h-4 mr-1" />
                  ${metrics.costEstimate.toFixed(4)}
                </div>
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  {metrics.latencyMs}ms
                </div>
              </div>
            )}
          </div>

          {/* Response Content */}
          <div className="flex-1 bg-gray-50 rounded-lg p-4 overflow-y-auto">
            {error ? (
              <div className="text-red-600 bg-red-50 border border-red-200 rounded-lg p-4">
                <strong>Error:</strong> {error}
              </div>
            ) : response ? (
              <div className="space-y-4">
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-gray-800">
                    {response}
                  </pre>
                </div>
                
                {/* Citations */}
                {citations.length > 0 && (
                  <div className="border-t border-gray-200 pt-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Citations</h4>
                    <div className="space-y-2">
                      {citations.map((citation, index) => (
                        <div key={index} className="text-xs bg-white border border-gray-200 rounded p-2">
                          <div className="font-medium text-gray-800">{citation.text}</div>
                          <div className="text-gray-500 mt-1">
                            Source: {citation.source}
                            {citation.page && ` (Page ${citation.page})`}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <Bot className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Run a test to see the response</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 