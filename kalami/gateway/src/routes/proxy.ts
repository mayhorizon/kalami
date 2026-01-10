/**
 * API proxy routes to forward requests to the backend.
 */
import { Router, Request, Response } from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import { config } from '../config.js';
import { logger } from '../logger.js';

const router = Router();

// Proxy all /api requests to backend
router.use('/', createProxyMiddleware({
  target: config.backendUrl,
  changeOrigin: true,
  pathRewrite: {
    '^/api': '',
  },
  onProxyReq: (proxyReq: any, req: Request) => {
    logger.debug({ method: req.method, path: req.path }, 'Proxying request');
  },
  onProxyRes: (proxyRes: any, req: Request) => {
    logger.debug(
      { method: req.method, path: req.path, status: proxyRes.statusCode },
      'Proxy response'
    );
  },
  onError: (err: Error, req: Request, res: Response) => {
    logger.error({ error: err, path: req.url }, 'Proxy error');
    res.status(502).json({ error: 'Backend service unavailable' });
  },
}));

export default router;
