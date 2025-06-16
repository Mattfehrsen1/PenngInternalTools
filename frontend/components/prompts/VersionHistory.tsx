'use client';

import { useState } from 'react';

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

interface VersionHistoryProps {
  versions: PromptVersion[];
  activeVersion: PromptVersion | null;
  onActivateVersion: (versionId: string) => void;
  onSelectVersion: (version: PromptVersion) => void;
}

export default function VersionHistory({
  versions,
  activeVersion,
  onActivateVersion,
  onSelectVersion
}: VersionHistoryProps) {
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getVersionStatus = (version: PromptVersion) => {
    if (version.is_active) return 'active';
    if (selectedVersionId === version.id) return 'selected';
    return 'default';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'selected':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };

  const handleVersionClick = (version: PromptVersion) => {
    setSelectedVersionId(version.id);
    onSelectVersion(version);
  };

  const handleActivateClick = (e: React.MouseEvent, versionId: string) => {
    e.stopPropagation(); // Prevent version selection when clicking activate
    onActivateVersion(versionId);
  };

  if (versions.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
        </svg>
        <h3 className="text-sm font-medium text-gray-900 mb-1">No Versions Yet</h3>
        <p className="text-sm text-gray-500">
          Create your first version by editing the prompt and saving.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-4">
      {/* Active Version Header */}
      {activeVersion && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-green-800">Active Version</span>
              <p className="text-xs text-green-600 mt-1">Currently deployed</p>
            </div>
            <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
              v{activeVersion.version}
            </span>
          </div>
        </div>
      )}

      {/* Version List */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Version History</h3>
        
        {versions.map((version) => {
          const status = getVersionStatus(version);
          const statusColor = getStatusColor(status);
          
          return (
            <div
              key={version.id}
              onClick={() => handleVersionClick(version)}
              className={`border rounded-lg p-3 cursor-pointer transition-all hover:shadow-sm ${
                selectedVersionId === version.id
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              {/* Version Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${statusColor}`}>
                    v{version.version}
                  </span>
                  {version.is_active && (
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                      Active
                    </span>
                  )}
                </div>
                
                {!version.is_active && (
                  <button
                    onClick={(e) => handleActivateClick(e, version.id)}
                    className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 transition-colors"
                  >
                    Activate
                  </button>
                )}
              </div>

              {/* Commit Message */}
              {version.commit_message && (
                <p className="text-sm text-gray-700 mb-2 font-medium">
                  {version.commit_message}
                </p>
              )}

              {/* Content Preview */}
              <div className="bg-gray-50 rounded border p-2 mb-2">
                <p className="text-xs text-gray-600 font-mono leading-relaxed">
                  {version.content.length > 120 
                    ? `${version.content.substring(0, 120)}...`
                    : version.content
                  }
                </p>
              </div>

              {/* Metadata */}
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Created {formatDate(version.created_at)}</span>
                <div className="flex items-center space-x-2">
                  <span>Author: {version.author_id.substring(0, 8)}</span>
                  {selectedVersionId === version.id && (
                    <span className="text-blue-600 font-medium">← Viewing</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Actions */}
      <div className="pt-4 border-t border-gray-200 space-y-2">
        <button
          onClick={() => {
            // TODO: Implement diff view functionality
            console.log('Compare versions clicked');
          }}
          disabled={versions.length < 2}
          className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg text-sm font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Compare Versions
        </button>
        
        <button
          onClick={() => {
            // TODO: Implement export functionality
            console.log('Export history clicked');
          }}
          className="w-full bg-white border border-gray-300 text-gray-700 py-2 px-4 rounded-lg text-sm font-medium hover:bg-gray-50"
        >
          Export History
        </button>
      </div>

      {/* Quick Stats */}
      <div className="bg-gray-50 rounded-lg p-3 text-center">
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <div className="font-medium text-gray-900">{versions.length}</div>
            <div className="text-gray-500">Total Versions</div>
          </div>
          <div>
            <div className="font-medium text-gray-900">
              {activeVersion ? `v${activeVersion.version}` : 'None'}
            </div>
            <div className="text-gray-500">Active Version</div>
          </div>
        </div>
      </div>
    </div>
  );
} 