// Custom hook for WebSocket connection management
import { useEffect, useCallback, useRef, useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useConversationStore } from '@/store/conversationStore';
import { wsClient } from '@/services/websocket';
import { WebSocketMessage, ConversationMessage } from '@/types';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: string) => void;
  onAudioReceived?: (audioBase64: string, format: string) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  sendAudio: (audioBase64: string, format?: string) => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { autoConnect = true } = options;
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const setCurrentTranscription = useConversationStore(state => state.setCurrentTranscription);
  const addMessage = useConversationStore(state => state.addMessage);
  const setIsSpeaking = useConversationStore(state => state.setIsSpeaking);

  const [isConnected, setIsConnected] = useState(false);
  const hasConnectedRef = useRef(false);

  // Store callbacks in refs to avoid effect re-runs
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // Message handler
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'connected':
        console.log('WebSocket connected:', message.payload);
        optionsRef.current.onConnected?.();
        break;

      case 'transcription':
        // Update real-time transcription
        const transcription = message.payload;
        if (transcription.text) {
          setCurrentTranscription(transcription.text);
        }

        // If final transcription, create user message
        if (transcription.is_final) {
          const userMessage: ConversationMessage = {
            id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            session_id: '', // Will be set by backend
            role: 'user',
            content_text: transcription.text,
            timestamp: new Date().toISOString(),
          };
          addMessage(userMessage);
          setCurrentTranscription('');
        }
        break;

      case 'response':
        // AI response received - reset speaking state
        setIsSpeaking(false);
        const response = message.payload;
        const assistantMessage: ConversationMessage = {
          id: `assistant-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          session_id: '',
          role: 'assistant',
          content_text: response.text,
          grammar_corrections: response.grammar_corrections,
          timestamp: new Date().toISOString(),
        };
        addMessage(assistantMessage);
        break;

      case 'audio':
        // Audio response received - play it
        console.log('Audio response received');
        const audioPayload = message.payload as { audio_base64: string; format: string };
        if (audioPayload?.audio_base64) {
          optionsRef.current.onAudioReceived?.(audioPayload.audio_base64, audioPayload.format || 'mp3');
        }
        break;

      case 'error':
        console.error('WebSocket error:', message.payload);
        setIsSpeaking(false);  // Allow user to retry
        optionsRef.current.onError?.(message.payload.message);
        break;

      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }, [setCurrentTranscription, addMessage, setIsSpeaking]);

  // Connection status handler
  const handleConnection = useCallback((connected: boolean) => {
    setIsConnected(connected);

    if (connected) {
      hasConnectedRef.current = true;
      optionsRef.current.onConnected?.();
    } else {
      optionsRef.current.onDisconnected?.();
    }
  }, []);

  // Connect function
  const connect = useCallback(async () => {
    try {
      const user = useAuthStore.getState().user;

      if (!user) {
        console.error('Cannot connect WebSocket: not authenticated');
        return;
      }

      // Get JWT token from API client
      const { default: apiClient } = await import('@/services/api');
      const jwtToken = await apiClient.getToken();

      if (!jwtToken) {
        console.error('Cannot connect WebSocket: no JWT token');
        return;
      }

      wsClient.connect(jwtToken);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      optionsRef.current.onError?.('Failed to establish connection');
    }
  }, []);

  // Disconnect function
  const disconnect = useCallback(() => {
    wsClient.disconnect();
    hasConnectedRef.current = false;
  }, []);

  // Send audio function
  const sendAudio = useCallback((audioBase64: string, format: string = 'm4a', sessionId?: string) => {
    if (!wsClient.getConnectionStatus()) {
      console.error('Cannot send audio: WebSocket not connected');
      optionsRef.current.onError?.('Not connected to server');
      return;
    }

    wsClient.sendAudio(audioBase64, format, sessionId);
  }, []);

  // Setup WebSocket listeners
  useEffect(() => {
    const unsubscribeMessage = wsClient.onMessage(handleMessage);
    const unsubscribeConnection = wsClient.onConnection(handleConnection);

    return () => {
      unsubscribeMessage();
      unsubscribeConnection();
    };
  }, [handleMessage, handleConnection]);

  // Auto-connect when authenticated
  useEffect(() => {
    if (autoConnect && isAuthenticated && !hasConnectedRef.current) {
      connect();
    }

    // Only disconnect on unmount, not on every re-render
    return () => {
      // Don't disconnect on re-renders, only when component fully unmounts
    };
  }, [autoConnect, isAuthenticated, connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (hasConnectedRef.current) {
        wsClient.disconnect();
        hasConnectedRef.current = false;
      }
    };
  }, []);

  return {
    isConnected,
    connect,
    disconnect,
    sendAudio,
  };
}
