const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

console.log('🔧 API_URL configured as:', API_URL);

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface PersonaUploadResponse {
  persona_id: string;
  name: string;
  namespace: string;
  chunks: number;
  message: string;
}

export interface Persona {
  id: string;
  name: string;
  description?: string;
  source_type: string;
  chunk_count: number;
  created_at: string;
  ready?: boolean;
}

export interface Citation {
  id: number;
  text: string;
  source: string;
  score: number;
}

class ApiClient {
  private token: string | null = null;

  constructor() {
    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async login(username: string, password: string): Promise<LoginResponse> {
    console.log('🌐 API.login called with:', { username, password: password.substring(0, 3) + '...' });
    
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    console.log('📡 Making request to:', `${API_URL}/auth/login`);
    
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        body: formData,
      });

      console.log('📨 Response status:', response.status);
      console.log('📨 Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Response error text:', errorText);
        throw new Error(`Login failed: ${response.status} - ${errorText}`);
      }

      const data: LoginResponse = await response.json();
      console.log('✅ Login response data:', { access_token: data.access_token.substring(0, 20) + '...', token_type: data.token_type });
      this.setToken(data.access_token);
      return data;
    } catch (error) {
      console.error('🚨 Fetch error in API.login:', error);
      throw error;
    }
  }

  async uploadPersona(
    name: string,
    description: string,
    file?: File,
    text?: string
  ): Promise<PersonaUploadResponse> {
    const formData = new FormData();
    formData.append('name', name);
    if (description) {
      formData.append('description', description);
    }
    if (file) {
      formData.append('file', file);
    }
    if (text) {
      formData.append('text', text);
    }

    const response = await fetch(`${API_URL}/persona/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Upload failed');
    }

    return response.json();
  }

  async listPersonas(): Promise<{ personas: Persona[] }> {
    const response = await fetch(`${API_URL}/persona/list`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch personas');
    }

    return response.json();
  }

  async getPersona(personaId: string): Promise<Persona> {
    const response = await fetch(`${API_URL}/persona/${personaId}`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch persona');
    }

    return response.json();
  }

  streamChat(
    personaId: string,
    question: string,
    model: string = 'auto',
    k: number = 6,
    onMessage: (event: string, data: any) => void,
    onError: (error: string) => void
  ): void {
    // Use fetch with POST instead of EventSource
    fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        persona_id: personaId,
        question,
        model,
        k,
      }),
    }).then(response => {
      if (!response.ok) {
        throw new Error('Chat request failed');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      async function readStream() {
        if (!reader) return;

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              if (buffer.trim()) {
                // Process any remaining data
                processLine(buffer);
              }
              break;
            }

            const text = decoder.decode(value, { stream: true });
            buffer += text;
            
            // Process complete lines
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer
            
            for (const line of lines) {
              processLine(line);
            }
          }
        } catch (error) {
          onError(error instanceof Error ? error.message : 'Stream error');
        }
      }

      function processLine(line: string) {
        const trimmedLine = line.trim();
        if (!trimmedLine || trimmedLine === '') return;
        
        if (trimmedLine.startsWith('event:')) {
          const event = trimmedLine.substring(6).trim();
          return; // Store event for next data line
        }
        
        if (trimmedLine.startsWith('data:')) {
          const dataStr = trimmedLine.substring(5).trim();
          if (dataStr === '[DONE]') {
            onMessage('done', {});
            return;
          }
          
          try {
            const data = JSON.parse(dataStr);
            // Determine event type from data structure
            if ('token' in data) {
              onMessage('token', data);
            } else if ('citations' in data) {
              onMessage('citations', data);
            } else if ('error' in data) {
              onMessage('error', data);
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e);
          }
        }
      }

      readStream();
    }).catch(error => {
      onError(error.message);
    });
  }
}

export const api = new ApiClient();
