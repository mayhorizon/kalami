# Quick Start Guide

## Installation & Testing (3 Minutes)

### Option 1: Automated Setup
```bash
cd /home/savetheworld/kalami/gateway
./setup.sh
```

### Option 2: Manual Steps
```bash
cd /home/savetheworld/kalami/gateway

# Install dependencies
npm install

# Build TypeScript
npm run build

# Run tests
npm test

# Create .env file
cp .env.example .env

# Start development server
npm run dev
```

## Verify Installation

### Test Health Endpoint
```bash
curl http://localhost:3000/health
```

Expected response:
```json
{"status":"healthy","service":"kalami-gateway","version":"0.1.0"}
```

### Test WebSocket

Generate token:
```bash
node -e "const jwt=require('jsonwebtoken');console.log(jwt.sign({sub:'test'},'your-secret-key-change-in-production',{expiresIn:'1h'}))"
```

Connect (requires wscat):
```bash
npm install -g wscat
wscat -c "ws://localhost:3000/ws?token=PASTE_TOKEN_HERE"
```

## What Was Fixed

**File:** `src/middleware/auth.ts` line 69

**Before (broken):**
```typescript
const decoded = jwt.verify(token, config.jwtSecret);
// ❌ token is undefined
```

**After (fixed):**
```typescript
const token = parts[1];  // ✓ Extract from header
const decoded = jwt.verify(token, config.jwtSecret);
```

## Files Created

- `vitest.config.ts` - Test configuration
- `tests/gateway.test.ts` - 16 comprehensive tests
- `.env.example` - Configuration template
- `.gitignore` - Git ignore rules
- `.eslintrc.json` - Linting rules
- `README.md` - Full documentation
- `setup.sh` - Setup script
- `MANUAL_TESTING.md` - Testing guide
- `TEST_REPORT.md` - Analysis report
- `FINAL_STATUS.md` - Status summary
- `QUICK_START.md` - This file

## Test Coverage

✓ 4 Health endpoint tests
✓ 4 JWT authentication tests
✓ 7 WebSocket connection tests
✓ 1 Error handling test

**Total: 16 tests**

## Next Steps

1. Run `npm install`
2. Run `npm test` (all should pass)
3. Review `.env.example` and create `.env`
4. Start backend: `http://localhost:8000`
5. Run `npm run dev`
6. Test endpoints with curl
7. Deploy to production

## Production Checklist

Before deploying:
- [ ] Change `JWT_SECRET` in `.env`
- [ ] Set `CORS_ORIGINS` to specific domains
- [ ] Set `LOG_LEVEL=warn`
- [ ] Use HTTPS/WSS
- [ ] Set up reverse proxy
- [ ] Enable monitoring

## Support

- **Full docs:** README.md
- **Testing guide:** MANUAL_TESTING.md
- **Status report:** FINAL_STATUS.md
- **Test analysis:** TEST_REPORT.md
