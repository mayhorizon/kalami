// REST API client for Kalami backend
import * as SecureStore from 'expo-secure-store';
import {
  User,
  LearningProfile,
  ConversationSession,
  ConversationMessage,
  Voice,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  CreateProfileRequest,
  StartSessionRequest,
  SendAudioRequest,
  SendAudioResponse,
  APIError,
} from '@/types';

const API_BASE_URL = __DEV__
  ? 'http://localhost:3000/api'
  : 'https://api.kalami.app/api';

const TOKEN_KEY = 'kalami_auth_token';

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  // Token management
  async getToken(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(TOKEN_KEY);
    } catch (error) {
      console.error('Failed to retrieve token:', error);
      return null;
    }
  }

  async setToken(token: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(TOKEN_KEY, token);
    } catch (error) {
      console.error('Failed to store token:', error);
      throw error;
    }
  }

  async removeToken(): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
    } catch (error) {
      console.error('Failed to remove token:', error);
    }
  }

  // Generic request handler
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await this.getToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          message: response.statusText,
        }));

        const error: APIError = {
          message: errorData.detail || errorData.message || 'Request failed',
          status: response.status,
          code: errorData.code,
          details: errorData,
        };

        throw error;
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return {} as T;
      }

      return await response.json();
    } catch (error) {
      if ((error as APIError).status) {
        throw error;
      }

      // Network or other errors
      const apiError: APIError = {
        message: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
      throw apiError;
    }
  }

  // Authentication endpoints
  async register(data: RegisterRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    await this.setToken(response.access_token);
    return response;
  }

  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    await this.setToken(response.access_token);
    return response;
  }

  async logout(): Promise<void> {
    await this.removeToken();
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // User profile endpoints
  async getLearningProfiles(): Promise<LearningProfile[]> {
    return this.request<LearningProfile[]>('/users/profiles');
  }

  async createLearningProfile(data: CreateProfileRequest): Promise<LearningProfile> {
    return this.request<LearningProfile>('/users/profiles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getUserStats(): Promise<{
    total_practice_time: number;
    total_conversations: number;
    current_streak: number;
    longest_streak: number;
  }> {
    return this.request('/users/stats');
  }

  // Conversation endpoints
  async startSession(data: StartSessionRequest): Promise<ConversationSession> {
    return this.request<ConversationSession>('/conversations/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async endSession(sessionId: string): Promise<ConversationSession> {
    return this.request<ConversationSession>(
      `/conversations/sessions/${sessionId}/end`,
      {
        method: 'POST',
      }
    );
  }

  async getSessionMessages(sessionId: string): Promise<ConversationMessage[]> {
    return this.request<ConversationMessage[]>(
      `/conversations/sessions/${sessionId}/messages`
    );
  }

  async sendAudio(
    sessionId: string,
    data: SendAudioRequest
  ): Promise<SendAudioResponse> {
    return this.request<SendAudioResponse>(
      `/conversations/sessions/${sessionId}/audio`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async sendText(
    sessionId: string,
    text: string
  ): Promise<SendAudioResponse> {
    return this.request<SendAudioResponse>(
      `/conversations/sessions/${sessionId}/text`,
      {
        method: 'POST',
        body: JSON.stringify({ text }),
      }
    );
  }

  // Speech endpoints
  async transcribeAudio(audioBase64: string, format: string): Promise<{ text: string }> {
    return this.request<{ text: string }>('/speech/transcribe', {
      method: 'POST',
      body: JSON.stringify({ audio_base64: audioBase64, format }),
    });
  }

  async synthesizeSpeech(
    text: string,
    voiceId?: string,
    language?: string
  ): Promise<{ audio_base64: string }> {
    return this.request<{ audio_base64: string }>('/speech/synthesize', {
      method: 'POST',
      body: JSON.stringify({ text, voice_id: voiceId, language }),
    });
  }

  async getVoices(): Promise<Voice[]> {
    return this.request<Voice[]>('/speech/voices');
  }
}

export const apiClient = new APIClient(API_BASE_URL);
export default apiClient;
