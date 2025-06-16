import { useCallback, useRef, useState, useEffect } from 'react';
import { AudioStreamHandler, SimpleAudioPlayer } from '../audio/streamHandler';

export type AudioState = 'idle' | 'loading' | 'playing' | 'paused' | 'error';

export interface UseAudioStreamReturn {
  state: AudioState;
  error: string | null;
  isPlaying: boolean;
  playText: (text: string, personaId: string, token: string) => Promise<void>;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  cleanup: () => void;
}

export function useAudioStream(): UseAudioStreamReturn {
  const [state, setState] = useState<AudioState>('idle');
  const [error, setError] = useState<string | null>(null);
  
  const audioHandlerRef = useRef<AudioStreamHandler | null>(null);
  const fallbackPlayerRef = useRef<SimpleAudioPlayer | null>(null);
  const currentRequestRef = useRef<AbortController | null>(null);

  // Create audio handler with callbacks
  const createAudioHandler = useCallback(() => {
    return new AudioStreamHandler({
      onLoadStart: () => {
        console.log('[useAudioStream] Audio loading started');
      },
      onCanPlay: () => {
        console.log('[useAudioStream] Audio can play');
        setState('playing');
      },
      onError: (errorMsg) => {
        console.error('[useAudioStream] Audio error:', errorMsg);
        setState('error');
        setError(errorMsg);
      },
      onEnded: () => {
        console.log('[useAudioStream] Audio ended');
        setState('idle');
        setError(null);
      }
    });
  }, []);

  // Create fallback player
  const createFallbackPlayer = useCallback(() => {
    return new SimpleAudioPlayer({
      onLoadStart: () => setState('loading'),
      onCanPlay: () => setState('playing'),
      onError: (errorMsg) => {
        setState('error');
        setError(errorMsg);
      },
      onEnded: () => {
        setState('idle');
        setError(null);
      }
    });
  }, []);

  const playText = useCallback(async (text: string, personaId: string, token: string) => {
    // Abort any ongoing request
    if (currentRequestRef.current) {
      currentRequestRef.current.abort();
    }

    // Stop any currently playing audio
    if (audioHandlerRef.current) {
      audioHandlerRef.current.stop();
    }
    if (fallbackPlayerRef.current) {
      fallbackPlayerRef.current.stop();
    }

    setState('loading');
    setError(null);

    // Create new abort controller for this request
    const abortController = new AbortController();
    currentRequestRef.current = abortController;

    try {
      console.log(`[useAudioStream] Starting voice generation for persona ${personaId}`);
      
      // Use the working endpoint that tests Redis caching performance
      const response = await fetch(`/api/personas/${personaId}/voice/stream-simple`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text.trim() }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Voice API error (${response.status}): ${errorText}`);
      }

      const contentType = response.headers.get('content-type');
      console.log('[useAudioStream] Response content-type:', contentType);

      if (contentType?.includes('audio/mpeg')) {
        // Try streaming approach first
        await handleStreamingAudio(response, abortController);
      } else {
        // Fallback to complete audio blob
        await handleCompleteAudio(response, abortController);
      }

    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('[useAudioStream] Request aborted');
        setState('idle');
        return;
      }
      
      console.error('[useAudioStream] Voice generation failed:', error);
      setState('error');
      setError(error.message || 'Voice generation failed');
    } finally {
      currentRequestRef.current = null;
    }
  }, []);

  const handleStreamingAudio = async (response: Response, abortController: AbortController) => {
    // Create and initialize audio handler
    const handler = createAudioHandler();
    audioHandlerRef.current = handler;

    const initialized = await handler.createMediaSource();
    if (!initialized) {
      throw new Error('Failed to initialize audio streaming');
    }

    // Start reading the stream
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body for streaming');
    }

    try {
      let firstChunk = true;
      
      while (!abortController.signal.aborted) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('[useAudioStream] Stream complete');
          break;
        }

        if (value && value.length > 0) {
          handler.appendAudioChunk(value);
          
          // Start playback after first chunk
          if (firstChunk) {
            console.log('[useAudioStream] Starting playback with first chunk');
            // Small delay to ensure buffer has some data
            setTimeout(() => {
              if (!abortController.signal.aborted) {
                handler.play().catch(error => {
                  console.error('[useAudioStream] Initial play failed:', error);
                  setState('error');
                  setError('Playback failed');
                });
              }
            }, 100);
            firstChunk = false;
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  };

  const handleCompleteAudio = async (response: Response, abortController: AbortController) => {
    console.log('[useAudioStream] Using fallback complete audio approach');
    
    const arrayBuffer = await response.arrayBuffer();
    if (abortController.signal.aborted) return;

    const audioData = new Uint8Array(arrayBuffer);
    
    const fallbackPlayer = createFallbackPlayer();
    fallbackPlayerRef.current = fallbackPlayer;

    await fallbackPlayer.playFromBlob(audioData);
  };

  const stop = useCallback(() => {
    if (currentRequestRef.current) {
      currentRequestRef.current.abort();
    }
    
    if (audioHandlerRef.current) {
      audioHandlerRef.current.stop();
    }
    
    if (fallbackPlayerRef.current) {
      fallbackPlayerRef.current.stop();
    }
    
    setState('idle');
    setError(null);
  }, []);

  const pause = useCallback(() => {
    if (audioHandlerRef.current && audioHandlerRef.current.isPlaying) {
      audioHandlerRef.current.pause();
      setState('paused');
    }
  }, []);

  const resume = useCallback(() => {
    if (audioHandlerRef.current && audioHandlerRef.current.isPaused) {
      audioHandlerRef.current.play().then(() => {
        setState('playing');
      }).catch(error => {
        setState('error');
        setError(`Resume failed: ${error.message}`);
      });
    }
  }, []);

  const cleanup = useCallback(() => {
    stop();
    
    if (audioHandlerRef.current) {
      audioHandlerRef.current.destroy();
      audioHandlerRef.current = null;
    }
    
    fallbackPlayerRef.current = null;
  }, [stop]);

  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  return {
    state,
    error,
    isPlaying: state === 'playing',
    playText,
    stop,
    pause,
    resume,
    cleanup,
  };
} 