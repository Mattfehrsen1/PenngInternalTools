'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { usePersona } from '@/lib/contexts/PersonaContext';
import PersonaSelector from '@/components/PersonaSelector';

interface PromptData {
  system: string;
  rag: string;
  user: string;
}

interface Template {
  id: string;
  name: string;
  description: string;
  prompts: PromptData;
}

export default function PromptsPage() {
  const params = useParams();
  const router = useRouter();
  const personaSlug = params.persona as string;
  const { selectedPersona, personas, setSelectedPersona } = usePersona();

  const [activeTab, setActiveTab] = useState<'system' | 'rag' | 'user'>('system');
  const [prompts, setPrompts] = useState<PromptData>({
    system: '',
    rag: '',
    user: ''
  });
  const [originalPrompts, setOriginalPrompts] = useState<PromptData>({
    system: '',
    rag: '',
    user: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  // No hardcoded templates - all data must come from API

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

  // Load prompts for the selected persona
  useEffect(() => {
    if (selectedPersona) {
      loadPrompts();
      loadTemplates();
    }
  }, [selectedPersona]);

  const loadTemplates = async () => {
    try {
      setLoadingTemplates(true);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Authentication token not found');
      }

      // Real API call to get templates
      const response = await fetch(`/api/personas/templates`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Transform backend templates to match frontend interface
        const apiTemplates: Template[] = data.templates.map((template: any) => ({
          id: template.id,
          name: template.name,
          description: template.description,
          prompts: {
            system: template.system_prompt || '',
            rag: template.rag_prompt || '',
            user: template.user_prompt || ''
          }
        }));
        setTemplates(apiTemplates);
      } else {
        console.error('Failed to load templates from API:', response.status);
        setError('Failed to load templates from server');
        setTemplates([]);
      }
    } catch (err) {
      console.error('Error loading templates:', err);
      setError('Failed to connect to server');
      setTemplates([]);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const loadPrompts = async () => {
    if (!selectedPersona) return;
    
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Authentication token not found');
      }

      // Real API call to get prompts
      const response = await fetch(`/api/personas/${selectedPersona.id}/prompts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Transform backend response to match frontend interface
      const promptsData: PromptData = {
        system: '',
        rag: '',
        user: ''
      };

      // Handle different response formats from backend
      if (data.prompts) {
        Object.entries(data.prompts).forEach(([layer, versions]) => {
          const layerVersions = versions as any[];
          const activePrompt = layerVersions?.find(v => v.is_active);
          if (activePrompt) {
            promptsData[layer as keyof PromptData] = activePrompt.content;
          }
        });
      }

      // No hardcoded defaults - show real state from API

      setPrompts(promptsData);
      setOriginalPrompts(promptsData);
      setHasChanges(false);
    } catch (err) {
      setError('Failed to load prompts');
      console.error('Error loading prompts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePromptChange = (tab: keyof PromptData, value: string) => {
    const newPrompts = { ...prompts, [tab]: value };
    setPrompts(newPrompts);
    
    // Check if there are changes
    const changed = newPrompts.system !== originalPrompts.system ||
                   newPrompts.rag !== originalPrompts.rag ||
                   newPrompts.user !== originalPrompts.user;
    setHasChanges(changed);
  };

  const handleSave = async () => {
    if (!selectedPersona) return;
    
    try {
      setSaving(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Authentication token not found');
      }

      // Save each prompt layer separately
      const layers: (keyof PromptData)[] = ['system', 'rag', 'user'];
      
      for (const layer of layers) {
                 const response = await fetch(
           `/api/personas/${selectedPersona.id}/prompts/${layer}/main/versions`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              content: prompts[layer],
              commit_message: `Updated ${layer} prompt via editor`,
            }),
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to save ${layer} prompt: ${response.status}`);
        }
      }

      // Reload prompts from server to get the latest saved state
      await loadPrompts();
      setHasChanges(false);
    } catch (err) {
      setError('Failed to save prompts');
      console.error('Error saving prompts:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleApplyTemplate = async (template: Template) => {
    if (!selectedPersona) return;
    
    try {
      setSaving(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('Authentication token not found');
      }

      // Real API call to apply template
      const response = await fetch(
        `/api/personas/${selectedPersona.id}/prompts/from-template`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            template_name: template.id, // Use template ID (e.g., 'alex_hormozi', 'empathetic_therapist')
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to apply template: ${response.status}`);
      }

      const result = await response.json();
      
      // Update local state with template prompts
      setPrompts(template.prompts);
      setOriginalPrompts(template.prompts);
      setHasChanges(false);
      setShowTemplateSelector(false);
    } catch (err) {
      setError('Failed to apply template');
      console.error('Error applying template:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setPrompts(originalPrompts);
    setHasChanges(false);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="h-4 bg-gray-200 rounded w-96 mb-8"></div>
          <div className="grid grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-gray-200 rounded-lg h-64"></div>
            ))}
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

  const tabs = [
    { id: 'system' as const, label: 'System Prompt', description: 'Core personality and behavior' },
    { id: 'rag' as const, label: 'RAG Template', description: 'How to incorporate knowledge base context' },
    { id: 'user' as const, label: 'User Template', description: 'How to process user queries' }
  ];

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-semibold">
              {selectedPersona.name.charAt(0)}
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                {selectedPersona.name} Prompts
              </h1>
              <p className="text-sm text-gray-600">{selectedPersona.description}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            {/* Template Selector */}
            <div className="relative">
              <button
                onClick={() => setShowTemplateSelector(!showTemplateSelector)}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
              >
                📝 Apply Template
              </button>
              
              {showTemplateSelector && (
                <div className="absolute right-0 top-full mt-1 w-80 bg-white border border-gray-200 rounded-md shadow-lg z-50">
                  <div className="p-2 border-b">
                    <div className="text-sm font-medium text-gray-900">Choose Template</div>
                  </div>
                  <div className="max-h-60 overflow-y-auto">
                    {templates.map(template => (
                      <button
                        key={template.id}
                        onClick={() => handleApplyTemplate(template)}
                        className="w-full text-left px-3 py-3 hover:bg-gray-50 border-b last:border-b-0"
                      >
                        <div className="font-medium text-sm">{template.name}</div>
                        <div className="text-xs text-gray-500 mt-1">{template.description}</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Save/Reset Actions */}
            {hasChanges && (
              <>
                <button
                  onClick={handleReset}
                  className="px-3 py-2 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Reset
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-3 py-2 text-sm bg-orange-500 text-white rounded-md hover:bg-orange-600 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </>
            )}
          </div>
        </div>

        {/* Persona Selector */}
        <div className="mb-2">
          <PersonaSelector currentPath="prompts" className="max-w-md" />
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="flex space-x-8">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div>{tab.label}</div>
              <div className="text-xs text-gray-400 mt-1">{tab.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Prompt Editor */}
      <div className="flex-1 p-6">
        <div className="h-full">
          <textarea
            value={prompts[activeTab]}
            onChange={(e) => handlePromptChange(activeTab, e.target.value)}
            placeholder={`Enter your ${activeTab} prompt here...`}
            className="w-full h-full p-4 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
      </div>
    </div>
  );
} 