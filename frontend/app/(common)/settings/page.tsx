'use client';

import { useState, useEffect } from 'react';

interface Settings {
  apiKeys: {
    openai: string;
    elevenlabs: string;
    pinecone: string;
  };
  defaultModel: string;
  temperature: number;
  maxTokens: number;
  features: {
    voiceEnabled: boolean;
    analyticsEnabled: boolean;
    betaFeatures: boolean;
  };
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    apiKeys: {
      openai: '',
      elevenlabs: '',
      pinecone: ''
    },
    defaultModel: 'gpt-4o',
    temperature: 0.7,
    maxTokens: 2048,
    features: {
      voiceEnabled: false,
      analyticsEnabled: true,
      betaFeatures: false
    }
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showApiKeys, setShowApiKeys] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      // TODO: Load from API
      const mockSettings: Settings = {
        apiKeys: {
          openai: 'sk-...configured',
          elevenlabs: 'el_...configured',
          pinecone: 'pc-...configured'
        },
        defaultModel: 'gpt-4o',
        temperature: 0.7,
        maxTokens: 2048,
        features: {
          voiceEnabled: true,
          analyticsEnabled: true,
          betaFeatures: false
        }
      };
      
      setTimeout(() => {
        setSettings(mockSettings);
        setLoading(false);
      }, 500);
    } catch (error) {
      console.error('Error loading settings:', error);
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // TODO: Save to API
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Settings saved:', settings);
    } catch (error) {
      console.error('Error saving settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (path: string, value: any) => {
    setSettings(prev => {
      const keys = path.split('.');
      const updated = { ...prev };
      let current: any = updated;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] };
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return updated;
    });
  };

  const maskApiKey = (key: string) => {
    if (!key || key.length < 8) return key;
    return key.substring(0, 6) + '...' + key.substring(key.length - 4);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="space-y-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-gray-200 rounded-lg h-48"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">
          Configure API keys, model preferences, and system features
        </p>
      </div>

      <div className="space-y-8">
        {/* API Keys */}
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">API Keys</h3>
            <button
              onClick={() => setShowApiKeys(!showApiKeys)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {showApiKeys ? 'Hide' : 'Show'} Keys
            </button>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                OpenAI API Key
              </label>
              <input
                type={showApiKeys ? 'text' : 'password'}
                value={showApiKeys ? settings.apiKeys.openai : maskApiKey(settings.apiKeys.openai)}
                onChange={(e) => updateSetting('apiKeys.openai', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="sk-..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ElevenLabs API Key
              </label>
              <input
                type={showApiKeys ? 'text' : 'password'}
                value={showApiKeys ? settings.apiKeys.elevenlabs : maskApiKey(settings.apiKeys.elevenlabs)}
                onChange={(e) => updateSetting('apiKeys.elevenlabs', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="el_..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Pinecone API Key
              </label>
              <input
                type={showApiKeys ? 'text' : 'password'}
                value={showApiKeys ? settings.apiKeys.pinecone : maskApiKey(settings.apiKeys.pinecone)}
                onChange={(e) => updateSetting('apiKeys.pinecone', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="pc-..."
              />
            </div>
          </div>
        </div>

        {/* Model Configuration */}
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Configuration</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Model
              </label>
              <select
                value={settings.defaultModel}
                onChange={(e) => updateSetting('defaultModel', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="claude-3-opus">Claude 3 Opus</option>
                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Tokens
              </label>
              <input
                type="number"
                value={settings.maxTokens}
                onChange={(e) => updateSetting('maxTokens', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                min="256"
                max="8192"
              />
            </div>
          </div>
          
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Temperature: {settings.temperature}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={settings.temperature}
              onChange={(e) => updateSetting('temperature', parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Conservative</span>
              <span>Balanced</span>
              <span>Creative</span>
            </div>
          </div>
        </div>

        {/* Feature Flags */}
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Flags</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">Voice Integration</div>
                <div className="text-sm text-gray-500">Enable ElevenLabs voice synthesis</div>
              </div>
              <button
                onClick={() => updateSetting('features.voiceEnabled', !settings.features.voiceEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.features.voiceEnabled ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.features.voiceEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">Analytics</div>
                <div className="text-sm text-gray-500">Track usage and performance metrics</div>
              </div>
              <button
                onClick={() => updateSetting('features.analyticsEnabled', !settings.features.analyticsEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.features.analyticsEnabled ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.features.analyticsEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">Beta Features</div>
                <div className="text-sm text-gray-500">Enable experimental functionality</div>
              </div>
              <button
                onClick={() => updateSetting('features.betaFeatures', !settings.features.betaFeatures)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.features.betaFeatures ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.features.betaFeatures ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* System Information */}
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-gray-500 mb-1">Version</div>
              <div className="font-medium">Clone Advisor v1.0.0</div>
            </div>
            <div>
              <div className="text-sm text-gray-500 mb-1">Sprint</div>
              <div className="font-medium">Sprint 4 - UI Revamp</div>
            </div>
            <div>
              <div className="text-sm text-gray-500 mb-1">Environment</div>
              <div className="font-medium">Development</div>
            </div>
            <div>
              <div className="text-sm text-gray-500 mb-1">Last Updated</div>
              <div className="font-medium">{new Date().toLocaleDateString()}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="mt-8 flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
} 