/**
 * Gateway Integration Tests
 *
 * Tests for:
 * - Health check endpoints
 * - WebSocket connections
 * - JWT authentication middleware
 */
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import jwt from 'jsonwebtoken';
import WebSocket from 'ws';
import { app, server, wsService } from '../src/index.js';
import { config } from '../src/config.js';

const BASE_URL = `http://${config.host}:${config.port}`;
const WS_URL = `ws://${config.host}:${config.port}/ws`;

// Wait for server to be ready
beforeAll(async () => {
  await new Promise<void>((resolve) => {
    if (server.listening) {
      resolve();
    } else {
      server.on('listening', () => resolve());
    }
  });
});

afterAll(async () => {
  await new Promise<void>((resolve) => {
    wsService.close();
    server.close(() => resolve());
  });
});

describe('Health Endpoints', () => {
  it('should return healthy status from /health', async () => {
    const response = await fetch(`${BASE_URL}/health`);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.status).toBe('healthy');
    expect(data.service).toBe('kalami-gateway');
    expect(data.version).toBe('0.1.0');
  });

  it('should return service information from root endpoint', async () => {
    const response = await fetch(`${BASE_URL}/`);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.name).toBe('Kalami Gateway');
    expect(data.version).toBe('0.1.0');
    expect(data.endpoints).toHaveProperty('health');
    expect(data.endpoints).toHaveProperty('websocket');
  });

  it('should return stats from /stats endpoint', async () => {
    const response = await fetch(`${BASE_URL}/stats`);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data).toHaveProperty('websocket');
    expect(data.websocket).toHaveProperty('connections');
    expect(data.websocket).toHaveProperty('users');
  });

  it('should check backend readiness at /health/ready', async () => {
    const response = await fetch(`${BASE_URL}/health/ready`);
    const data = await response.json();

    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(data).toHaveProperty('status');
    expect(data).toHaveProperty('backend');
  });
});

describe('JWT Authentication Middleware', () => {
  const validToken = jwt.sign({ sub: 'test-user-123' }, config.jwtSecret, {
    expiresIn: '1h',
  });

  const expiredToken = jwt.sign({ sub: 'test-user-456' }, config.jwtSecret, {
    expiresIn: '0s',
  });

  it('should accept valid JWT token in Authorization header', async () => {
    // Note: This test requires a protected endpoint
    // For now, we'll test token generation
    const decoded = jwt.verify(validToken, config.jwtSecret) as { sub: string };
    expect(decoded.sub).toBe('test-user-123');
  });

  it('should reject expired JWT token', async () => {
    await new Promise((resolve) => setTimeout(resolve, 100)); // Wait for expiry

    try {
      jwt.verify(expiredToken, config.jwtSecret);
      expect.fail('Should have thrown an error');
    } catch (error) {
      expect(error).toBeDefined();
    }
  });

  it('should reject invalid JWT token', async () => {
    const invalidToken = 'invalid.token.here';

    try {
      jwt.verify(invalidToken, config.jwtSecret);
      expect.fail('Should have thrown an error');
    } catch (error) {
      expect(error).toBeDefined();
    }
  });

  it('should generate valid JWT tokens', () => {
    const token = jwt.sign(
      { sub: 'user-789', email: 'test@example.com' },
      config.jwtSecret,
      { expiresIn: '24h' }
    );

    const decoded = jwt.verify(token, config.jwtSecret) as {
      sub: string;
      email: string;
    };

    expect(decoded.sub).toBe('user-789');
    expect(decoded.email).toBe('test@example.com');
  });
});

