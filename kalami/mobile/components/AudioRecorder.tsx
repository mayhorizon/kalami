// Audio recording component with visual feedback
import React, { useCallback, useEffect } from 'react';
import { View, TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import * as Haptics from 'expo-haptics';
import { useAudio } from '@/hooks/useAudio';

interface AudioRecorderProps {
  onRecordingComplete?: (audioBase64: string, format: string) => void;
  onError?: (error: Error) => void;
  disabled?: boolean;
}

export function AudioRecorder({ onRecordingComplete, onError, disabled }: AudioRecorderProps) {
  const { recording, startRecording, stopRecording, getAudioBase64, clearRecording } = useAudio({
    onRecordingComplete: async (uri) => {
      if (onRecordingComplete) {
        try {
          const base64 = await getAudioBase64(uri);
          onRecordingComplete(base64, 'm4a');
        } catch (error) {
          console.error('Failed to process recording:', error);
          onError?.(error as Error);
        }
      }
    },
    onError,
  });

  const handlePressIn = useCallback(async () => {
    if (disabled) return;

    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      await startRecording();
    } catch (error) {
      console.error('Failed to start recording:', error);
      onError?.(error as Error);
    }
  }, [disabled, startRecording, onError]);

  const handlePressOut = useCallback(async () => {
    if (disabled) return;

    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      await stopRecording();
    } catch (error) {
      console.error('Failed to stop recording:', error);
      onError?.(error as Error);
    }
  }, [disabled, stopRecording, onError]);

  // Format duration as MM:SS
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <View style={styles.container}>
      {recording.isRecording && (
        <View style={styles.durationContainer}>
          <View style={styles.recordingIndicator} />
          <Text style={styles.durationText}>{formatDuration(recording.duration)}</Text>
        </View>
      )}

      <TouchableOpacity
        style={[
          styles.recordButton,
          recording.isRecording && styles.recordButtonActive,
          disabled && styles.recordButtonDisabled,
        ]}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        activeOpacity={0.8}
        disabled={disabled}
      >
        <View
          style={[
            styles.recordButtonInner,
            recording.isRecording && styles.recordButtonInnerActive,
          ]}
        >
          {disabled ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.recordButtonText}>
              {recording.isRecording ? '🔴' : '🎤'}
            </Text>
          )}
        </View>
      </TouchableOpacity>

      <Text style={styles.instructionText}>
        {recording.isRecording ? 'Release to send' : 'Hold to speak'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
  },
  durationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#FF3B30',
    borderRadius: 20,
  },
  recordingIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#fff',
    marginRight: 8,
  },
  durationText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    fontFamily: 'monospace',
  },
  recordButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  recordButtonActive: {
    backgroundColor: '#FF3B30',
  },
  recordButtonDisabled: {
    backgroundColor: '#999',
    opacity: 0.5,
  },
  recordButtonInner: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#0066E8',
    alignItems: 'center',
    justifyContent: 'center',
  },
  recordButtonInnerActive: {
    backgroundColor: '#E8341A',
  },
  recordButtonText: {
    fontSize: 32,
  },
  instructionText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
});
