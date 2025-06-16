'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
// Removed Monaco editor - using simple textarea instead

// Import other components
import VersionHistory from '@/components/prompts/VersionHistory';
import PromptSelector from '@/components/prompts/PromptSelector';
import PromptPlayground from '@/components/prompts/PromptPlayground';

interface PromptVersion {
  id: string;
  layer: string;
  name: string;
  content: string;
  version: number;
  is_active: boolean;
  author_id: string;
  commit_message?: string;
  persona_id?: string;
  created_at: string;
  updated_at: string;
}

interface SelectedPrompt {
  layer: string;
  name: string;
}

export default function PromptControlCenter() {
  const router = useRouter();
  const [token, setToken] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  
  // Prompt state
  const [selectedPrompt, setSelectedPrompt] = useState<SelectedPrompt | null>(null);
  const [currentContent, setCurrentContent] = useState<string>('');
  const [versions, setVersions] = useState<PromptVersion[]>([]);
  const [activeVersion, setActiveVersion] = useState<PromptVersion | null>(null);
  const [isEditorDirty, setIsEditorDirty] = useState(false);
  const [showPlayground, setShowPlayground] = useState(false);

  // Check authentication
  useEffect(() => {
    console.log('🔧 Prompt Control Center: Checking authentication...');
    
    try {
      const storedToken = localStorage.getItem('auth_token');
      
      if (!storedToken) {
        console.log('❌ No token found, redirecting to login');
        router.push('/login');
        return;
      }
      
      setToken(storedToken);
    } catch (error) {
      console.error('❌ Error checking auth:', error);
      router.push('/login');
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  // Load prompt versions when selection changes
  useEffect(() => {
    if (selectedPrompt && token) {
      fetchVersionHistory();
    }
  }, [selectedPrompt, token]);

  const fetchVersionHistory = async () => {
    if (!selectedPrompt || !token) return;

    try {
      const response = await fetch(
        `/api/prompts/${selectedPrompt.layer}/${selectedPrompt.name}/versions`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setVersions(data.versions || []);
        setActiveVersion(data.active_version || null);
        
        // Set editor content to active version or latest version
        const contentToShow = data.active_version?.content || 
                            (data.versions.length > 0 ? data.versions[0].content : '');
        setCurrentContent(contentToShow);
        setIsEditorDirty(false);
      } else {
        console.error('Failed to fetch version history:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching version history:', error);
    }
  };

  const handleSaveVersion = async (commitMessage?: string) => {
    if (!selectedPrompt || !token || !currentContent) return;

    try {
      const response = await fetch(
        `/api/prompts/${selectedPrompt.layer}/${selectedPrompt.name}/versions`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content: currentContent,
            commit_message: commitMessage || 'Updated prompt',
          }),
        }
      );

      if (response.ok) {
        const newVersion = await response.json();
        console.log('✅ Version saved:', newVersion);
        
        // Refresh version history
        await fetchVersionHistory();
        setIsEditorDirty(false);
      } else {
        console.error('Failed to save version:', response.statusText);
      }
    } catch (error) {
      console.error('Error saving version:', error);
    }
  };

  const handleActivateVersion = async (versionId: string) => {
    if (!token) return;

    try {
      const response = await fetch(`/api/prompts/${versionId}/activate`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        console.log('✅ Version activated');
        await fetchVersionHistory();
      } else {
        console.error('Failed to activate version:', response.statusText);
      }
    } catch (error) {
      console.error('Error activating version:', error);
    }
  };

  const handleEditorChange = (value: string) => {
    setCurrentContent(value);
    
    // Check if content has changed from active version
    const activeContent = activeVersion?.content || '';
    setIsEditorDirty(value !== activeContent);
  };

  const handleKeyboardShortcut = (e: KeyboardEvent) => {
    // Cmd+S / Ctrl+S to save
    if ((e.metaKey || e.ctrlKey) && e.key === 's') {
      e.preventDefault();
      if (isEditorDirty) {
        handleSaveVersion();
      }
    }
  };

  useEffect(() => {
    document.addEventListener('keydown', handleKeyboardShortcut);
    
    return () => {
      document.removeEventListener('keydown', handleKeyboardShortcut);
    };
  }, [isEditorDirty]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Prompt Control Center...</p>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <p className="text-gray-600">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">🔧 Prompt Control Center</h1>
            <p className="text-sm text-gray-600 mt-1">
              Visual prompt engineering with version control and testing
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Dirty state indicator */}
            {isEditorDirty && (
              <div className="flex items-center text-amber-600">
                <div className="w-2 h-2 bg-amber-500 rounded-full mr-2"></div>
                <span className="text-sm">Unsaved changes</span>
              </div>
            )}
            
            {/* Save button */}
            <button
              onClick={() => handleSaveVersion()}
              disabled={!isEditorDirty || !selectedPrompt}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save Version
            </button>
            
            {/* Playground toggle */}
            <button
              onClick={() => setShowPlayground(!showPlayground)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700"
            >
              {showPlayground ? 'Hide' : 'Show'} Playground
            </button>
          </div>
        </div>
      </div>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Prompt Selector */}
        <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">Prompts</h2>
            <p className="text-sm text-gray-600">Select a prompt to edit</p>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            <PromptSelector
              selectedPrompt={selectedPrompt}
              onSelectPrompt={setSelectedPrompt}
              token={token}
            />
          </div>
        </div>

        {/* Center - Monaco Editor */}
        <div className="flex-1 flex flex-col">
          {selectedPrompt ? (
            <>
              {/* Editor toolbar */}
              <div className="bg-gray-100 px-4 py-2 border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium text-gray-700">
                    {selectedPrompt.layer.toUpperCase()} / {selectedPrompt.name}
                  </span>
                  {activeVersion && (
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                      Active: v{activeVersion.version}
                    </span>
                  )}
                </div>
                
                <div className="text-xs text-gray-500">
                  Cmd+S to save • Jinja2 syntax supported
                </div>
              </div>
              
              {/* Simple Text Editor */}
              <div className="flex-1 p-4">
                <textarea
                  value={currentContent}
                  onChange={(e) => handleEditorChange(e.target.value)}
                  className="w-full h-full border border-gray-300 rounded-lg p-4 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your prompt content here..."
                />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Prompt</h3>
                <p className="text-gray-600">Choose a prompt from the sidebar to start editing</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar - Version History */}
        <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">Version History</h2>
            <p className="text-sm text-gray-600">Manage prompt versions</p>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {selectedPrompt ? (
              <VersionHistory
                versions={versions}
                activeVersion={activeVersion}
                onActivateVersion={handleActivateVersion}
                onSelectVersion={(version: PromptVersion) => {
                  setCurrentContent(version.content);
                  setIsEditorDirty(version.content !== (activeVersion?.content || ''));
                }}
              />
            ) : (
              <div className="p-4 text-center text-gray-500">
                <p>Select a prompt to view versions</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Playground Modal */}
      {showPlayground && selectedPrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <PromptPlayground
              layer={selectedPrompt.layer}
              name={selectedPrompt.name}
              content={currentContent}
              token={token}
              onClose={() => setShowPlayground(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
} 