'use client';

import { useState } from 'react';
import { API_URL } from '@/lib/api';

interface Persona {
  id: string;
  name: string;
  description?: string;
  chunks: number;
  created_at?: string;
  source_type?: string;
}

interface PersonaManagerProps {
  personas: Persona[];
  selectedPersona: Persona | null;
  onPersonaSelect: (persona: Persona) => void;
  onPersonaUpdate: (updatedPersona: Persona) => void;
  onPersonaDelete: (personaId: string) => void;
  onShowUpload: () => void;
  onShowMultiUpload?: (personaId: string) => void;
  token: string;
}

interface EditModalProps {
  persona: Persona | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (persona: Persona) => void;
  token: string;
}

interface DeleteModalProps {
  persona: Persona | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isDeleting?: boolean;
}

function EditModal({ persona, isOpen, onClose, onSave, token }: EditModalProps) {
  const [name, setName] = useState(persona?.name || '');
  const [description, setDescription] = useState(persona?.description || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !persona) return null;

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Name is required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/persona/${persona.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
        }),
      });

      if (response.ok) {
        const updatedPersona = { ...persona, name: name.trim(), description: description.trim() || undefined };
        onSave(updatedPersona);
        onClose();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to update persona');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '0.5rem',
        padding: '1.5rem',
        minWidth: '400px',
        maxWidth: '90vw',
      }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem' }}>Edit Persona</h3>
        
        {error && (
          <div style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#dc2626',
            padding: '0.75rem',
            borderRadius: '0.25rem',
            marginBottom: '1rem',
            fontSize: '0.875rem',
          }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.875rem' }}>
            Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && name.trim()) {
                handleSave();
              } else if (e.key === 'Escape') {
                onClose();
              }
            }}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #d1d5db',
              borderRadius: '0.25rem',
              fontSize: '0.875rem',
              outline: 'none',
              transition: 'border-color 0.2s',
            }}
            onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
            onBlur={(e) => e.target.style.borderColor = '#d1d5db'}
            placeholder="Enter persona name"
            autoFocus
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.875rem' }}>
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                onClose();
              }
            }}
            rows={3}
            style={{
              width: '100%',
              padding: '0.5rem',
              border: '1px solid #d1d5db',
              borderRadius: '0.25rem',
              fontSize: '0.875rem',
              resize: 'vertical',
              outline: 'none',
              transition: 'border-color 0.2s',
              fontFamily: 'inherit',
            }}
            onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
            onBlur={(e) => e.target.style.borderColor = '#d1d5db'}
            placeholder="Optional description for this persona (e.g., 'Marketing expert based on company guidelines')"
          />
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            disabled={isLoading}
            style={{
              backgroundColor: '#f3f4f6',
              color: '#374151',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isLoading || !name.trim()}
            style={{
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              cursor: isLoading || !name.trim() ? 'not-allowed' : 'pointer',
              opacity: isLoading || !name.trim() ? 0.7 : 1,
              fontSize: '0.875rem',
            }}
          >
            {isLoading ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}

function DeleteModal({ persona, isOpen, onClose, onConfirm, isDeleting }: DeleteModalProps) {
  if (!isOpen || !persona) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '0.5rem',
        padding: '1.5rem',
        minWidth: '400px',
        maxWidth: '90vw',
      }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.25rem', color: '#dc2626' }}>Delete Persona</h3>
        
        <p style={{ margin: '0 0 1.5rem 0', fontSize: '0.875rem', color: '#374151' }}>
          Are you sure you want to delete <strong>"{persona.name}"</strong>? 
          This will permanently remove all {persona.chunks} knowledge chunks and cannot be undone.
        </p>

        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            disabled={isDeleting}
            style={{
              backgroundColor: '#f3f4f6',
              color: '#374151',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              cursor: isDeleting ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              opacity: isDeleting ? 0.7 : 1,
            }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            style={{
              backgroundColor: '#dc2626',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              cursor: isDeleting ? 'not-allowed' : 'pointer',
              fontSize: '0.875rem',
              opacity: isDeleting ? 0.7 : 1,
            }}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function PersonaManager({
  personas,
  selectedPersona,
  onPersonaSelect,
  onPersonaUpdate,
  onPersonaDelete,
  onShowUpload,
  onShowMultiUpload,
  token,
}: PersonaManagerProps) {
  const [editingPersona, setEditingPersona] = useState<Persona | null>(null);
  const [deletingPersona, setDeletingPersona] = useState<Persona | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [operationInProgress, setOperationInProgress] = useState(false);

  const handleEdit = (persona: Persona, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingPersona(persona);
  };

  const handleDelete = (persona: Persona, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeletingPersona(persona);
  };

  const confirmDelete = async () => {
    if (!deletingPersona) return;

    setIsDeleting(true);
    setOperationInProgress(true);
    try {
      const response = await fetch(`${API_URL}/persona/${deletingPersona.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        onPersonaDelete(deletingPersona.id);
        setDeletingPersona(null);
      } else {
        console.error('Failed to delete persona');
      }
    } catch (error) {
      console.error('Network error during deletion:', error);
    } finally {
      setIsDeleting(false);
      setOperationInProgress(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return '';
    }
  };

  return (
    <div style={{ 
      width: '320px',
      minWidth: '280px',
      maxWidth: '400px',
      backgroundColor: '#f9fafb',
      borderRight: '1px solid #e5e7eb',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      position: 'relative',
    }}>
      {/* Header */}
      <div style={{ 
        padding: '1rem',
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: '#ffffff',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 'bold' }}>Knowledge Bases</h3>
          <span style={{ 
            backgroundColor: '#e5e7eb',
            color: '#374151',
            fontSize: '0.75rem',
            fontWeight: 'bold',
            padding: '0.25rem 0.5rem',
            borderRadius: '0.75rem',
          }}>
            {personas.length}
          </span>
        </div>
        
        <button
          onClick={onShowUpload}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#059669';
            e.currentTarget.style.transform = 'translateY(-1px)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.25)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#10b981';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
          }}
          style={{
            width: '100%',
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            padding: '0.75rem',
            borderRadius: '0.375rem',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontWeight: 'bold',
            transition: 'all 0.2s ease-in-out',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          }}
          aria-label="Create a new persona by uploading documents"
        >
          + Create New Persona
        </button>
      </div>

      {/* Persona List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
        {personas.map(persona => (
          <div
            key={persona.id}
            onClick={() => onPersonaSelect(persona)}
            onMouseEnter={(e) => {
              if (selectedPersona?.id !== persona.id) {
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }
            }}
            onMouseLeave={(e) => {
              if (selectedPersona?.id !== persona.id) {
                e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
                e.currentTarget.style.transform = 'translateY(0)';
              }
            }}
            style={{
              padding: '1rem',
              marginBottom: '0.5rem',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              backgroundColor: selectedPersona?.id === persona.id ? '#dbeafe' : '#ffffff',
              border: selectedPersona?.id === persona.id ? '2px solid #3b82f6' : '1px solid #e5e7eb',
              boxShadow: selectedPersona?.id === persona.id ? '0 4px 12px rgba(59, 130, 246, 0.15)' : '0 1px 3px rgba(0, 0, 0, 0.1)',
              transition: 'all 0.2s ease-in-out',
              position: 'relative',
              transform: selectedPersona?.id === persona.id ? 'translateY(-1px)' : 'translateY(0)',
            }}
          >
            {/* Persona Name */}
            <div style={{ 
              fontWeight: 'bold', 
              fontSize: '0.9rem',
              marginBottom: '0.25rem',
              color: '#1f2937',
            }}>
              {persona.name}
            </div>
            
            {/* Description */}
            {persona.description && (
              <div style={{ 
                fontSize: '0.75rem', 
                color: '#6b7280',
                marginBottom: '0.5rem',
                lineHeight: '1.3',
              }}>
                {persona.description.length > 60 
                  ? persona.description.substring(0, 60) + '...'
                  : persona.description
                }
              </div>
            )}
            
            {/* Stats */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              fontSize: '0.75rem',
              color: '#6b7280',
            }}>
              <span>{persona.chunks} chunks</span>
              {persona.source_type && (
                <span style={{ 
                  backgroundColor: '#f3f4f6',
                  padding: '0.125rem 0.375rem',
                  borderRadius: '0.25rem',
                  textTransform: 'uppercase',
                  fontWeight: 'bold',
                }}>
                  {persona.source_type}
                </span>
              )}
            </div>
            
            {/* Created date */}
            {persona.created_at && (
              <div style={{ 
                fontSize: '0.7rem', 
                color: '#9ca3af',
                marginTop: '0.25rem',
              }}>
                Created {formatDate(persona.created_at)}
              </div>
            )}

            {/* Action buttons */}
            <div style={{
              position: 'absolute',
              top: '0.5rem',
              right: '0.5rem',
              display: 'flex',
              gap: '0.25rem',
              opacity: selectedPersona?.id === persona.id ? 1 : 0.7,
              transition: 'opacity 0.2s',
            }}>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  window.location.href = `/brain/personas/${persona.id}/prompts`;
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#fef3c7'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '0.375rem',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                  color: '#d97706',
                  transition: 'all 0.2s',
                }}
                title="Edit persona prompts and personality"
                aria-label={`Edit prompts for ${persona.name}`}
              >
                🎭
              </button>
              <button
                onClick={(e) => handleEdit(persona, e)}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '0.375rem',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                  color: '#374151',
                  transition: 'all 0.2s',
                }}
                title="Edit persona details"
                aria-label={`Edit ${persona.name}`}
              >
                ✏️
              </button>
              {onShowMultiUpload && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onShowMultiUpload(persona.id);
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  style={{
                    backgroundColor: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '0.375rem',
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem',
                    color: '#059669',
                    transition: 'all 0.2s',
                  }}
                  title="Add more files to this persona"
                  aria-label={`Add files to ${persona.name}`}
                >
                  📁+
                </button>
              )}
              <button
                onClick={(e) => handleDelete(persona, e)}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#fef2f2'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '0.375rem',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                  color: '#dc2626',
                  transition: 'all 0.2s',
                }}
                title="Delete this persona permanently"
                aria-label={`Delete ${persona.name}`}
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
        
        {personas.length === 0 && (
          <div style={{
            textAlign: 'center',
            padding: '3rem 1rem',
            color: '#6b7280',
            fontSize: '0.875rem',
          }}>
            <div style={{ 
              fontSize: '3rem', 
              marginBottom: '1rem',
              opacity: 0.8,
            }}>
              🧠
            </div>
            <h3 style={{ 
              margin: '0 0 0.5rem 0',
              color: '#374151',
              fontSize: '1rem',
              fontWeight: 'bold',
            }}>
              No AI Personas Yet
            </h3>
            <p style={{ 
              margin: '0 0 1rem 0',
              lineHeight: '1.4',
            }}>
              Upload documents to create your first AI expert persona
            </p>
            <div style={{
              backgroundColor: '#f0f9ff',
              border: '1px solid #bae6fd',
              borderRadius: '0.375rem',
              padding: '0.75rem',
              fontSize: '0.75rem',
              color: '#0369a1',
              lineHeight: '1.3',
            }}>
              💡 Tip: Each persona becomes an expert on the documents you upload
            </div>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      <EditModal
        persona={editingPersona}
        isOpen={!!editingPersona}
        onClose={() => setEditingPersona(null)}
        onSave={(updatedPersona) => {
          onPersonaUpdate(updatedPersona);
          setEditingPersona(null);
        }}
        token={token}
      />

      {/* Delete Modal */}
      <DeleteModal
        persona={deletingPersona}
        isOpen={!!deletingPersona}
        onClose={() => setDeletingPersona(null)}
        onConfirm={confirmDelete}
        isDeleting={isDeleting}
      />
    </div>
  );
} 