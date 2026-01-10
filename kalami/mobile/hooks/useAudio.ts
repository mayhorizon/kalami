// Custom hook for audio recording and playback using expo-av
import { useState, useEffect, useRef, useCallback } from 'react';
import { Audio, AVPlaybackStatus } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import { Platform } from 'react-native';
import { AudioRecordingState, AudioPlaybackState } from '@/types';

interface UseAudioOptions {
  onRecordingComplete?: (uri: string) => void;
  onPlaybackComplete?: () => void;
  onError?: (error: Error) => void;
}

interface UseAudioReturn {
  recording: AudioRecordingState;
  playback: AudioPlaybackState;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string | undefined>;
  pauseRecording: () => Promise<void>;
  resumeRecording: () => Promise<void>;
  playAudio: (uri: string) => Promise<void>;
  playAudioFromBase64: (base64: string, format?: string) => Promise<void>;
  stopPlayback: () => Promise<void>;
  pausePlayback: () => Promise<void>;
  resumePlayback: () => Promise<void>;
  getAudioBase64: (uri: string) => Promise<string>;
  clearRecording: () => Promise<void>;
}

export function useAudio(options: UseAudioOptions = {}): UseAudioReturn {
  const [recording, setRecording] = useState<AudioRecordingState>({
    isRecording: false,
    isPaused: false,
    duration: 0,
    uri: undefined,
  });

  const [playback, setPlayback] = useState<AudioPlaybackState>({
    isPlaying: false,
    isLoaded: false,
    duration: 0,
    position: 0,
  });

  const recordingRef = useRef<Audio.Recording | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Request audio permissions and configure audio mode
  useEffect(() => {
    const setupAudio = async () => {
      try {
        const permission = await Audio.requestPermissionsAsync();

        if (!permission.granted) {
          options.onError?.(new Error('Audio permission not granted'));
          return;
        }

        await Audio.setAudioModeAsync({
          allowsRecordingIOS: true,
          playsInSilentModeIOS: true,
          playThroughEarpieceAndroid: false,
          staysActiveInBackground: false,
        });
      } catch (error) {
        console.error('Failed to setup audio:', error);
        options.onError?.(error as Error);
      }
    };

    setupAudio();

    return () => {
      // Cleanup on unmount
      if (recordingRef.current) {
        recordingRef.current.stopAndUnloadAsync().catch(console.error);
      }
      if (soundRef.current) {
        soundRef.current.unloadAsync().catch(console.error);
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, []);

  // Recording functions
  const startRecording = useCallback(async () => {
    try {
      // Stop any existing recording
      if (recordingRef.current) {
        await recordingRef.current.stopAndUnloadAsync();
      }

      // Create new recording with 16kHz sample rate for optimal STT
      const { recording: newRecording } = await Audio.Recording.createAsync(
        {
          android: {
            extension: '.m4a',
            outputFormat: Audio.AndroidOutputFormat.MPEG_4,
            audioEncoder: Audio.AndroidAudioEncoder.AAC,
            sampleRate: 16000,
            numberOfChannels: 1,
            bitRate: 128000,
          },
          ios: {
            extension: '.m4a',
            outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
            audioQuality: Audio.IOSAudioQuality.HIGH,
            sampleRate: 16000,
            numberOfChannels: 1,
            bitRate: 128000,
            linearPCMBitDepth: 16,
            linearPCMIsBigEndian: false,
            linearPCMIsFloat: false,
          },
          web: {
            mimeType: 'audio/webm',
            bitsPerSecond: 128000,
          },
        },
        (status) => {
          // Update duration during recording
          if (status.isRecording && status.durationMillis) {
            setRecording(prev => ({
              ...prev,
              duration: Math.floor(status.durationMillis / 1000),
            }));
          }
        }
      );

      recordingRef.current = newRecording;

      setRecording({
        isRecording: true,
        isPaused: false,
        duration: 0,
        uri: undefined,
      });
    } catch (error) {
      console.error('Failed to start recording:', error);
      options.onError?.(error as Error);
      throw error;
    }
  }, [options]);

  const stopRecording = useCallback(async (): Promise<string | undefined> => {
    try {
      if (!recordingRef.current) {
        return undefined;
      }

      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI() ?? undefined;
      recordingRef.current = null;

      setRecording(prev => ({
        ...prev,
        isRecording: false,
        isPaused: false,
        uri,
      }));

      if (uri) {
        options.onRecordingComplete?.(uri);
      }

      return uri;
    } catch (error) {
      console.error('Failed to stop recording:', error);
      options.onError?.(error as Error);
      throw error;
    }
  }, [options]);

  const pauseRecording = useCallback(async () => {
    try {
      if (recordingRef.current) {
        await recordingRef.current.pauseAsync();
        setRecording(prev => ({ ...prev, isPaused: true }));
      }
    } catch (error) {
      console.error('Failed to pause recording:', error);
      options.onError?.(error as Error);
    }
  }, [options]);

  const resumeRecording = useCallback(async () => {
    try {
      if (recordingRef.current) {
        await recordingRef.current.startAsync();
        setRecording(prev => ({ ...prev, isPaused: false }));
      }
    } catch (error) {
      console.error('Failed to resume recording:', error);
      options.onError?.(error as Error);
    }
  }, [options]);

  // Playback functions
  const playAudio = useCallback(async (uri: string) => {
    try {
      // Unload previous sound
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
      }

      const { sound } = await Audio.Sound.createAsync(
        { uri },
        { shouldPlay: true },
        (status: AVPlaybackStatus) => {
          if (status.isLoaded) {
            setPlayback({
              isPlaying: status.isPlaying,
              isLoaded: true,
              duration: status.durationMillis ? Math.floor(status.durationMillis / 1000) : 0,
              position: status.positionMillis ? Math.floor(status.positionMillis / 1000) : 0,
            });

            if (status.didJustFinish) {
              options.onPlaybackComplete?.();
            }
          }
        }
      );

      soundRef.current = sound;
      await sound.playAsync();
    } catch (error) {
      console.error('Failed to play audio:', error);
      options.onError?.(error as Error);
      throw error;
    }
  }, [options]);

  const playAudioFromBase64 = useCallback(async (base64: string, format: string = 'm4a') => {
    try {
      // Write base64 to temporary file
      const tempUri = `${FileSystem.cacheDirectory}temp_audio.${format}`;
      await FileSystem.writeAsStringAsync(tempUri, base64, {
        encoding: FileSystem.EncodingType.Base64,
      });

      await playAudio(tempUri);
    } catch (error) {
      console.error('Failed to play audio from base64:', error);
      options.onError?.(error as Error);
      throw error;
    }
  }, [playAudio, options]);

  const stopPlayback = useCallback(async () => {
    try {
      if (soundRef.current) {
        await soundRef.current.stopAsync();
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }

      setPlayback({
        isPlaying: false,
        isLoaded: false,
        duration: 0,
        position: 0,
      });
    } catch (error) {
      console.error('Failed to stop playback:', error);
      options.onError?.(error as Error);
    }
  }, [options]);

  const pausePlayback = useCallback(async () => {
    try {
      if (soundRef.current) {
        await soundRef.current.pauseAsync();
      }
    } catch (error) {
      console.error('Failed to pause playback:', error);
      options.onError?.(error as Error);
    }
  }, [options]);

  const resumePlayback = useCallback(async () => {
    try {
      if (soundRef.current) {
        await soundRef.current.playAsync();
      }
    } catch (error) {
      console.error('Failed to resume playback:', error);
      options.onError?.(error as Error);
    }
  }, [options]);

  // Utility functions
  const getAudioBase64 = useCallback(async (uri: string): Promise<string> => {
    try {
      const base64 = await FileSystem.readAsStringAsync(uri, {
        encoding: FileSystem.EncodingType.Base64,
      });
      return base64;
    } catch (error) {
      console.error('Failed to convert audio to base64:', error);
      options.onError?.(error as Error);
      throw error;
    }
  }, [options]);

  const clearRecording = useCallback(async () => {
    try {
      if (recording.uri) {
        await FileSystem.deleteAsync(recording.uri, { idempotent: true });
      }

      setRecording({
        isRecording: false,
        isPaused: false,
        duration: 0,
        uri: undefined,
      });
    } catch (error) {
      console.error('Failed to clear recording:', error);
      options.onError?.(error as Error);
    }
  }, [recording.uri, options]);

  return {
    recording,
    playback,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    playAudio,
    playAudioFromBase64,
    stopPlayback,
    pausePlayback,
    resumePlayback,
    getAudioBase64,
    clearRecording,
  };
}
