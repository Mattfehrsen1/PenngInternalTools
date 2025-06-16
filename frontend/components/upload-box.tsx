'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { api, API_URL } from '../lib/api';

interface UploadBoxProps {
  onUploadComplete: (personaId: string) => void;
}

export function UploadBox({ onUploadComplete }: UploadBoxProps) {
  const [uploadMode, setUploadMode] = useState<'file' | 'text'>('file');
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [text, setText] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      setFile(file);
      setError('');
      // Auto-generate name from filename
      const nameFromFile = file.name.replace(/\.[^/.]+$/, '');
      setName(nameFromFile);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  const handleUpload = async () => {
    if (!name.trim()) {
      setError('Please provide a name for the clone');
      return;
    }

    if (uploadMode === 'file' && !file) {
      setError('Please select a PDF file');
      return;
    }

    if (uploadMode === 'text' && !text.trim()) {
      setError('Please enter some text');
      return;
    }

    setError('');
    setUploading(true);
    setProgress(20);

    try {
      const response = await fetch(`${API_URL}/persona/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          description,
          file: uploadMode === 'file' ? file : undefined,
          text: uploadMode === 'text' ? text : undefined,
        }),
      });

      const data = await response.json();

      setProgress(100);
      onUploadComplete(data.persona_id);
      
      // Reset form
      setFile(null);
      setName('');
      setDescription('');
      setText('');
      setProgress(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardContent className="p-6">
        <div className="space-y-4">
          <div className="flex gap-2 mb-4">
            <Button
              variant={uploadMode === 'file' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setUploadMode('file')}
              disabled={uploading}
            >
              <FileText className="mr-2 h-4 w-4" />
              Upload PDF
            </Button>
            <Button
              variant={uploadMode === 'text' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setUploadMode('text')}
              disabled={uploading}
            >
              <FileText className="mr-2 h-4 w-4" />
              Paste Text
            </Button>
          </div>

          {uploadMode === 'file' ? (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
              } ${uploading ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary'}`}
            >
              <input {...getInputProps()} />
              <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              {file ? (
                <div>
                  <p className="text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-sm text-muted-foreground">
                    {isDragActive
                      ? 'Drop your PDF here'
                      : 'Drag & drop a PDF here, or click to select'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Maximum file size: 10MB
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="text">Paste your text</Label>
              <Textarea
                id="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste or type your text here..."
                rows={8}
                disabled={uploading}
              />
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="name">Clone Name *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Alex Hormozi Book"
              disabled={uploading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (optional)</Label>
            <Input
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the content"
              disabled={uploading}
            />
          </div>

          {error && (
            <div className="text-sm text-destructive">{error}</div>
          )}

          {uploading && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-sm text-muted-foreground text-center">
                Processing your {uploadMode === 'file' ? 'PDF' : 'text'}...
              </p>
            </div>
          )}

          <Button
            onClick={handleUpload}
            disabled={uploading || (!file && uploadMode === 'file') || (!text && uploadMode === 'text')}
            className="w-full"
          >
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              'Create Clone'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
