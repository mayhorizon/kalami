// WebSocket client for real-time communication with Kalami gateway
import { WebSocketMessage, TranscriptionPayload, ResponsePayload, AudioPayload, ErrorPayload } from '@/types';

const WS_BASE_URL = __DEV__
  ? 'ws://localhost:3000/ws'
  : 'wss://api.kalami.app/ws';

const HEARTBEAT_INTERVAL = 30000; // 30 seconds
const RECONNECT_DELAY = 3000; // 3 seconds
const MAX_RECONNECT_ATTEMPTS = 5;

type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = (connected: boolean) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private shouldReconnect = true;
  private isConnected = false;

  constructor(baseURL: string = WS_BASE_URL) {
    this.url = baseURL;
  }

  // Connection management
  connect(token: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    this.token = token;
    this.shouldReconnect = true;
    this.reconnectAttempts = 0;
    this.establishConnection();
  }

  private establishConnection(): void {
    if (!this.token) {
      console.error('Cannot connect: no token provided');
      return;
    }

    try {
      const wsURL = `${this.url}?token=${this.token}`;
      this.ws = new WebSocket(wsURL);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);

      console.log('WebSocket connecting to:', this.url);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.cleanup();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  private cleanup(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // Event handlers
  private handleOpen(): void {
    console.log('WebSocket connected');
    this.isConnected = true;
    this.reconnectAttempts = 0;

    this.notifyConnectionHandlers(true);
    this.startHeartbeat();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      // Handle heartbeat internally
      if (message.type === 'heartbeat') {
        this.send({ type: 'heartbeat', payload: { pong: true } });
        return;
      }

      // Notify all message handlers
      this.messageHandlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);

    const errorMessage: WebSocketMessage = {
      type: 'error',
      payload: {
        message: 'WebSocket connection error',
      } as ErrorPayload,
    };

    this.messageHandlers.forEach(handler => handler(errorMessage));
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket closed:', event.code, event.reason);
    this.isConnected = false;
    this.cleanup();

    this.notifyConnectionHandlers(false);

    if (this.shouldReconnect && this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      this.scheduleReconnect();
    } else if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error('Max reconnection attempts reached');
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);

    this.reconnectTimer = setTimeout(() => {
      if (this.shouldReconnect) {
        this.establishConnection();
      }
    }, RECONNECT_DELAY * this.reconnectAttempts);
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'heartbeat', payload: { ping: true } });
      }
    }, HEARTBEAT_INTERVAL);
  }

  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(connected);
      } catch (error) {
        console.error('Error in connection handler:', error);
      }
    });
  }

  // Message sending
  send(message: WebSocketMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected, cannot send message');
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
    }
  }

  sendAudio(audioBase64: string, format: string = 'm4a'): void {
    this.send({
      type: 'audio',
      payload: {
        audio_base64: audioBase64,
        format,
      } as AudioPayload,
    });
  }

  // Event subscriptions
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onConnection(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    return () => this.connectionHandlers.delete(handler);
  }

  // Status
  getConnectionStatus(): boolean {
    return this.isConnected;
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient();
export default wsClient;
