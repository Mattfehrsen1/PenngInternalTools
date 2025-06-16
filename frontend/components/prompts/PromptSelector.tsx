'use client';

import { useState } from 'react';
import { Plus, X } from 'lucide-react';
import { usePrompts, CreatePromptData, PromptInfo } from '@/lib/hooks/usePrompts';

interface SelectedPrompt {
  layer: string;
  name: string;
}

interface PromptSelectorProps {
  selectedPrompt: SelectedPrompt | null;
  onSelectPrompt: (prompt: SelectedPrompt) => void;
  token: string;
}

export default function PromptSelector({
  selectedPrompt,
  onSelectPrompt,
  token
}: PromptSelectorProps) {
  const { prompts, loading: isLoading, error, createPrompt, refreshPrompts } = usePrompts(token);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<CreatePromptData>({
    layer: 'system',
    name: '',
    content: '',
    commit_message: 'Initial version'
  });
  const [isCreating, setIsCreating] = useState(false);

  const handleCreatePrompt = async () => {
    if (!createForm.name.trim() || !createForm.content.trim()) {
      alert('Please fill in all required fields');
      return;
    }

    setIsCreating(true);
    try {
      const success = await createPrompt(createForm);
      
      if (success) {
        // Close modal and reset form
        setShowCreateModal(false);
        setCreateForm({
          layer: 'system',
          name: '',
          content: '',
          commit_message: 'Initial version'
        });
        
        // Select the newly created prompt
        onSelectPrompt({ 
          layer: createForm.layer, 
          name: createForm.name 
        });
      } else {
        alert('Failed to create prompt. Please try again.');
      }
    } catch (error) {
      console.error('Error creating prompt:', error);
      alert('Error creating prompt. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const handlePromptClick = (layer: string, name: string) => {
    onSelectPrompt({ layer, name });
  };

  const isSelected = (layer: string, name: string) => {
    return selectedPrompt?.layer === layer && selectedPrompt?.name === name;
  };

  const getLayerIcon = (layer: string) => {
    switch (layer.toLowerCase()) {
      case 'system':
        return '🤖';
      case 'rag':
        return '📚';
      case 'user':
        return '💬';
      default:
        return '📝';
    }
  };

  const getLayerDescription = (layer: string) => {
    switch (layer.toLowerCase()) {
      case 'system':
        return 'Create human-like personas with personality, expertise & authentic communication';
      case 'rag':
        return 'Context formatting & citations';
      case 'user':
        return 'Query processing & validation';
      default:
        return 'Custom prompt templates';
    }
  };

  const getPlaceholderContent = (layer: string) => {
    switch (layer.toLowerCase()) {
      case 'system':
        return `You are {{persona_name}}, {{persona_description}}.

=== BACKGROUND & EXPERTISE ===
{{background}}
• What's your story? How did you become an expert?
• What specific domain knowledge do you possess?
• What experiences shaped your perspective?

=== CORE VALUES & MORAL COMPASS ===
{{values}}
• What principles guide your decisions?
• What do you care most deeply about?
• What would you never compromise on?

=== COMMUNICATION STYLE ===
Tone: {{tone}} (e.g., conversational, formal, direct, empathetic)
Speech Patterns: {{speech_patterns}} (e.g., uses "right?", "uh", rhetorical questions)
Emotional Range: {{emotional_traits}} (e.g., empathetic but direct, passionate about topics)

=== BEHAVIORAL TRAITS ===
{{behavioral_traits}}
• Are you analytical? Intuitive? Assertive? Collaborative?
• How do you handle disagreement?
• Do you challenge assumptions or validate feelings first?
• Are you detail-oriented or big-picture focused?

=== RULES OF ENGAGEMENT ===
Your Purpose: {{purpose}}
• What's your main goal in conversations?
• What type of help do you provide?

Always Do:
• {{always_do}}
• Ask clarifying questions when requests are vague
• Provide actionable, specific advice
• Stay true to your personality and expertise

Never Do:
• {{restrictions}}
• Give advice outside your expertise without disclaimers
• Use jargon without explanation

=== EXAMPLE RESPONSE STYLE ===
Here's how you should respond to questions:

Question: [Sample question in your domain]
Your Response: "[Show your personality, tone, and expertise in a typical response. Include your speech patterns, how you structure advice, and your unique perspective.]"

=== MEMORY & CONTEXT ===
• You can reference past conversations with this user
• You remember their goals and previous challenges
• You build on previous advice and check progress
• You adapt your communication style based on what works for them

Remember: You're not just providing information - you're being a specific person with unique experiences, perspectives, and ways of communicating. Every response should feel authentically YOU.`;
      
      case 'rag':
        return `Based on the following context, provide a comprehensive answer to the user's question.

Context:
{% for chunk in chunks %}
[{{chunk.index_plus_one}}] {{chunk.text}}
Source: {{chunk.source}}{% if chunk.page %} (Page {{chunk.page}}){% endif %}

{% endfor %}

User Question: {{query}}

Please provide a detailed response using the context above, and cite your sources using the reference numbers [1], [2], etc.`;
      
      case 'user':
        return `Process the following user query and provide appropriate guidance:

User Query: {{query}}

Instructions:
- Understand the user's intent
- Provide clear and helpful responses
- Ask clarifying questions if needed
- Maintain a helpful and professional tone`;
      
      default:
        return 'Enter your custom prompt template here...';
    }
  };

  if (isLoading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-4 bg-gray-200 rounded w-20"></div>
              <div className="space-y-1">
                <div className="h-8 bg-gray-100 rounded"></div>
                <div className="h-8 bg-gray-100 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-red-800 text-sm">{error}</span>
          </div>
          <button
            onClick={refreshPrompts}
            className="mt-2 text-red-600 hover:text-red-800 text-sm underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-6 p-4">
        {/* Create New Prompt Button */}
        <button
          onClick={() => setShowCreateModal(true)}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create New Prompt
        </button>

        {Object.entries(prompts).map(([layer, promptList]) => (
          <div key={layer} className="space-y-2">
            {/* Layer Header */}
            <div className="flex items-center space-x-2 pb-2 border-b border-gray-200">
              <span className="text-lg">{getLayerIcon(layer)}</span>
              <div>
                <h3 className="font-semibold text-gray-900 capitalize">{layer}</h3>
                <p className="text-xs text-gray-500">{getLayerDescription(layer)}</p>
              </div>
            </div>

            {/* Prompts List */}
            <div className="space-y-1">
              {promptList.length > 0 ? (
                promptList.map((prompt) => (
                  <button
                    key={`${prompt.layer}-${prompt.name}`}
                    onClick={() => handlePromptClick(prompt.layer, prompt.name)}
                    className={`w-full text-left p-3 rounded-lg border transition-all hover:shadow-sm ${
                      isSelected(prompt.layer, prompt.name)
                        ? 'bg-blue-50 border-blue-200 ring-2 ring-blue-500 ring-opacity-20'
                        : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{prompt.name}</p>
                        <div className="flex items-center space-x-2 mt-1">
                          {prompt.active_version && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                              v{prompt.active_version}
                            </span>
                          )}
                          <span className="text-xs text-gray-500">
                            {prompt.total_versions} version{prompt.total_versions !== 1 ? 's' : ''}
                          </span>
                        </div>
                      </div>
                      
                      {isSelected(prompt.layer, prompt.name) && (
                        <svg className="w-5 h-5 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                    </div>
                    
                    {prompt.last_updated && (
                      <p className="text-xs text-gray-400 mt-1">
                        Updated {new Date(prompt.last_updated).toLocaleDateString()}
                      </p>
                    )}
                  </button>
                ))
              ) : (
                <div className="text-center py-4 text-gray-500">
                  <svg className="w-8 h-8 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-sm">No {layer} prompts yet</p>
                  <p className="text-xs">Create your first prompt!</p>
                </div>
              )}
            </div>
          </div>
        ))}

        {Object.keys(prompts).length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Prompts Found</h3>
            <p className="text-gray-600">Create your first prompt to get started!</p>
          </div>
        )}
      </div>

      {/* Create Prompt Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Create New Prompt</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-140px)]">
              {/* Layer Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt Layer
                </label>
                <select
                  value={createForm.layer}
                  onChange={(e) => {
                    const newLayer = e.target.value;
                    setCreateForm(prev => ({
                      ...prev,
                      layer: newLayer,
                      content: getPlaceholderContent(newLayer)
                    }));
                  }}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="system">🤖 System - Human-like personas with personality & expertise</option>
                  <option value="rag">📚 RAG - Context formatting & citations</option>
                  <option value="user">💬 User - Query processing & validation</option>
                </select>
              </div>

              {/* Prompt Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt Name *
                </label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., technical_expert, creative_writer, default"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Use lowercase letters, numbers, and underscores only
                </p>
              </div>

              {/* Prompt Content */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt Content *
                </label>
                
                {/* System Layer Guidance */}
                {createForm.layer === 'system' && (
                  <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-2">💡 Pro Tip: Building Human-Like Personas</h4>
                    <p className="text-sm text-blue-800 mb-3">
                      Use our 6-step professional framework to create authentic, engaging personas:
                    </p>
                    <div className="text-xs text-blue-700 space-y-1">
                      <div><strong>1. Background & Expertise:</strong> Their story, domain knowledge, experiences</div>
                      <div><strong>2. Core Values:</strong> Principles, moral compass, what they care about</div>
                      <div><strong>3. Communication Style:</strong> Tone, speech patterns, emotional range</div>
                      <div><strong>4. Behavioral Traits:</strong> How they think, handle disagreement, focus areas</div>
                      <div><strong>5. Rules of Engagement:</strong> Purpose, always do, never do</div>
                      <div><strong>6. Example Responses:</strong> Show their personality in action</div>
                    </div>
                    <p className="text-xs text-blue-600 mt-2">
                      <strong>Examples:</strong> Check out "alex_hormozi_v2" for a business expert or create your own therapist, teacher, or specialist persona!
                    </p>
                  </div>
                )}
                
                <textarea
                  value={createForm.content}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, content: e.target.value }))}
                  placeholder="Enter your prompt template here..."
                  rows={createForm.layer === 'system' ? 16 : 12}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Use Jinja2 syntax: <code>{'{{variable}}'}</code> for variables, <code>{'{% statement %}'}</code> for logic
                </p>
              </div>

              {/* Commit Message */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Commit Message
                </label>
                <input
                  type="text"
                  value={createForm.commit_message}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, commit_message: e.target.value }))}
                  placeholder="Describe this version..."
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
              <button
                onClick={() => setShowCreateModal(false)}
                disabled={isCreating}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreatePrompt}
                disabled={isCreating || !createForm.name.trim() || !createForm.content.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isCreating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Create Prompt
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
} 