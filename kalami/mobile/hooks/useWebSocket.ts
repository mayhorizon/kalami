// Custom hook for WebSocket connection management
import { useEffect, useCallback, useRef } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useConversationStore } from '@/store/conversationStore';
import { wsClient } from '@/services/websocket';
import { WebSocketMessage, ConversationMessage } from '@/types';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: string) => void;
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

  const isConnectedRef = useRef(false);
  const hasConnectedRef = useRef(false);

  // Message handler
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'connected':
        console.log('WebSocket connected:', message.payload);
        options.onConnected?.();
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
            id: `temp-${Date.now()}`,
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
        // AI response received
        const response = message.payload;
        const assistantMessage: ConversationMessage = {
          id: `temp-${Date.now()}`,
          session_id: '',
          role: 'assistant',
          content_text: response.text,
          grammar_corrections: response.grammar_corrections,
          timestamp: new Date().toISOString(),
        };
        addMessage(assistantMessage);
        break;

      case 'audio':
        // Audio response received - will be handled by conversation screen
        console.log('Audio response received');
        break;

      case 'error':
        console.error('WebSocket error:', message.payload);
        options.onError?.(message.payload.message);
        break;

      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }, [setCurrentTranscription, addMessage, options]);

  // Connection status handler
  const handleConnection = useCallback((connected: boolean) => {
    isConnectedRef.current = connected;

    if (connected) {
      hasConnectedRef.current = true;
      options.onConnected?.();
    } else {
      options.onDisconnected?.();
    }
  }, [options]);

  // Connect function
  const connect = useCallback(async () => {
    try {
      const token = await useAuthStore.getState().user;

      if (!token) {
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
      options.onError?.('Failed to establish connection');
    }
  }, [options]);

  // Disconnect function
  const disconnect = useCallback(() => {
    wsClient.disconnect();
    hasConnectedRef.current = false;
  }, []);

  // Send audio function
  const sendAudio = useCallback((audioBase64: string, format: string = 'm4a') => {
    if (!isConnectedRef.current) {
      console.error('Cannot send audio: WebSocket not connected');
      options.onError?.('Not connected to server');
      return;
    }

    wsClient.sendAudio(audioBase64, format);
  }, [options]);

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

    return () => {
      if (autoConnect) {
        disconnect();
      }
    };
  }, [autoConnect, isAuthenticated, connect, disconnect]);

  return {
    isConnected: isConnectedRef.current,
    connect,
    disconnect,
    sendAudio,
  };
}