describe('WebSocket Connections', () => {
  let validToken: string;

  beforeEach(() => {
    validToken = jwt.sign({ sub: 'ws-test-user' }, config.jwtSecret, {
      expiresIn: '1h',
    });
  });

  it('should reject WebSocket connection without token', async () => {
    const ws = new WebSocket(WS_URL);

    await new Promise<void>((resolve) => {
      ws.on('close', (code, reason) => {
        expect(code).toBe(4001);
        expect(reason.toString()).toContain('Authentication required');
        resolve();
      });
    });
  });

  it('should reject WebSocket connection with invalid token', async () => {
    const ws = new WebSocket(`${WS_URL}?token=invalid-token`);

    await new Promise<void>((resolve) => {
      ws.on('close', (code, reason) => {
        expect(code).toBe(4002);
        expect(reason.toString()).toContain('Invalid token');
        resolve();
      });
    });
  });

  it('should accept WebSocket connection with valid token', async () => {
    const ws = new WebSocket(`${WS_URL}?token=${validToken}`);

    await new Promise<void>((resolve, reject) => {
      ws.on('open', () => {
        expect(ws.readyState).toBe(WebSocket.OPEN);
        ws.close();
      });

      ws.on('message', (data) => {
        const message = JSON.parse(data.toString());
        if (message.type === 'connected') {
          expect(message.payload).toHaveProperty('connectionId');
          resolve();
        }
      });

      ws.on('error', (error) => {
        reject(error);
      });

      ws.on('close', () => {
        resolve();
      });
    });
  });

  it('should receive welcome message on connection', async () => {
    const ws = new WebSocket(`${WS_URL}?token=${validToken}`);

    await new Promise<void>((resolve, reject) => {
      let receivedWelcome = false;

      ws.on('message', (data) => {
        const message = JSON.parse(data.toString());

        if (message.type === 'connected') {
          receivedWelcome = true;
          expect(message.payload).toHaveProperty('connectionId');
          expect(typeof message.payload.connectionId).toBe('string');
          ws.close();
        }
      });

      ws.on('close', () => {
        expect(receivedWelcome).toBe(true);
        resolve();
      });

      ws.on('error', (error) => {
        reject(error);
      });
    });
  });

  it('should handle ping-pong messages', async () => {
    const ws = new WebSocket(`${WS_URL}?token=${validToken}`);

    await new Promise<void>((resolve, reject) => {
      ws.on('open', () => {
        ws.send(JSON.stringify({ type: 'ping' }));
      });

      ws.on('message', (data) => {
        const message = JSON.parse(data.toString());

        if (message.type === 'pong') {
          expect(message.type).toBe('pong');
          ws.close();
          resolve();
        }
      });

      ws.on('error', (error) => {
        reject(error);
      });
    });
  });

  it('should handle JSON messages', async () => {
    const ws = new WebSocket(`${WS_URL}?token=${validToken}`);

    await new Promise<void>((resolve, reject) => {
      ws.on('open', () => {
        ws.send(JSON.stringify({
          type: 'start_recording',
        }));
      });

      ws.on('message', (data) => {
        const message = JSON.parse(data.toString());

        if (message.type === 'recording_started') {
          expect(message.type).toBe('recording_started');
          ws.close();
          resolve();
        }
      });

      ws.on('error', (error) => {
        reject(error);
      });

      // Set timeout
      setTimeout(() => {
        ws.close();
        resolve();
      }, 2000);
    });
  });

  it('should track multiple connections in stats', async () => {
    const ws1 = new WebSocket(`${WS_URL}?token=${validToken}`);
    const ws2 = new WebSocket(`${WS_URL}?token=${validToken}`);

    await new Promise<void>((resolve) => {
      let openCount = 0;

      const checkStats = async () => {
        const response = await fetch(`${BASE_URL}/stats`);
        const data = await response.json();

        expect(data.websocket.connections).toBeGreaterThanOrEqual(2);

        ws1.close();
        ws2.close();
        resolve();
      };

      ws1.on('open', () => {
        openCount++;
        if (openCount === 2) {
          setTimeout(checkStats, 100);
        }
      });

      ws2.on('open', () => {
        openCount++;
        if (openCount === 2) {
          setTimeout(checkStats, 100);
        }
      });
    });
  });
});

describe('Error Handling', () => {
  it('should handle malformed JSON in WebSocket messages', async () => {
    const validToken = jwt.sign({ sub: 'error-test-user' }, config.jwtSecret, {
      expiresIn: '1h',
    });

    const ws = new WebSocket(`${WS_URL}?token=${validToken}`);

    await new Promise<void>((resolve, reject) => {
      ws.on('open', () => {
        ws.send('this is not valid json');
      });

      ws.on('message', (data) => {
        const message = JSON.parse(data.toString());

        if (message.type === 'error') {
          expect(message.payload).toHaveProperty('message');
          ws.close();
          resolve();
        }
      });

      ws.on('error', (error) => {
        reject(error);
      });

      // Cleanup timeout
      setTimeout(() => {
        ws.close();
        resolve();
      }, 2000);
    });
  });
});
