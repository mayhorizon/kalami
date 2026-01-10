/**
 * Gateway configuration loaded from environment variables.
 */
import dotenv from 'dotenv';

dotenv.config();

export const config = {
  // Server
  port: parseInt(process.env.GATEWAY_PORT || '3000', 10),
  host: process.env.GATEWAY_HOST || '0.0.0.0',

  // Backend API
  backendUrl: process.env.BACKEND_URL || 'http://localhost:8000',

  // JWT
  jwtSecret: process.env.JWT_SECRET || 'your-secret-key-change-in-production',

  // WebSocket
  wsHeartbeatInterval: parseInt(process.env.WS_HEARTBEAT_INTERVAL || '30000', 10),

  // CORS
  corsOrigins: process.env.CORS_ORIGINS?.split(',') || ['*'],

  // Logging
  logLevel: process.env.LOG_LEVEL || 'info',
};
