/**
 * Health check routes.
 */
import { Router } from 'express';
import { config } from '../config.js';

const router = Router();

router.get('/', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'kalami-gateway',
    version: '0.1.0',
  });
});

router.get('/ready', async (req, res) => {
  // Check if backend is reachable
  try {
    const response = await fetch(`${config.backendUrl}/health`, {
      signal: AbortSignal.timeout(5000),
    });

    if (response.ok) {
      res.json({
        status: 'ready',
        backend: 'connected',
      });
    } else {
      res.status(503).json({
        status: 'degraded',
        backend: 'unhealthy',
      });
    }
  } catch (error) {
    res.status(503).json({
      status: 'not ready',
      backend: 'unreachable',
    });
  }
});

export default router;
