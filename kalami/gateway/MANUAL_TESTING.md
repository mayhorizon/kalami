# Manual Testing Guide for Kalami Gateway

Since automated installation is restricted, follow these manual steps to test and run the gateway.

## Step 1: Install Dependencies

```bash
cd /home/savetheworld/kalami/gateway
npm install
```

Expected output: Dependencies installed successfully, `node_modules/` directory created.

## Step 2: Build TypeScript

```bash
npm run build
```

Expected output:
- No TypeScript errors
- `dist/` directory created with compiled JavaScript files

**Known fixes applied:**
- Fixed undefined `token` variable in `src/middleware/auth.ts` line 69

## Step 3: Run Tests

```bash
npm test
```

This will run the vitest test suite covering:
- Health endpoints (`/health`, `/stats`, `/health/ready`)
- JWT authentication (valid tokens, expired tokens, invalid tokens)
- WebSocket connections (authentication, message handling, ping-pong)
- Error handling

## Step 4: Start Development Server

```bash
npm run dev
```

Expected output:
```
Kalami Gateway running on http://0.0.0.0:3000
WebSocket available at ws://0.0.0.0:3000/ws
Backend URL: http://localhost:8000
```

## Step 5: Manual Endpoint Tests

### Test Health Endpoint

```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "kalami-gateway",
  "version": "0.1.0"
}
```

### Test Root Endpoint

```bash
curl http://localhost:3000/
```

Expected response:
```json
{
  "name": "Kalami Gateway",
  "version": "0.1.0",
  "endpoints": {
    "health": "/health",
    "api": "/api/*",
    "websocket": "/ws"
  }
}
```

### Test Stats Endpoint

```bash
curl http://localhost:3000/stats
```

Expected response:
```json
{
  "websocket": {
    "connections": 0,
    "users": 0
  }
}
```

### Test Readiness Check

```bash
curl http://localhost:3000/health/ready
```

Expected response (if backend is running):
```json
{
  "status": "ready",
  "backend": "connected"
}
```

Expected response (if backend is not running):
```json
{
  "status": "not ready",
  "backend": "unreachable"
}
```

## Step 6: Test WebSocket Connection

### Without Token (Should Fail)

```bash
npm install -g wscat  # If not already installed
wscat -c ws://localhost:3000/ws
```

Expected: Connection closes with code 4001 (Authentication required)

### With Valid Token

First, generate a test token:

```bash
node -e "const jwt = require('jsonwebtoken'); const token = jwt.sign({ sub: 'test-user' }, 'your-secret-key-change-in-production', { expiresIn: '1h' }); console.log(token);"
```

Then connect:

```bash
wscat -c "ws://localhost:3000/ws?token=YOUR_TOKEN_HERE"
```

Expected:
```json
< {"type":"connected","payload":{"connectionId":"..."}}
```

Send a ping:
```json
> {"type":"ping"}
< {"type":"pong"}
```

## Known Issues and Fixes Applied

### 1. TypeScript Error in auth.ts (FIXED)

**Issue:** Undefined variable `token` on line 69 of `src/middleware/auth.ts`

**Fix Applied:**
```typescript
// Before (broken):
const parts = authHeader.split(' ');
if (parts.length === 2 && parts[0] === 'Bearer') {
  try {
    const decoded = jwt.verify(token, config.jwtSecret) as { sub: string };
    // ...
  }
}

// After (fixed):
const parts = authHeader.split(' ');
if (parts.length === 2 && parts[0] === 'Bearer') {
  const token = parts[1];  // <-- ADDED THIS LINE
  try {
    const decoded = jwt.verify(token, config.jwtSecret) as { sub: string };
    // ...
  }
}
```

## Error Scenarios to Test

1. **Invalid JSON in WebSocket**: Send malformed JSON, should receive error message
2. **Expired JWT**: Create expired token, should be rejected
3. **Missing Authorization Header**: Call protected endpoint without header
4. **Backend Offline**: Stop backend, check `/health/ready` returns 503
5. **Invalid WebSocket Message Type**: Send unknown message type

## Performance Testing

Test multiple simultaneous WebSocket connections:

```bash
# Terminal 1
wscat -c "ws://localhost:3000/ws?token=TOKEN1"

# Terminal 2
wscat -c "ws://localhost:3000/ws?token=TOKEN2"

# Terminal 3
curl http://localhost:3000/stats
```

Stats should show 2 connections.

## Cleanup

Stop the server with `Ctrl+C`. The gateway handles graceful shutdown:
- Closes all WebSocket connections with code 1001
- Stops accepting new connections
- Exits cleanly

## Troubleshooting

### Port 3000 already in use

```bash
lsof -ti:3000 | xargs kill
```

Or change `GATEWAY_PORT` in `.env`.

### Module not found errors

```bash
rm -rf node_modules package-lock.json
npm install
```

### TypeScript compilation errors

Check `tsconfig.json` settings and ensure all source files have proper imports with `.js` extensions (required for ES modules).

### WebSocket connection issues

- Verify JWT_SECRET in `.env` matches token signing secret
- Check token is not expired
- Ensure token is passed as query parameter: `?token=xxx`
