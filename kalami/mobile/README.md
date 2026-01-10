# Kalami Mobile App

React Native mobile application for Kalami - AI Language Learning Assistant.

## Features

- **Voice Conversation**: Real-time voice conversations with AI language tutor
- **Audio Recording**: High-quality 16kHz audio recording using expo-av
- **WebSocket Streaming**: Real-time transcription and responses
- **Multi-Language Support**: Practice Spanish, French, German, and more
- **CEFR Level Tracking**: Track progress from A1 (Beginner) to C2 (Proficient)
- **Grammar Corrections**: Get instant feedback on grammar mistakes
- **Pronunciation Analysis**: Receive phoneme-level pronunciation feedback
- **Progress Tracking**: Monitor practice time, streaks, and conversation count

## Prerequisites

- Node.js v18+ (v24.12.0 installed via nvm)
- npm or yarn
- Expo CLI
- iOS Simulator (Mac) or Android Emulator
- Physical device with Expo Go app (recommended for audio testing)

## Installation

1. Navigate to the mobile directory:
```bash
cd /home/savetheworld/kalami/mobile
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Update `.env` with your API URLs if needed (defaults to localhost)

## Running the App

### Development Mode

Start the Expo development server:
```bash
npm start
```

This will open Expo DevTools in your browser. From there you can:
- Press `i` to open iOS Simulator
- Press `a` to open Android Emulator
- Scan QR code with Expo Go app on your physical device

### Platform-Specific Commands

Run on iOS Simulator:
```bash
npm run ios
```

Run on Android Emulator:
```bash
npm run android
```

Run on web (limited audio support):
```bash
npm run web
```

## Project Structure

```
mobile/
├── app/                          # Expo Router screens
│   ├── _layout.tsx              # Root layout with providers
│   ├── index.tsx                # Home/redirect screen
│   ├── (auth)/
│   │   ├── login.tsx            # Login screen
│   │   └── register.tsx         # Registration screen
│   └── (main)/
│       ├── conversation.tsx     # Main conversation screen
│       └── profile.tsx          # User profile & language selection
├── components/
│   ├── AudioRecorder.tsx        # Hold-to-record audio button
│   ├── ConversationBubble.tsx   # Chat message bubble
│   └── WaveformVisualizer.tsx   # Animated audio waveform
├── hooks/
│   ├── useAudio.ts              # Audio recording/playback hook
│   └── useWebSocket.ts          # WebSocket connection hook
├── services/
│   ├── api.ts                   # REST API client
│   └── websocket.ts             # WebSocket client
├── store/
│   ├── authStore.ts             # Authentication state (Zustand)
│   └── conversationStore.ts     # Conversation state (Zustand)
├── types/
│   └── index.ts                 # TypeScript type definitions
├── app.json                     # Expo configuration
├── package.json                 # Dependencies
└── tsconfig.json                # TypeScript configuration
```

## Key Technologies

- **Framework**: React Native with Expo SDK 50
- **Navigation**: Expo Router (file-based routing)
- **State Management**: Zustand (lightweight state management)
- **Server State**: TanStack Query (React Query)
- **Audio**: expo-av (recording and playback)
- **Storage**: expo-secure-store (JWT token storage)
- **Haptics**: expo-haptics (tactile feedback)
- **WebSocket**: Native WebSocket API
- **TypeScript**: Full type safety

## Audio Configuration

The app records audio at 16kHz sample rate (optimal for speech-to-text):

- **iOS**: M4A format, AAC encoding
- **Android**: M4A format, AAC encoding
- **Sample Rate**: 16000 Hz
- **Channels**: Mono (1 channel)
- **Bit Rate**: 128 kbps

## API Endpoints

The app connects to the API Gateway at `http://localhost:3000` (development).

### REST API Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `GET /api/users/profiles` - List learning profiles
- `POST /api/users/profiles` - Create learning profile
- `POST /api/conversations/sessions` - Start conversation
- `POST /api/conversations/sessions/:id/end` - End conversation
- `POST /api/conversations/sessions/:id/audio` - Send audio

### WebSocket Connection
- `ws://localhost:3000/ws?token={JWT_TOKEN}`

WebSocket message types:
- `connected` - Connection established
- `transcription` - Real-time speech-to-text
- `response` - AI response with corrections
- `audio` - TTS audio response
- `error` - Error messages
- `heartbeat` - Keep-alive ping/pong

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Development (default)
API_BASE_URL=http://localhost:3000/api
WS_BASE_URL=ws://localhost:3000/ws

# Production
# API_BASE_URL=https://api.kalami.app/api
# WS_BASE_URL=wss://api.kalami.app/ws
```

**Note**: URLs are hardcoded in `services/api.ts` and `services/websocket.ts` with `__DEV__` checks.

## Testing on Physical Device

For best audio quality testing, use a physical device:

1. Install Expo Go app from App Store or Google Play
2. Run `npm start` on your development machine
3. Scan the QR code with your device
4. Ensure your device and computer are on the same network

**Important**: Localhost URLs won't work on physical devices. Use your computer's IP address:
```
API_BASE_URL=http://192.168.1.100:3000/api
WS_BASE_URL=ws://192.168.1.100:3000/ws
```

## Permissions

The app requires the following permissions:

- **Microphone**: Required for audio recording
- **Speech Recognition**: Used for voice-to-text transcription (iOS)

Permissions are requested automatically when the app starts.

## Common Issues

### Audio Recording Not Working
- Check microphone permissions in device settings
- Ensure you're testing on a physical device or simulator with microphone support
- Verify expo-av is properly installed: `npx expo install expo-av`

### WebSocket Connection Fails
- Ensure the API Gateway is running on port 3000
- Check that JWT token is valid and not expired
- Verify network connectivity
- Check console for connection errors

### "Cannot find module" Errors
- Run `npm install` to install all dependencies
- Clear Metro bundler cache: `npx expo start -c`

### Expo Go Errors
- Update to latest Expo Go app version
- Ensure SDK versions match between app and Expo Go
- Try restarting the Expo development server

## Building for Production

### iOS

1. Configure app signing in `app.json`
2. Build the app:
```bash
npx eas build --platform ios
```

### Android

1. Configure signing keystore
2. Build the app:
```bash
npx eas build --platform android
```

Refer to [Expo EAS Build documentation](https://docs.expo.dev/build/introduction/) for detailed instructions.

## Development Workflow

1. **Start Backend Services**:
```bash
# Terminal 1 - Backend
cd ../backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 - Gateway
cd ../gateway && npm run dev
```

2. **Start Mobile App**:
```bash
# Terminal 3 - Mobile
npm start
```

3. **Development Tips**:
   - Use `console.log` for debugging (visible in terminal)
   - Enable Remote Debugging in Expo DevTools
   - Use React DevTools for component inspection
   - Enable Fast Refresh for instant updates

## Code Quality

- TypeScript strict mode enabled
- ESLint and Prettier recommended (not configured)
- All API calls have proper error handling
- Zustand stores are typed
- WebSocket reconnection logic implemented
- Secure token storage with expo-secure-store

## Contributing

When adding new features:
1. Follow existing file structure
2. Add TypeScript types to `types/index.ts`
3. Use Zustand for global state
4. Use React Query for server state
5. Handle all errors gracefully
6. Test on both iOS and Android

## License

Proprietary - Kalami Language Learning
