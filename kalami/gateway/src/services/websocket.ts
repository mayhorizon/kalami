/**
 * WebSocket service for real-time voice streaming.
 *
 * Handles:
 * - Audio streaming from mobile clients
 * - Real-time transcription updates
 * - AI response streaming
 */
import { WebSocket, WebSocketServer } from 'ws';
import { IncomingMessage } from 'http';
import { v4 as uuidv4 } from 'uuid';
import { config } from '../config.js';
import { logger } from '../logger.js';
import { verifyWsToken } from '../middleware/auth.js';

interface ClientConnection {
  id: string;
  userId: string;
  token: string;
  ws: WebSocket;
  sessionId?: string;
  isAlive: boolean;
  lastActivity: Date;
}

interface WsMessage {
  type: string;
  payload?: unknown;
}

export class WebSocketService {
  private wss: WebSocketServer;
  private clients: Map<string, ClientConnection> = new Map();
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(server: any) {
    this.wss = new WebSocketServer({ server, path: '/ws' });
    this.setupServer();
    this.startHeartbeat();
    logger.info('WebSocket server initialized on /ws');
  }

  private setupServer(): void {
    this.wss.on('connection', (ws: WebSocket, req: IncomingMessage) => {
      this.handleConnection(ws, req);
    });

    this.wss.on('error', (error) => {
      logger.error({ error }, 'WebSocket server error');
    });
  }

  private handleConnection(ws: WebSocket, req: IncomingMessage): void {
    // Extract token from query string
    const url = new URL(req.url || '', `http://${req.headers.host}`);
    const token = url.searchParams.get('token');

    if (!token) {
      logger.warn('WebSocket connection without token');
      ws.close(4001, 'Authentication required');
      return;
    }

    const auth = verifyWsToken(token);
    if (!auth) {
      logger.warn('WebSocket connection with invalid token');
      ws.close(4002, 'Invalid token');
      return;
    }

    const connectionId = uuidv4();
    const client: ClientConnection = {
      id: connectionId,
      userId: auth.userId,
      token: token,
      ws,
      isAlive: true,
      lastActivity: new Date(),
    };

    this.clients.set(connectionId, client);
    logger.info({ connectionId, userId: auth.userId }, 'Client connected');

    // Send welcome message
    this.send(ws, {
      type: 'connected',
      payload: { connectionId },
    });

    // Handle messages
    ws.on('message', (data: Buffer) => {
      this.handleMessage(client, data);
    });

    // Handle pong (heartbeat response)
    ws.on('pong', () => {
      client.isAlive = true;
    });

    // Handle close
    ws.on('close', (code, reason) => {
      logger.info({ connectionId, code, reason: reason.toString() }, 'Client disconnected');
      this.clients.delete(connectionId);
    });

    // Handle errors
    ws.on('error', (error) => {
      logger.error({ connectionId, error }, 'WebSocket client error');
    });
  }

  private handleMessage(client: ClientConnection, data: Buffer): void {
    client.lastActivity = new Date();

    try {
      // Check if binary (audio data) or text (JSON command)
      if (data[0] === 0x7b) {
        // Starts with '{' - JSON message
        const message: WsMessage = JSON.parse(data.toString());
        this.handleJsonMessage(client, message);
      } else {
        // Binary audio data
        this.handleAudioData(client, data);
      }
    } catch (error) {
      logger.error({ error, clientId: client.id }, 'Error handling message');
      this.send(client.ws, {
        type: 'error',
        payload: { message: 'Invalid message format' },
      });
    }
  }

  private handleJsonMessage(client: ClientConnection, message: WsMessage): void {
    logger.debug({ clientId: client.id, type: message.type }, 'Received JSON message');

    switch (message.type) {
      case 'start_session':
        this.handleStartSession(client, message.payload as { profileId: string; topic?: string });
        break;

      case 'end_session':
        this.handleEndSession(client);
        break;

      case 'start_recording':
        this.send(client.ws, { type: 'recording_started' });
        break;

      case 'stop_recording':
        this.handleStopRecording(client);
        break;

      case 'ping':
        this.send(client.ws, { type: 'pong' });
        break;

      case 'heartbeat':
        // Respond to heartbeat from client
        this.send(client.ws, { type: 'heartbeat', payload: { pong: true } });
        break;

      case 'audio':
        // Handle audio data sent as JSON with base64
        this.handleAudioMessage(client, message.payload as { audio_base64: string; format: string });
        break;

      default:
        logger.warn({ type: message.type }, 'Unknown message type');
    }
  }

  private handleAudioData(client: ClientConnection, data: Buffer): void {
    // Forward audio to backend for processing
    // In a real implementation, this would stream to the STT service
    logger.debug({ clientId: client.id, bytes: data.length }, 'Received audio chunk');

    // Acknowledge receipt
    this.send(client.ws, {
      type: 'audio_received',
      payload: { bytes: data.length },
    });
  }

