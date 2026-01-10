# Kalami Gateway

Real-time API gateway for the Kalami language learning application. Handles WebSocket connections for voice streaming and proxies REST API requests to the FastAPI backend.

## Architecture

- **Express.js** - HTTP server and routing
- **WebSocket (ws)** - Real-time bidirectional communication
- **http-proxy-middleware** - Reverse proxy to FastAPI backend
- **JWT** - Authentication and authorization
- **Pino** - Structured logging

## Prerequisites

- Node.js >= 18.0.0
- npm or yarn
- FastAPI backend running (default: http://localhost:8000)

## Installation

```bash
npm install
```

## Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GATEWAY_PORT` | Port to run the gateway on | 3000 |
| `GATEWAY_HOST` | Host to bind to | 0.0.0.0 |
| `BACKEND_URL` | URL of the FastAPI backend | http://localhost:8000 |
| `JWT_SECRET` | Secret key for JWT signing/verification | (change in production) |
| `WS_HEARTBEAT_INTERVAL` | WebSocket heartbeat interval (ms) | 30000 |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | * |
| `LOG_LEVEL` | Logging level (debug, info, warn, error) | info |

**IMPORTANT**: Change `JWT_SECRET` to a secure random string in production.

## Development

Run in development mode with auto-reload:

```bash
npm run dev
```

The gateway will start on `http://localhost:3000` with:
- HTTP endpoints: `http://localhost:3000/`
- WebSocket endpoint: `ws://localhost:3000/ws`

## Production

Build the TypeScript code:

```bash
npm run build
```

Start the production server:

```bash
npm start
```

## Testing

Run the test suite:

```bash
npm test
```

Run tests with coverage:

```bash
npm run test -- --coverage
```

## API Endpoints

### Health Check

```
GET /health
```

Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "kalami-gateway",
  "version": "0.1.0"
}
```

### Readiness Check

```
GET /health/ready
```

Checks if the gateway can connect to the backend.

**Response:**
```json
{
  "status": "ready",
  "backend": "connected"
}
```

### Statistics

```
GET /stats
```

Returns WebSocket connection statistics.

**Response:**
```json
{
  "websocket": {
    "connections": 5,
    "users": 3
  }
}
```

### API Proxy

```
GET/POST/PUT/DELETE /api/*
```

All requests to `/api/*` are proxied to the backend at `BACKEND_URL`.

Example:
- `GET /api/users/me` → `GET {BACKEND_URL}/users/me`
- `POST /api/conversations/sessions` → `POST {BACKEND_URL}/conversations/sessions`

## WebSocket Connection

### Authentication

WebSocket connections require a JWT token passed as a query parameter:

```javascript
const ws = new WebSocket('ws://localhost:3000/ws?token=YOUR_JWT_TOKEN');
```

The token must be signed with the `JWT_SECRET` and contain a `sub` claim with the user ID.

### Connection Flow

1. Client connects with valid JWT token
2. Server validates token and sends welcome message:

```json
{
  "type": "connected",
  "payload": {
    "connectionId": "uuid-here"
  }
}
```

3. Client can now send/receive messages

### Message Types

#### Client to Server

**Start Session:**
```json
{
  "type": "start_session",
  "payload": {
    "profileId": "profile-id",
    "topic": "shopping"
  }
}
```

**Start Recording:**
```json
{
  "type": "start_recording"
}
```

**Audio Data:**
Send raw binary audio data (not JSON).

**Stop Recording:**
```json
{
  "type": "stop_recording"
}
```

**End Session:**
```json
{
  "type": "end_session"
}
```

**Ping:**
```json
{
  "type": "ping"
}
```

#### Server to Client

**Session Started:**
```json
{
  "type": "session_started",
  "payload": {
    "id": "session-id",
    "profileId": "profile-id"
  }
}
```

**Recording Started:**
```json
{
  "type": "recording_started"
}
```

**Audio Received:**
```json
{
  "type": "audio_received",
  "payload": {
    "bytes": 4096
  }
}
```

**Processing:**
```json
{
  "type": "processing",
  "payload": {
    "stage": "transcribing"
  }
}
```

**Session Ended:**
```json
{
  "type": "session_ended"
}
```

**Pong:**
```json
{
  "type": "pong"
}
```

**Error:**
```json
{
  "type": "error",
  "payload": {
    "message": "Error description"
  }
}
```

### Heartbeat

The server sends WebSocket pings every 30 seconds (configurable via `WS_HEARTBEAT_INTERVAL`). Clients that don't respond with a pong are disconnected.

### Close Codes

| Code | Reason |
|------|--------|
| 1001 | Server shutting down |
| 4001 | Authentication required (no token) |
| 4002 | Invalid token |

## Error Handling

The gateway implements comprehensive error handling:

- **Invalid JSON messages** - Returns error message to client
- **Backend unavailable** - Returns 502 Bad Gateway
- **Authentication failures** - Returns 401 Unauthorized
- **WebSocket errors** - Logs and closes connection gracefully

All errors are logged with structured logging using Pino.

## Security

- JWT tokens are verified before allowing WebSocket connections
- CORS is configurable via `CORS_ORIGINS`
- All requests are logged for audit trails
- WebSocket heartbeat detects and removes dead connections
- Graceful shutdown on SIGTERM/SIGINT

## Logging

The gateway uses Pino for structured logging with pretty-printing in development.

Log levels: `debug`, `info`, `warn`, `error`

Example log output:
```
[2024-01-09 10:30:45] INFO: Kalami Gateway running on http://0.0.0.0:3000
[2024-01-09 10:30:45] INFO: WebSocket available at ws://0.0.0.0:3000/ws
[2024-01-09 10:31:12] INFO: Client connected {"connectionId":"abc-123","userId":"user-456"}
```

## Graceful Shutdown

The gateway handles SIGTERM and SIGINT signals:

1. Stops accepting new connections
2. Closes all WebSocket connections with code 1001
3. Closes HTTP server
4. Exits process

## Troubleshooting

### WebSocket connection rejected

- Verify JWT token is valid and not expired
- Check that `JWT_SECRET` matches between gateway and token issuer
- Ensure token is passed in query parameter: `?token=xxx`

### Backend connection failed

- Verify `BACKEND_URL` is correct
- Check that FastAPI backend is running
- Test with: `curl http://localhost:8000/health`

### Port already in use

- Change `GATEWAY_PORT` in .env
- Or stop the process using port 3000: `lsof -ti:3000 | xargs kill`

## License

MIT
