'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { usePersona } from '@/lib/contexts/PersonaContext';
import Link from 'next/link';

interface Persona {
  id: string;
  name: string;
  description: string;
}

interface VoiceOption {
  id: string;
  name: string;
  description: string;
  gender: 'male' | 'female' | 'neutral';
  accent: string;
  category: 'professional' | 'conversational' | 'narrative' | 'character';
}

interface VoiceSettings {
  voiceId: string;
  speed: number;
  pitch: number;
  stability: number;
  clarity: number;
}

// Global voice streaming function stub (same as in ChatPane)
(window as any).streamVoice = (text: string) => {
  console.log('🔊 Voice streaming (stub):', text.substring(0, 50) + '...');
  // TODO: Implement actual voice streaming with ElevenLabs
};

export default function VoicePage() {
  const params = useParams();
  const router = useRouter();
  const personaSlug = params.persona as string;
  const { selectedPersona, personas, setSelectedPersona } = usePersona();
  const audioRef = useRef<HTMLAudioElement>(null);

  const [selectedVoice, setSelectedVoice] = useState<string>('default');
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings>({
    voiceId: 'default',
    speed: 1.0,
    pitch: 1.0,
    stability: 0.5,
    clarity: 0.75
  });
  const [sampleText, setSampleText] = useState('Hello! I\'m excited to help you today. This is how I sound when speaking.');
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>('professional');

  const [voiceOptions, setVoiceOptions] = useState<VoiceOption[]>([]);

  const categories = [
    { id: 'professional', label: 'Professional', icon: '💼' },
    { id: 'conversational', label: 'Conversational', icon: '💬' },
    { id: 'narrative', label: 'Narrative', icon: '📖' },
    { id: 'character', label: 'Character', icon: '🎭' }
  ];

  // Set persona based on URL parameter
  useEffect(() => {
    if (personaSlug && personas.length > 0) {
      const persona = personas.find(p => p.slug === personaSlug || p.id === personaSlug);
      if (persona && (!selectedPersona || selectedPersona.slug !== persona.slug)) {
        setSelectedPersona(persona);
      } else if (!persona) {
        router.push('/clones');
        return;
      }
    }
  }, [personaSlug, personas, selectedPersona, setSelectedPersona, router]);

  // Load voice settings and available voices for the selected persona
  useEffect(() => {
    if (selectedPersona) {
      loadVoiceData();
    }
  }, [selectedPersona]);

  const loadVoiceData = async () => {
    if (!selectedPersona) return;
    
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        setError('Authentication required');
        return;
      }

      // Load available voices from ElevenLabs
      const voicesResponse = await fetch('/api/voice/list', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (voicesResponse.ok) {
        const voicesData = await voicesResponse.json();
        // Map ElevenLabs voices to our UI format
        const mappedVoices: VoiceOption[] = voicesData.voices.map((voice: any) => ({
          id: voice.voice_id,
          name: voice.name,
          description: voice.description || `${voice.labels?.gender || 'unknown'} voice`,
          gender: voice.labels?.gender === 'male' ? 'male' : 
                  voice.labels?.gender === 'female' ? 'female' : 'neutral',
          accent: voice.labels?.accent || 'American',
          category: voice.category || 'conversational'
        }));
        setVoiceOptions(mappedVoices);
      }

      // Load persona's current voice settings
      const settingsResponse = await fetch(`/api/personas/${selectedPersona.id}/settings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (settingsResponse.ok) {
        const settingsData = await settingsResponse.json();
        const voiceSettings = settingsData.voice_settings || {};
        
        setVoiceSettings({
          voiceId: settingsData.voice_id || 'EXAVITQu4vr4xnSDxMaL',
          speed: voiceSettings.speed || 1.0,
          pitch: voiceSettings.pitch || 1.0,
          stability: voiceSettings.stability || 0.5,
          clarity: voiceSettings.similarity_boost || 0.75
        });
        setSelectedVoice(settingsData.voice_id || 'EXAVITQu4vr4xnSDxMaL');
      }
    } catch (err) {
      setError('Failed to load voice data');
      console.error('Error loading voice data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVoicePreview = async (voiceId: string, text: string) => {
    if (!selectedPersona) return;
    
    try {
      setIsGenerating(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        setError('Authentication required');
        return;
      }

      // Use the real voice streaming endpoint
      const response = await fetch(`/api/personas/${selectedPersona.id}/voice/stream`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          text: text,
          voice_id: voiceId,
          voice_settings: {
            stability: voiceSettings.stability,
            similarity_boost: voiceSettings.clarity,
            style: 0.0,
            use_speaker_boost: true
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Voice generation failed: ${response.status}`);
      }

      // Convert response to audio and play
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.onplay = () => setIsPlaying(true);
        audioRef.current.onended = () => setIsPlaying(false);
        audioRef.current.onerror = () => {
          setError('Audio playback failed');
          setIsPlaying(false);
        };
        await audioRef.current.play();
      }

    } catch (err) {
      setError('Failed to generate voice preview');
      console.error('Error generating voice:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveSettings = async () => {
    if (!selectedPersona) return;

    try {
      setError(null);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        setError('Authentication required');
        return;
      }

      // Save voice settings to the real API
      const response = await fetch(`/api/personas/${selectedPersona.id}/settings`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          voice_id: voiceSettings.voiceId,
          voice_settings: {
            stability: voiceSettings.stability,
            similarity_boost: voiceSettings.clarity,
            style: 0.0,
            use_speaker_boost: true
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to save settings: ${response.status}`);
      }

      // Show success message temporarily
      const originalError = error;
      setError('✅ Voice settings saved successfully!');
      setTimeout(() => setError(originalError), 3000);
      
    } catch (err) {
      setError('Failed to save voice settings');
      console.error('Error saving voice settings:', err);
    }
  };

  const updateVoiceSetting = (key: keyof VoiceSettings, value: string | number) => {
    setVoiceSettings(prev => ({ ...prev, [key]: value }));
  };

  const filteredVoices = voiceOptions.filter(voice => voice.category === activeCategory);

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="h-4 bg-gray-200 rounded w-96 mb-8"></div>
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-gray-200 rounded-lg h-80"></div>
            <div className="bg-gray-200 rounded-lg h-80"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!selectedPersona) {
    return (
      <div className="p-6 text-center">
        <div className="text-gray-500 mb-4">No persona selected</div>
        <button
          onClick={() => router.push('/clones')}
          className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600"
        >
          Select a Persona
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center text-white font-semibold">
              {selectedPersona.name.charAt(0)}
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {selectedPersona.name} Voice
              </h1>
              <p className="text-sm text-gray-600">{selectedPersona.description}</p>
            </div>
          </div>
          
          <button
            onClick={handleSaveSettings}
            className="px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 text-sm"
          >
            💾 Save Settings
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-auto">
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Voice Selection */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Voice Selection</h3>
                
                {/* Category Tabs */}
                <div className="flex space-x-1 mb-6 bg-gray-100 rounded-lg p-1">
                  {categories.map(category => (
                    <button
                      key={category.id}
                      onClick={() => setActiveCategory(category.id)}
                      className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
                        activeCategory === category.id
                          ? 'bg-white text-gray-900 shadow-sm'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      <span className="mr-2">{category.icon}</span>
                      {category.label}
                    </button>
                  ))}
                </div>

                {/* Voice Options */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredVoices.map((voice) => (
                    <div
                      key={voice.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        selectedVoice === voice.id
                          ? 'border-orange-500 bg-orange-50 ring-2 ring-orange-200'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        setSelectedVoice(voice.id);
                        updateVoiceSetting('voiceId', voice.id);
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <div className="font-medium text-gray-900">{voice.name}</div>
                            <div className={`text-xs px-2 py-0.5 rounded-full ${
                              voice.gender === 'male' ? 'bg-blue-100 text-blue-800' :
                              voice.gender === 'female' ? 'bg-pink-100 text-pink-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {voice.gender}
                            </div>
                          </div>
                          <div className="text-sm text-gray-500 mb-2">{voice.description}</div>
                          <div className="text-xs text-gray-400">{voice.accent} accent</div>
                        </div>
                        
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleVoicePreview(voice.id, sampleText);
                          }}
                          disabled={isGenerating}
                          className="ml-2 px-3 py-1.5 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors text-sm disabled:opacity-50"
                        >
                          {isGenerating ? '⏳' : '🔊'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Voice Playground & Settings */}
            <div className="space-y-6">
              {/* Playground */}
              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Voice Playground</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Sample Text
                    </label>
                    <textarea
                      value={sampleText}
                      onChange={(e) => setSampleText(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-orange-500 focus:border-orange-500 text-sm"
                      rows={4}
                      placeholder="Enter text to test voice generation..."
                    />
                  </div>

                  <button
                    onClick={() => handleVoicePreview(selectedVoice, sampleText)}
                    disabled={isGenerating || !sampleText.trim()}
                    className="w-full px-4 py-3 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isGenerating ? '⏳ Generating...' : '🎤 Generate Voice Sample'}
                  </button>

                  {isPlaying && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <div className="text-sm text-green-800">Playing voice sample...</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Voice Settings */}
              <div className="bg-white rounded-lg border p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Voice Settings</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Speed: {voiceSettings.speed.toFixed(1)}x
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="2"
                      step="0.1"
                      value={voiceSettings.speed}
                      onChange={(e) => updateVoiceSetting('speed', parseFloat(e.target.value))}
                      className="w-full accent-orange-500"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Slow</span>
                      <span>Normal</span>
                      <span>Fast</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Stability: {voiceSettings.stability.toFixed(2)}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={voiceSettings.stability}
                      onChange={(e) => updateVoiceSetting('stability', parseFloat(e.target.value))}
                      className="w-full accent-orange-500"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>More variable</span>
                      <span>More stable</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Clarity: {voiceSettings.clarity.toFixed(2)}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={voiceSettings.clarity}
                      onChange={(e) => updateVoiceSetting('clarity', parseFloat(e.target.value))}
                      className="w-full accent-orange-500"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>More creative</span>
                      <span>More precise</span>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-gray-200">
                  <div className="text-sm text-blue-600 bg-blue-50 p-3 rounded-md">
                    <strong>Note:</strong> Voice settings are automatically applied to chat responses. 
                    Test different combinations to find the perfect voice for your persona.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <audio ref={audioRef} className="hidden" />
    </div>
  );
} 