  private async handleStartSession(
    client: ClientConnection,
    payload: { profileId: string; topic?: string }
  ): Promise<void> {
    try {
      // Call backend to create session
      const response = await fetch(`${config.backendUrl}/conversations/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${client.token}`,
        },
        body: JSON.stringify({
          profile_id: payload.profileId,
          topic: payload.topic,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const session = await response.json() as { id: string };
      client.sessionId = session.id;

      this.send(client.ws, {
        type: 'session_started',
        payload: session,
      });

      logger.info({ clientId: client.id, sessionId: session.id }, 'Session started');
    } catch (error) {
      logger.error({ error }, 'Failed to start session');
      this.send(client.ws, {
        type: 'error',
        payload: { message: 'Failed to start session' },
      });
    }
  }

  private handleEndSession(client: ClientConnection): void {
    if (client.sessionId) {
      // Call backend to end session
      logger.info({ clientId: client.id, sessionId: client.sessionId }, 'Session ended');
      client.sessionId = undefined;

      this.send(client.ws, { type: 'session_ended' });
    }
  }

  private handleStopRecording(client: ClientConnection): void {
    // Signal that recording has stopped
    // Backend will finalize transcription and generate response
    this.send(client.ws, {
      type: 'processing',
      payload: { stage: 'transcribing' },
    });
  }

  private async handleAudioMessage(
    client: ClientConnection,
    payload: { audio_base64: string; format: string; session_id?: string }
  ): Promise<void> {
    const sessionId = payload.session_id || client.sessionId;

    if (!sessionId) {
      this.send(client.ws, {
        type: 'error',
        payload: { message: 'No active session. Start a session first.' },
      });
      return;
    }

    logger.info({ clientId: client.id, format: payload.format, sessionId }, 'Processing audio');

    // Notify client we're processing
    this.send(client.ws, {
      type: 'processing',
      payload: { stage: 'transcribing' },
    });

    try {
      // Convert base64 to buffer
      const audioBuffer = Buffer.from(payload.audio_base64, 'base64');

      logger.info({ clientId: client.id, audioSize: audioBuffer.length }, 'Audio buffer created');

      // Create multipart form data manually for Node.js compatibility
      const boundary = '----WebKitFormBoundary' + Math.random().toString(36).substring(2);
      const filename = `recording.${payload.format}`;
      const contentType = payload.format === 'webm' ? 'audio/webm' : `audio/${payload.format}`;

      // Build multipart body
      const parts: Buffer[] = [];

      // Add audio file part
      parts.push(Buffer.from(
        `--${boundary}\r\n` +
        `Content-Disposition: form-data; name="audio"; filename="${filename}"\r\n` +
        `Content-Type: ${contentType}\r\n\r\n`
      ));
      parts.push(audioBuffer);
      parts.push(Buffer.from('\r\n'));

      // End boundary
      parts.push(Buffer.from(`--${boundary}--\r\n`));

      const body = Buffer.concat(parts);

      // Send to backend for processing (STT -> LLM -> TTS)
      const response = await fetch(`${config.backendUrl}/conversations/sessions/${sessionId}/audio`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${client.token}`,
          'Content-Type': `multipart/form-data; boundary=${boundary}`,
        },
        body: body,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }

      const result = await response.json() as {
        user_text: string;
        assistant_text: string;
        assistant_audio_base64?: string;
        corrections?: Array<{ original: string; corrected: string; explanation: string }>;
      };

      // Send transcription
      this.send(client.ws, {
        type: 'transcription',
        payload: {
          text: result.user_text,
          is_final: true,
        },
      });

      // Send AI response
      this.send(client.ws, {
        type: 'response',
        payload: {
          text: result.assistant_text,
          grammar_corrections: result.corrections || [],
        },
      });

      // Send audio response if available
      if (result.assistant_audio_base64) {
        this.send(client.ws, {
          type: 'audio',
          payload: {
            audio_base64: result.assistant_audio_base64,
            format: 'mp3',
          },
        });
      }

      logger.info({ clientId: client.id }, 'Audio processing complete');

    } catch (error) {
      logger.error({ error, clientId: client.id }, 'Failed to process audio');
      this.send(client.ws, {
        type: 'error',
        payload: { message: 'Failed to process audio. Please try again.' },
      });
    }
  }

  private send(ws: WebSocket, message: WsMessage): void {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }

  /**
   * Send a message to a specific user (all their connections).
   */
  public sendToUser(userId: string, message: WsMessage): void {
    for (const client of this.clients.values()) {
      if (client.userId === userId) {
        this.send(client.ws, message);
      }
    }
  }

  /**
   * Broadcast to all connected clients.
   */
  public broadcast(message: WsMessage): void {
    for (const client of this.clients.values()) {
      this.send(client.ws, message);
    }
  }

  /**
   * Start heartbeat to detect dead connections.
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      for (const [id, client] of this.clients.entries()) {
        if (!client.isAlive) {
          logger.info({ connectionId: id }, 'Client heartbeat timeout');
          client.ws.terminate();
          this.clients.delete(id);
          continue;
        }

        client.isAlive = false;
        client.ws.ping();
      }
    }, config.wsHeartbeatInterval);
  }

  /**
   * Graceful shutdown.
   */
  public close(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    for (const client of this.clients.values()) {
      client.ws.close(1001, 'Server shutting down');
    }

    this.wss.close();
    logger.info('WebSocket server closed');
  }

  /**
   * Get connection statistics.
   */
  public getStats(): { connections: number; users: number } {
    const userIds = new Set<string>();
    for (const client of this.clients.values()) {
      userIds.add(client.userId);
    }

    return {
      connections: this.clients.size,
      users: userIds.size,
    };
  }
}
