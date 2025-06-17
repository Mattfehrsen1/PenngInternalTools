'use client';

import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';

interface TestSummary {
  total_tests: number;
  passed: number;
  failed: number;
  pass_rate: number;
  average_score: number;
  average_keyword_score: number;
}

interface TestResult {
  test_id: string;
  query: string;
  passed: boolean;
  overall_score: number;
  keyword_score: number;
  citation_check: boolean;
  tone_check: number;
  llm_judge_score: number;
  errors: string[];
}

export default function BrainAnalyticsPage() {
  const router = useRouter();
  const [availableSuites, setAvailableSuites] = useState<string[]>([]);
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [selectedSuite, setSelectedSuite] = useState<string>('');
  const [testResults, setTestResults] = useState<{summary: TestSummary, results: TestResult[]} | null>(null);
  const [judgeTest, setJudgeTest] = useState({
    query: '',
    response: '',
    expected_tone: 'helpful',
    expected_keywords: ''
  });
  const [judgeResult, setJudgeResult] = useState<any>(null);
  const [isJudging, setIsJudging] = useState(false);

  useEffect(() => {
    fetchTestSuites();
  }, []);

  const fetchTestSuites = async () => {
    try {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/chat/tests/suites', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setAvailableSuites(data.available_suites || []);
      if (data.available_suites?.length > 0) {
        setSelectedSuite(data.available_suites[0]);
      }
    } catch (error) {
      console.error('Error fetching test suites:', error);
    }
  };

  const runTestSuite = async () => {
    if (!selectedSuite) return;
    
    setIsRunningTest(true);
    try {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/chat/tests/run/${selectedSuite}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          persona_name: `${selectedSuite} Test Persona`,
          persona_description: `A ${selectedSuite} AI assistant for testing`
        })
      });
      const data = await response.json();
      setTestResults(data);
    } catch (error) {
      console.error('Error running test suite:', error);
    } finally {
      setIsRunningTest(false);
    }
  };

  const runJudgeTest = async () => {
    setIsJudging(true);
    try {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/chat/judge/evaluate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: judgeTest.query,
          response: judgeTest.response,
          expected_tone: judgeTest.expected_tone,
          expected_keywords: judgeTest.expected_keywords.split(',').map(k => k.trim()).filter(k => k)
        })
      });
      const data = await response.json();
      setJudgeResult(data);
    } catch (error) {
      console.error('Error running judge test:', error);
    } finally {
      setIsJudging(false);
    }
  };

  const handleBackToBrain = () => {
    router.push('/brain');
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-sm text-gray-500">
        <button
          onClick={handleBackToBrain}
          className="hover:text-gray-700 transition-colors"
        >
          🧠 Brain
        </button>
        <span>/</span>
        <span className="text-gray-900">Quality Dashboard</span>
      </nav>

      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Quality Dashboard</h1>
        <p className="text-gray-600">Monitor AI response quality with automated testing and LLM judges</p>
      </div>

      {/* Quick Stats */}
      {testResults && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-sm font-medium text-gray-500">Pass Rate</div>
            <div className="text-2xl font-bold text-green-600">
              {(testResults.summary.pass_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-sm font-medium text-gray-500">Average Score</div>
            <div className="text-2xl font-bold text-blue-600">
              {testResults.summary.average_score.toFixed(1)}/10
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-sm font-medium text-gray-500">Tests Passed</div>
            <div className="text-2xl font-bold text-green-600">
              {testResults.summary.passed}/{testResults.summary.total_tests}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4">
            <div className="text-sm font-medium text-gray-500">Keyword Score</div>
            <div className="text-2xl font-bold text-purple-600">
              {(testResults.summary.average_keyword_score * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      )}

      {/* Automated Testing Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Automated Test Suites</h2>
        
        <div className="flex items-center space-x-4 mb-4">
          <select 
            value={selectedSuite}
            onChange={(e) => setSelectedSuite(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            {availableSuites.map(suite => (
              <option key={suite} value={suite}>
                {suite.replace('_', ' ').toUpperCase()}
              </option>
            ))}
          </select>
          
          <button
            onClick={runTestSuite}
            disabled={isRunningTest || !selectedSuite}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isRunningTest ? 'Running Tests...' : 'Run Test Suite'}
          </button>
        </div>

        {testResults && (
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">Test Results for {selectedSuite}</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Test ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Overall Score</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">LLM Judge</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Citations</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {testResults.results.map((result) => (
                    <tr key={result.test_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {result.test_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          result.passed 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {result.passed ? 'PASS' : 'FAIL'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {result.overall_score?.toFixed(2) || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {result.llm_judge_score?.toFixed(1) || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          result.citation_check 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {result.citation_check ? 'YES' : 'NO'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* LLM Judge Testing Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">LLM Judge Evaluation</h2>
        <p className="text-gray-600 mb-4">Test individual responses with our GPT-4o judge system</p>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Query</label>
              <textarea
                value={judgeTest.query}
                onChange={(e) => setJudgeTest({...judgeTest, query: e.target.value})}
                placeholder="What question was asked?"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">AI Response</label>
              <textarea
                value={judgeTest.response}
                onChange={(e) => setJudgeTest({...judgeTest, response: e.target.value})}
                placeholder="The AI response to evaluate..."
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                rows={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Expected Tone</label>
                <select
                  value={judgeTest.expected_tone}
                  onChange={(e) => setJudgeTest({...judgeTest, expected_tone: e.target.value})}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="helpful">Helpful</option>
                  <option value="technical">Technical</option>
                  <option value="creative">Creative</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Expected Keywords</label>
                <input
                  value={judgeTest.expected_keywords}
                  onChange={(e) => setJudgeTest({...judgeTest, expected_keywords: e.target.value})}
                  placeholder="keyword1, keyword2, keyword3"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>
            </div>
            <button
              onClick={runJudgeTest}
              disabled={isJudging || !judgeTest.query || !judgeTest.response}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {isJudging ? 'Evaluating...' : 'Evaluate with LLM Judge'}
            </button>
          </div>

          {judgeResult && (
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Judge Results</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-3">
                  <div className="text-sm font-medium text-blue-700">Overall Score</div>
                  <div className="text-xl font-bold text-blue-900">{judgeResult.overall_score?.toFixed(1) || 'N/A'}/10</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3">
                  <div className="text-sm font-medium text-green-700">Accuracy</div>
                  <div className="text-xl font-bold text-green-900">{judgeResult.accuracy_score || 'N/A'}/10</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-3">
                  <div className="text-sm font-medium text-purple-700">Relevance</div>
                  <div className="text-xl font-bold text-purple-900">{judgeResult.relevance_score || 'N/A'}/10</div>
                </div>
                <div className="bg-orange-50 rounded-lg p-3">
                  <div className="text-sm font-medium text-orange-700">Citations</div>
                  <div className="text-xl font-bold text-orange-900">{judgeResult.citations_score || 'N/A'}/10</div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div>
                  <h4 className="font-medium text-gray-900">Feedback</h4>
                  <p className="text-sm text-gray-600 bg-gray-50 rounded-md p-2">{judgeResult.feedback}</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Reasoning</h4>
                  <p className="text-sm text-gray-600 bg-gray-50 rounded-md p-2">{judgeResult.reasoning}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 