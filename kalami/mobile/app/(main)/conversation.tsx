// Main conversation screen with audio recording
import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '@/store/authStore';
import { useConversationStore } from '@/store/conversationStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAudio } from '@/hooks/useAudio';
import { AudioRecorder } from '@/components/AudioRecorder';
import { ConversationBubble } from '@/components/ConversationBubble';
import { WaveformVisualizer } from '@/components/WaveformVisualizer';
import { ConversationMessage } from '@/types';

// Cross-platform confirm dialog
const confirmAction = (title: string, message: string, onConfirm: () => void) => {
  if (Platform.OS === 'web') {
    if (window.confirm(`${title}\n\n${message}`)) {
      onConfirm();
    }
  } else {
    // Use dynamic import to avoid web bundling issues
    import('react-native').then(({ Alert }) => {
      Alert.alert(title, message, [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Confirm', style: 'destructive', onPress: onConfirm },
      ]);
    });
  }
};

export default function ConversationScreen() {
  const router = useRouter();
  const flatListRef = useRef<FlatList>(null);
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);

  const user = useAuthStore(state => state.user);
  const logout = useAuthStore(state => state.logout);

  const {
    currentSession,
    messages,
    selectedProfile,
    profiles,
    currentTranscription,
    isSpeaking,
    loadProfiles,
    startSession,
    endSession,
    setIsSpeaking,
  } = useConversationStore();

  const [error, setError] = useState<string | null>(null);

  const { isConnected, sendAudio } = useWebSocket({
    autoConnect: true,
    onError: (err) => {
      console.error('Connection error:', err);
      setError(`Connection Error: ${err}`);
    },
    onAudioReceived: async (audioBase64, format) => {
      console.log('Playing AI audio response, format:', format);
      try {
        await playAudioFromBase64(audioBase64);
      } catch (err: any) {
        console.error('Failed to play AI audio:', err);
      }
    },
  });

  const { playAudioFromBase64 } = useAudio({
    onPlaybackComplete: () => {
      setPlayingMessageId(null);
    },
    onError: (err) => {
      console.error('Audio playback error:', err);
      setError(`Playback Error: ${err.message}`);
    },
  });

  // Load profiles on mount
  useEffect(() => {
    loadProfiles().catch(err => {
      console.error('Failed to load profiles:', err);
      setError('Failed to load learning profiles');
    });
  }, [loadProfiles]);

  // Clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0) {
      flatListRef.current?.scrollToEnd({ animated: true });
    }
  }, [messages]);

  // Track if we're currently starting a session to prevent duplicates
  const isStartingSessionRef = useRef(false);

  // Start session when profile is selected or changed
  useEffect(() => {
    if (!selectedProfile) return;
    if (isStartingSessionRef.current) return;

    // Check if we need a new session (no session or wrong profile)
    const needsNewSession = !currentSession ||
      currentSession.profile_id !== selectedProfile.id;

    if (needsNewSession) {
      isStartingSessionRef.current = true;

      const startNew = async () => {
        try {
          if (currentSession) {
            await endSession();
          }
          await handleStartSession();
        } finally {
          isStartingSessionRef.current = false;
        }
      };

      startNew();
    }
  }, [selectedProfile?.id]);

  const handleStartSession = async () => {
    try {
      await startSession();
    } catch (err: any) {
      console.error('Failed to start session:', err);
      setError('Failed to start conversation session');
    }
  };

  const handleEndSession = async () => {
    confirmAction(
      'End Session',
      'Are you sure you want to end this conversation?',
      async () => {
        await endSession();
        router.push('/(main)/profile');
      }
    );
  };

  const handleRecordingComplete = async (audioBase64: string, format: string) => {
    if (!isConnected) {
      setError('Not connected. Please wait for connection to be established.');
      return;
    }

    if (!currentSession) {
      setError('No active session. Please wait for session to start.');
      return;
    }

    setIsSpeaking(true);

    try {
      // Send audio via WebSocket with session ID
      sendAudio(audioBase64, format, currentSession.id);
    } catch (err: any) {
      console.error('Failed to send audio:', err);
      setError('Failed to send audio. Please try again.');
      setIsSpeaking(false);
    }
  };

  const handlePlayMessage = async (message: ConversationMessage) => {
    if (!message.audio_url) return;

    try {
      setPlayingMessageId(message.id);
      // In production, fetch audio from URL and convert to base64
      // For now, assuming audio_url contains base64 data
      await playAudioFromBase64(message.audio_url);
    } catch (error) {
      console.error('Failed to play message audio:', error);
      setPlayingMessageId(null);
    }
  };

  const handleProfile = () => {
    router.push('/(main)/profile');
  };

  const handleLogout = async () => {
    confirmAction(
      'Logout',
      'Are you sure you want to logout?',
      async () => {
        await logout();
        router.replace('/(auth)/login');
      }
    );
  };

  const renderMessage = ({ item }: { item: ConversationMessage }) => (
    <ConversationBubble
      message={item}
      onPlayAudio={() => handlePlayMessage(item)}
      isAudioPlaying={playingMessageId === item.id}
    />
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.headerLeft}>
        <TouchableOpacity onPress={handleProfile} style={styles.profileButton}>
          <Text style={styles.profileIcon}>👤</Text>
        </TouchableOpacity>
        <View>
          <Text style={styles.headerTitle}>
            {selectedProfile ? `Learning ${selectedProfile.target_language}` : 'Kalami'}
          </Text>
          <View style={styles.connectionStatus}>
            <View style={[styles.statusDot, isConnected && styles.statusDotConnected]} />
            <Text style={styles.statusText}>
              {isConnected ? 'Connected' : 'Connecting...'}
            </Text>
          </View>
        </View>
      </View>
      <View style={styles.headerRight}>
        {currentSession && (
          <TouchableOpacity onPress={handleEndSession} style={styles.endButton}>
            <Text style={styles.endButtonText}>End</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
          <Text style={styles.logoutIcon}>🚪</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (!selectedProfile) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No Learning Profile</Text>
          <Text style={styles.emptyText}>
            Create a learning profile to start practicing
          </Text>
          <TouchableOpacity style={styles.button} onPress={handleProfile}>
            <Text style={styles.buttonText}>Create Profile</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        {renderHeader()}

        {error && (
          <View style={styles.errorBanner}>
            <Text style={styles.errorBannerText}>{error}</Text>
            <TouchableOpacity onPress={() => setError(null)}>
              <Text style={styles.errorDismiss}>✕</Text>
            </TouchableOpacity>
          </View>
        )}

        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messageList}
          ListEmptyComponent={
            <View style={styles.emptyMessages}>
              <Text style={styles.emptyMessagesIcon}>💬</Text>
              <Text style={styles.emptyMessagesText}>
                Start speaking to begin your conversation
              </Text>
            </View>
          }
        />

        {currentTranscription && (
          <View style={styles.transcriptionContainer}>
            <Text style={styles.transcriptionLabel}>You're saying:</Text>
            <Text style={styles.transcriptionText}>{currentTranscription}</Text>
          </View>
        )}

        {isSpeaking && (
          <View style={styles.processingContainer}>
            <WaveformVisualizer isActive={true} />
            <Text style={styles.processingText}>Processing...</Text>
          </View>
        )}

        <View style={styles.inputContainer}>
          <AudioRecorder
            onRecordingComplete={handleRecordingComplete}
            onError={(err) => {
              console.error('Recording error:', err);
              setError(`Recording Error: ${err.message}`);
            }}
            disabled={!isConnected || isSpeaking}
          />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#fff',
  },
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  profileButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F5F5F5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileIcon: {
    fontSize: 20,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#999',
    marginRight: 6,
  },
  statusDotConnected: {
    backgroundColor: '#34C759',
  },
  statusText: {
    fontSize: 12,
    color: '#666',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  endButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#FF3B30',
    borderRadius: 8,
  },
  endButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  logoutButton: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoutIcon: {
    fontSize: 18,
  },
  messageList: {
    paddingVertical: 16,
  },
  emptyMessages: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyMessagesIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyMessagesText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  transcriptionContainer: {
    backgroundColor: '#F5F5F5',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5E5',
  },
  transcriptionLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  transcriptionText: {
    fontSize: 16,
    color: '#000',
  },
  processingContainer: {
    alignItems: 'center',
    paddingVertical: 16,
    backgroundColor: '#F5F5F5',
  },
  processingText: {
    marginTop: 8,
    fontSize: 14,
    color: '#666',
  },
  inputContainer: {
    borderTopWidth: 1,
    borderTopColor: '#E5E5E5',
    backgroundColor: '#fff',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  button: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  errorBanner: {
    backgroundColor: '#FFEBEE',
    borderBottomWidth: 1,
    borderBottomColor: '#F44336',
    paddingHorizontal: 16,
    paddingVertical: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  errorBannerText: {
    color: '#C62828',
    fontSize: 14,
    flex: 1,
  },
  errorDismiss: {
    color: '#C62828',
    fontSize: 18,
    paddingLeft: 12,
  },
});
