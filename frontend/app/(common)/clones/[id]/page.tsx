'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import AgentManager from '../../../../components/agent/AgentManager';

interface CloneDetails {
  id: string;
  name: string;
  description: string;
  purpose: string;
  avatar?: string;
  chunks: number;
  qualityScore: number;
  status: 'active' | 'training' | 'draft';
  created_at: Date;
  updated_at: Date;
}

export default function CloneEditPage() {
  const params = useParams();
  const router = useRouter();
  const cloneId = params.id as string;
  
  const [clone, setClone] = useState<CloneDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    purpose: '',
  });

  useEffect(() => {
    loadClone();
  }, [cloneId]);

  const loadClone = async () => {
    try {
      // TODO: Load from API
      const mockClone: CloneDetails = {
        id: cloneId,
        name: 'Alex Hormozi',
        description: 'Business mentor focused on scaling and revenue',
        purpose: 'Help entrepreneurs build profitable businesses by providing direct, actionable advice based on proven strategies and real-world experience.',
        chunks: 247,
        qualityScore: 9.8,
        status: 'active',
        created_at: new Date('2024-01-10'),
        updated_at: new Date('2024-01-15'),
      };
      
      setClone(mockClone);
      setFormData({
        name: mockClone.name,
        description: mockClone.description,
        purpose: mockClone.purpose,
      });
    } catch (error) {
      console.error('Error loading clone:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // TODO: Save to API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (clone) {
        setClone({
          ...clone,
          ...formData,
          updated_at: new Date(),
        });
      }
      
      // TODO: Show success message
    } catch (error) {
      console.error('Error saving clone:', error);
      // TODO: Show error message
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="bg-white rounded-lg border p-6">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-10 bg-gray-200 rounded mb-6"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-20 bg-gray-200 rounded mb-6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!clone) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="text-red-500 text-4xl mb-4">⚠️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Clone not found</h3>
          <p className="text-gray-600 mb-6">
            The clone you're looking for doesn't exist or has been deleted.
          </p>
          <Link
            href="/clones"
            className="inline-flex px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            ← Back to Clones
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link
              href="/clones"
              className="text-gray-500 hover:text-gray-700"
            >
              ← Back
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Edit Clone</h1>
              <p className="text-gray-600 mt-1">
                Customize your AI persona's identity and behavior
              </p>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <Link
              href={`/chat/${clone.id}`}
              className="px-4 py-2 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors"
            >
              💬 Test Chat
            </Link>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Edit Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Clone Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Alex Hormozi"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Short Description
                </label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Business mentor focused on scaling and revenue"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Purpose & Behavior
                </label>
                <textarea
                  value={formData.purpose}
                  onChange={(e) => handleInputChange('purpose', e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Describe how this clone should behave and what it's designed to help with..."
                />
                <p className="text-sm text-gray-500 mt-1">
                  This will influence the clone's personality and response style.
                </p>
              </div>
            </div>
          </div>

          {/* Avatar Section */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Avatar</h3>
            
            <div className="flex items-center space-x-6">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-semibold text-2xl">
                {formData.name.charAt(0) || '?'}
              </div>
              
              <div>
                <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors">
                  Upload Image
                </button>
                <p className="text-sm text-gray-500 mt-1">
                  JPG, PNG up to 2MB (optional)
                </p>
              </div>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Advanced Settings</h3>
            
            <div className="space-y-4">
              <Link
                href={`/prompts/${clone.id}`}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center">
                  <span className="text-lg mr-3">📝</span>
                  <div>
                    <div className="font-medium text-gray-900">Edit Prompts</div>
                    <div className="text-sm text-gray-500">Customize system prompts and behavior</div>
                  </div>
                </div>
                <span className="text-gray-400">→</span>
              </Link>
              
              <Link
                href={`/voice/${clone.id}`}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center">
                  <span className="text-lg mr-3">🎤</span>
                  <div>
                    <div className="font-medium text-gray-900">Voice Settings</div>
                    <div className="text-sm text-gray-500">Configure voice and audio preferences</div>
                  </div>
                </div>
                <span className="text-gray-400">→</span>
              </Link>
              
              <Link
                href={`/files/${clone.id}`}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center">
                  <span className="text-lg mr-3">📁</span>
                  <div>
                    <div className="font-medium text-gray-900">Knowledge Base</div>
                    <div className="text-sm text-gray-500">Manage uploaded documents and files</div>
                  </div>
                </div>
                <span className="text-gray-400">→</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Clone Stats */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Clone Stats</h3>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Quality Score</span>
                <span className="font-semibold text-green-600">{clone.qualityScore}/10</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Knowledge Chunks</span>
                <span className="font-semibold">{clone.chunks}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status</span>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  clone.status === 'active' ? 'bg-green-100 text-green-800' :
                  clone.status === 'training' ? 'bg-blue-100 text-blue-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {clone.status}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Created</span>
                <span className="text-sm">{clone.created_at.toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Updated</span>
                <span className="text-sm">{clone.updated_at.toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          {/* Agent Management */}
          <AgentManager 
            personaId={cloneId} 
            personaName={clone.name}
            onAgentUpdate={(agentId) => {
              console.log('Agent updated:', agentId);
              // Could update clone state here if needed
            }}
          />

          {/* Quick Actions */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            
            <div className="space-y-2">
              <button className="w-full px-4 py-2 text-left text-sm bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors">
                🧪 Run Test Suite
              </button>
              <button className="w-full px-4 py-2 text-left text-sm bg-gray-50 text-gray-600 rounded-md hover:bg-gray-100 transition-colors">
                📊 View Analytics
              </button>
              <button className="w-full px-4 py-2 text-left text-sm bg-gray-50 text-gray-600 rounded-md hover:bg-gray-100 transition-colors">
                📋 Duplicate Clone
              </button>
              <button className="w-full px-4 py-2 text-left text-sm bg-red-50 text-red-600 rounded-md hover:bg-red-100 transition-colors">
                🗑️ Delete Clone
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 