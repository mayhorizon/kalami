// Chat bubble component for conversation messages
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { ConversationMessage } from '@/types';

interface ConversationBubbleProps {
  message: ConversationMessage;
  onPlayAudio?: () => void;
  isAudioPlaying?: boolean;
}

export function ConversationBubble({ message, onPlayAudio, isAudioPlaying }: ConversationBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <View style={[styles.container, isUser ? styles.userContainer : styles.assistantContainer]}>
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        <Text style={[styles.text, isUser ? styles.userText : styles.assistantText]}>
          {message.content_text}
        </Text>

        {message.audio_url && (
          <TouchableOpacity
            style={styles.audioButton}
            onPress={onPlayAudio}
            disabled={isAudioPlaying}
          >
            <Text style={styles.audioIcon}>{isAudioPlaying ? '⏸️' : '▶️'}</Text>
          </TouchableOpacity>
        )}

        {message.grammar_corrections && message.grammar_corrections.length > 0 && (
          <View style={styles.correctionsContainer}>
            <Text style={styles.correctionsTitle}>✏️ Corrections:</Text>
            {message.grammar_corrections.map((correction, index) => (
              <View key={index} style={styles.correctionItem}>
                <Text style={styles.correctionOriginal}>
                  ❌ {correction.original}
                </Text>
                <Text style={styles.correctionCorrected}>
                  ✅ {correction.corrected}
                </Text>
                <Text style={styles.correctionExplanation}>
                  {correction.explanation}
                </Text>
              </View>
            ))}
          </View>
        )}

        {message.pronunciation_feedback && (
          <View style={styles.pronunciationContainer}>
            <Text style={styles.pronunciationTitle}>
              🗣️ Pronunciation: {Math.round(message.pronunciation_feedback.overall_score)}%
            </Text>
            {message.pronunciation_feedback.problematic_phonemes && (
              <Text style={styles.pronunciationText}>
                Practice: {message.pronunciation_feedback.problematic_phonemes.join(', ')}
              </Text>
            )}
          </View>
        )}
      </View>

      <Text style={[styles.timestamp, isUser ? styles.userTimestamp : styles.assistantTimestamp]}>
        {formatTime(message.timestamp)}
      </Text>
    </View>
  );
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  const hours = date.getHours();
  const minutes = date.getMinutes();
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const formattedHours = hours % 12 || 12;
  const formattedMinutes = minutes.toString().padStart(2, '0');
  return `${formattedHours}:${formattedMinutes} ${ampm}`;
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 4,
    marginHorizontal: 16,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  bubble: {
    maxWidth: '80%',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  userBubble: {
    backgroundColor: '#007AFF',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#E5E5EA',
    borderBottomLeftRadius: 4,
  },
  text: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#fff',
  },
  assistantText: {
    color: '#000',
  },
  timestamp: {
    fontSize: 11,
    color: '#999',
    marginTop: 4,
    marginHorizontal: 4,
  },
  userTimestamp: {
    textAlign: 'right',
  },
  assistantTimestamp: {
    textAlign: 'left',
  },
  audioButton: {
    marginTop: 8,
    padding: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  audioIcon: {
    fontSize: 20,
  },
  correctionsContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.1)',
  },
  correctionsTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: '#000',
  },
  correctionItem: {
    marginBottom: 8,
  },
  correctionOriginal: {
    fontSize: 13,
    color: '#FF3B30',
    marginBottom: 2,
  },
  correctionCorrected: {
    fontSize: 13,
    color: '#34C759',
    marginBottom: 2,
  },
  correctionExplanation: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  pronunciationContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.1)',
  },
  pronunciationTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  pronunciationText: {
    fontSize: 13,
    color: '#666',
  },
});
