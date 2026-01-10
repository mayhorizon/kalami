// TypeScript type definitions for Kalami mobile app

export interface User {
  id: string;
  email: string;
  name: string;
  native_language: string;
  created_at: string;
}

export interface LearningProfile {
  id: string;
  user_id: string;
  target_language: string;
  cefr_level: CEFRLevel;
  total_practice_time: number;
  conversation_count: number;
  current_streak: number;
  longest_streak: number;
  created_at: string;
  updated_at: string;
}

export type CEFRLevel = 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';

export interface ConversationSession {
  id: string;
  user_id: string;
  profile_id: string;
  topic?: string;
  difficulty_level: CEFRLevel;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  message_count: number;
  words_spoken: number;
  accuracy_score?: number;
}

export interface ConversationMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content_text: string;
  audio_url?: string;
  transcription?: string;
  grammar_corrections?: GrammarCorrection[];
  pronunciation_feedback?: PronunciationFeedback;
  timestamp: string;
}

export interface GrammarCorrection {
  original: string;
  corrected: string;
  explanation: string;
  category: string;
}

export interface PronunciationFeedback {
  overall_score: number;
  problematic_phonemes?: string[];
  suggestions?: string[];
}

export interface Voice {
  id: string;
  name: string;
  language: string;
  gender?: string;
  provider: 'elevenlabs' | 'openai';
}

// API Request/Response types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  native_language: string;
}

export interface CreateProfileRequest {
  target_language: string;
  cefr_level: CEFRLevel;
}

export interface StartSessionRequest {
  profile_id: string;
  topic?: string;
  difficulty_level: CEFRLevel;
}

export interface SendAudioRequest {
  audio_base64: string;
  format: 'mp3' | 'wav' | 'm4a';
}

export interface SendAudioResponse {
  transcription: string;
  response_text: string;
  response_audio_url?: string;
  grammar_corrections?: GrammarCorrection[];
  pronunciation_feedback?: PronunciationFeedback;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'transcription' | 'response' | 'audio' | 'error' | 'connected' | 'heartbeat';
  payload: any;
}

export interface TranscriptionPayload {
  text: string;
  is_final: boolean;
}

export interface ResponsePayload {
  text: string;
  grammar_corrections?: GrammarCorrection[];
}

export interface AudioPayload {
  audio_base64: string;
  format: string;
}

export interface ErrorPayload {
  message: string;
  code?: string;
}

// Audio recording types
export interface AudioRecordingState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  uri?: string;
}

export interface AudioPlaybackState {
  isPlaying: boolean;
  isLoaded: boolean;
  duration: number;
  position: number;
}

// API Error types
export interface APIError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}
