/**
 * Audio Stream Handler for ElevenLabs Voice Streaming
 * Handles audio/mpeg streams from backend with MediaSource API
 */

export interface AudioStreamConfig {
  onLoadStart?: () => void;
  onCanPlay?: () => void;
  onError?: (error: string) => void;
  onEnded?: () => void;
}

export class AudioStreamHandler {
  private audio: HTMLAudioElement;
  private mediaSource: MediaSource | null = null;
  private sourceBuffer: SourceBuffer | null = null;
  private chunks: Uint8Array[] = [];
  private isInitialized = false;

  constructor(private config: AudioStreamConfig = {}) {
    this.audio = new Audio();
    this.setupAudioElement();
  }

  private setupAudioElement() {
    this.audio.addEventListener('loadstart', () => {
      this.config.onLoadStart?.();
    });

    this.audio.addEventListener('canplay', () => {
      this.config.onCanPlay?.();
    });

    this.audio.addEventListener('error', (e) => {
      const errorMsg = `Audio error: ${this.audio.error?.message || 'Unknown error'}`;
      console.error('[AudioStreamHandler]', errorMsg);
      this.config.onError?.(errorMsg);
    });

    this.audio.addEventListener('ended', () => {
      this.config.onEnded?.();
      this.cleanup();
    });
  }

  async createMediaSource(): Promise<boolean> {
    try {
      if (!MediaSource.isTypeSupported('audio/mpeg')) {
        throw new Error('audio/mpeg not supported');
      }

      this.mediaSource = new MediaSource();
      this.audio.src = URL.createObjectURL(this.mediaSource);

      return new Promise((resolve, reject) => {
        if (!this.mediaSource) {
          reject(new Error('MediaSource creation failed'));
          return;
        }

        this.mediaSource.addEventListener('sourceopen', () => {
          try {
            if (!this.mediaSource) {
              reject(new Error('MediaSource not available'));
              return;
            }

            this.sourceBuffer = this.mediaSource.addSourceBuffer('audio/mpeg');
            this.sourceBuffer.addEventListener('updateend', () => {
              this.processNextChunk();
            });

            this.isInitialized = true;
            resolve(true);
          } catch (error) {
            reject(error);
          }
        });

        this.mediaSource.addEventListener('error', (e) => {
          reject(new Error('MediaSource error'));
        });
      });
    } catch (error) {
      console.error('[AudioStreamHandler] MediaSource setup failed:', error);
      this.config.onError?.(`MediaSource setup failed: ${error}`);
      return false;
    }
  }

  appendAudioChunk(chunk: Uint8Array): void {
    if (!this.isInitialized || !this.sourceBuffer) {
      console.warn('[AudioStreamHandler] Not initialized, queueing chunk');
      this.chunks.push(chunk);
      return;
    }

    this.chunks.push(chunk);
    this.processNextChunk();
  }

  private processNextChunk(): void {
    if (!this.sourceBuffer || this.sourceBuffer.updating || this.chunks.length === 0) {
      return;
    }

    const chunk = this.chunks.shift();
    if (chunk) {
      try {
        this.sourceBuffer.appendBuffer(chunk);
      } catch (error) {
        console.error('[AudioStreamHandler] Error appending buffer:', error);
        this.config.onError?.(`Buffer append error: ${error}`);
      }
    }
  }

  async play(): Promise<void> {
    try {
      await this.audio.play();
    } catch (error) {
      console.error('[AudioStreamHandler] Play failed:', error);
      this.config.onError?.(`Playback failed: ${error}`);
      throw error;
    }
  }

  pause(): void {
    this.audio.pause();
  }

  stop(): void {
    this.audio.pause();
    this.audio.currentTime = 0;
    this.cleanup();
  }

  get isPlaying(): boolean {
    return !this.audio.paused && !this.audio.ended;
  }

  get isPaused(): boolean {
    return this.audio.paused;
  }

  get duration(): number {
    return this.audio.duration || 0;
  }

  get currentTime(): number {
    return this.audio.currentTime;
  }

  private cleanup(): void {
    // Clear remaining chunks
    this.chunks = [];

    // Close MediaSource
    if (this.mediaSource && this.mediaSource.readyState === 'open') {
      try {
        this.mediaSource.endOfStream();
      } catch (error) {
        console.warn('[AudioStreamHandler] Error ending stream:', error);
      }
    }

    // Reset state
    this.isInitialized = false;
    this.sourceBuffer = null;
  }

  destroy(): void {
    this.stop();
    this.audio.removeEventListener('loadstart', () => {});
    this.audio.removeEventListener('canplay', () => {});
    this.audio.removeEventListener('error', () => {});
    this.audio.removeEventListener('ended', () => {});
    
    if (this.audio.src) {
      URL.revokeObjectURL(this.audio.src);
    }
  }
}

/**
 * Simple fallback audio player for basic audio/mpeg files
 * Used when MediaSource API fails
 */
export class SimpleAudioPlayer {
  private audio: HTMLAudioElement;

  constructor(private config: AudioStreamConfig = {}) {
    this.audio = new Audio();
    this.setupAudioElement();
  }

  private setupAudioElement() {
    this.audio.addEventListener('loadstart', () => {
      this.config.onLoadStart?.();
    });

    this.audio.addEventListener('canplay', () => {
      this.config.onCanPlay?.();
    });

    this.audio.addEventListener('error', (e) => {
      const errorMsg = `Audio error: ${this.audio.error?.message || 'Unknown error'}`;
      this.config.onError?.(errorMsg);
    });

    this.audio.addEventListener('ended', () => {
      this.config.onEnded?.();
    });
  }

  async playFromBlob(audioData: Uint8Array): Promise<void> {
    const blob = new Blob([audioData], { type: 'audio/mpeg' });
    const url = URL.createObjectURL(blob);
    
    try {
      this.audio.src = url;
      await this.audio.play();
    } catch (error) {
      URL.revokeObjectURL(url);
      throw error;
    }
  }

  stop(): void {
    this.audio.pause();
    this.audio.currentTime = 0;
    if (this.audio.src) {
      URL.revokeObjectURL(this.audio.src);
      this.audio.src = '';
    }
  }

  get isPlaying(): boolean {
    return !this.audio.paused && !this.audio.ended;
  }
} 