'use client';

import { useState, useEffect } from 'react';

interface QualityMetric {
  persona: string;
  testsPassed: number;
  totalTests: number;
  averageScore: number;
  lastTested: Date;
  status: 'excellent' | 'good' | 'needs-improvement' | 'poor';
}

export default function QualityPage() {
  const [metrics, setMetrics] = useState<QualityMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPersona, setSelectedPersona] = useState<string | null>(null);

  useEffect(() => {
    loadQualityMetrics();
  }, []);

  const loadQualityMetrics = async () => {
    try {
      // TODO: Load from API
      const mockMetrics: QualityMetric[] = [
        {
          persona: 'Alex Hormozi',
          testsPassed: 12,
          totalTests: 15,
          averageScore: 9.8,
          lastTested: new Date('2024-01-15'),
          status: 'excellent'
        },
        {
          persona: 'Technical Expert',
          testsPassed: 11,
          totalTests: 15,
          averageScore: 9.2,
          lastTested: new Date('2024-01-14'),
          status: 'excellent'
        },
        {
          persona: 'Creative Writer',
          testsPassed: 8,
          totalTests: 15,
          averageScore: 8.7,
          lastTested: new Date('2024-01-12'),
          status: 'good'
        }
      ];
      
      setTimeout(() => {
        setMetrics(mockMetrics);
        setLoading(false);
      }, 500);
    } catch (error) {
      console.error('Error loading quality metrics:', error);
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'bg-green-100 text-green-800';
      case 'good': return 'bg-blue-100 text-blue-800';
      case 'needs-improvement': return 'bg-yellow-100 text-yellow-800';
      case 'poor': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 9.5) return 'text-green-600';
    if (score >= 8.5) return 'text-blue-600';
    if (score >= 7.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const runTestSuite = (persona: string) => {
    console.log(`🧪 Running test suite for ${persona}`);
    // TODO: Implement test suite execution
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-gray-200 rounded-lg h-32"></div>
            ))}
          </div>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-gray-200 rounded-lg h-20"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const totalTests = metrics.reduce((sum, m) => sum + m.totalTests, 0);
  const totalPassed = metrics.reduce((sum, m) => sum + m.testsPassed, 0);
  const overallPassRate = totalTests > 0 ? (totalPassed / totalTests) * 100 : 0;
  const averageScore = metrics.length > 0 
    ? metrics.reduce((sum, m) => sum + m.averageScore, 0) / metrics.length 
    : 0;

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Quality Analytics</h1>
        <p className="text-gray-600 mt-1">
          Monitor AI clone performance and response quality across all personas
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-2xl">📊</span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Overall Pass Rate</p>
              <p className="text-2xl font-bold text-gray-900">{overallPassRate.toFixed(1)}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-2xl">⭐</span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Average Score</p>
              <p className={`text-2xl font-bold ${getScoreColor(averageScore)}`}>
                {averageScore.toFixed(1)}/10
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-2xl">🎭</span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Active Personas</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Personas Quality Table */}
      <div className="bg-white rounded-lg border">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Persona Performance</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Persona
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Test Results
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Average Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Tested
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {metrics.map((metric, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-semibold text-sm mr-3">
                        {metric.persona.charAt(0)}
                      </div>
                      <div className="font-medium text-gray-900">{metric.persona}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {metric.testsPassed}/{metric.totalTests} passed
                    </div>
                    <div className="text-xs text-gray-500">
                      {((metric.testsPassed / metric.totalTests) * 100).toFixed(1)}% pass rate
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-lg font-bold ${getScoreColor(metric.averageScore)}`}>
                      {metric.averageScore}/10
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(metric.status)}`}>
                      {metric.status.replace('-', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {metric.lastTested.toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => runTestSuite(metric.persona)}
                      className="text-blue-600 hover:text-blue-800 mr-4"
                    >
                      Run Tests
                    </button>
                    <button
                      onClick={() => setSelectedPersona(metric.persona)}
                      className="text-gray-600 hover:text-gray-800"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Test Suite Controls */}
      <div className="mt-8 bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Suite Management</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Available Test Suites</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                <span className="text-sm text-gray-900">Default Persona Tests (5 tests)</span>
                <button className="text-blue-600 hover:text-blue-800 text-sm">Run</button>
              </div>
              <div className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                <span className="text-sm text-gray-900">Technical Expert Tests (5 tests)</span>
                <button className="text-blue-600 hover:text-blue-800 text-sm">Run</button>
              </div>
              <div className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                <span className="text-sm text-gray-900">Creative Writer Tests (5 tests)</span>
                <button className="text-blue-600 hover:text-blue-800 text-sm">Run</button>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-900 mb-2">Bulk Actions</h4>
            <div className="space-y-3">
              <button
                onClick={() => console.log('🧪 Running all test suites')}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Run All Test Suites
              </button>
              <button
                onClick={() => console.log('📊 Generating quality report')}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
              >
                Generate Quality Report
              </button>
              <button
                onClick={() => console.log('🔄 Refreshing metrics')}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
              >
                Refresh Metrics
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 