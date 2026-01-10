/**
 * Kalami Gateway - Real-time API Gateway
 *
 * Handles:
 * - WebSocket connections for voice streaming
 * - REST API proxy to FastAPI backend
 * - Authentication and rate limiting
 */
import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { config } from './config.js';
import { logger } from './logger.js';
import { WebSocketService } from './services/websocket.js';
import healthRoutes from './routes/health.js';
import proxyRoutes from './routes/proxy.js';

const app = express();
const server = createServer(app);

// Middleware
app.use(cors({ origin: config.corsOrigins }));
app.use(express.json());

// Request logging
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info({
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration: `${duration}ms`,
    });
  });
  next();
});

// Routes
app.use('/health', healthRoutes);
app.use('/api', proxyRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'Kalami Gateway',
    version: '0.1.0',
    endpoints: {
      health: '/health',
      api: '/api/*',
      websocket: '/ws',
    },
  });
});

// Initialize WebSocket service
const wsService = new WebSocketService(server);

// Expose WebSocket stats
app.get('/stats', (req, res) => {
  res.json({
    websocket: wsService.getStats(),
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down...');
  wsService.close();
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down...');
  wsService.close();
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

// Start server
server.listen(config.port, config.host, () => {
  logger.info(`Kalami Gateway running on http://${config.host}:${config.port}`);
  logger.info(`WebSocket available at ws://${config.host}:${config.port}/ws`);
  logger.info(`Backend URL: ${config.backendUrl}`);
});

export { app, server, wsService };
