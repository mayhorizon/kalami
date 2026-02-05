// Zustand store for conversation state
import { create } from 'zustand';
import { Platform } from 'react-native';
import { ConversationSession, ConversationMessage, LearningProfile } from '@/types';
import apiClient from '@/services/api';

const SELECTED_PROFILE_KEY = 'kalami_selected_profile_id';

// Helper to save/load selected profile ID (web only for now)
const saveSelectedProfileId = (profileId: string | null) => {
  try {
    if (Platform.OS === 'web' && typeof localStorage !== 'undefined') {
      if (profileId) {
        localStorage.setItem(SELECTED_PROFILE_KEY, profileId);
      } else {
        localStorage.removeItem(SELECTED_PROFILE_KEY);
      }
    }
  } catch (e) {
    console.error('Failed to save selected profile:', e);
  }
};

const loadSelectedProfileId = (): string | null => {
  try {
    if (Platform.OS === 'web' && typeof localStorage !== 'undefined') {
      return localStorage.getItem(SELECTED_PROFILE_KEY);
    }
    return null;
  } catch (e) {
    console.error('Failed to load selected profile:', e);
    return null;
  }
};

interface ConversationState {
  currentSession: ConversationSession | null;
  messages: ConversationMessage[];
  selectedProfile: LearningProfile | null;
  profiles: LearningProfile[];
  isLoading: boolean;
  error: string | null;

  // Realtime transcription state
  currentTranscription: string;
  isSpeaking: boolean;

  // Actions
  loadProfiles: () => Promise<void>;
  selectProfile: (profile: LearningProfile) => void;
  createProfile: (targetLanguage: string, cefrLevel: string) => Promise<void>;

  startSession: (topic?: string) => Promise<void>;
  endSession: () => Promise<void>;

  addMessage: (message: ConversationMessage) => void;
  loadMessages: () => Promise<void>;

  setCurrentTranscription: (text: string) => void;
  setIsSpeaking: (speaking: boolean) => void;

  clearError: () => void;
  reset: () => void;
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  currentSession: null,
  messages: [],
  selectedProfile: null,
  profiles: [],
  isLoading: false,
  error: null,
  currentTranscription: '',
  isSpeaking: false,

  loadProfiles: async () => {
    set({ isLoading: true, error: null });

    try {
      const profiles = await apiClient.getLearningProfiles();
      set({
        profiles,
        isLoading: false,
        error: null,
      });

      // Restore previously selected profile or default to first
      if (!get().selectedProfile && profiles.length > 0) {
        const savedProfileId = loadSelectedProfileId();
        const savedProfile = savedProfileId
          ? profiles.find(p => p.id === savedProfileId)
          : null;
        set({ selectedProfile: savedProfile || profiles[0] });
      }
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to load profiles',
      });
      throw error;
    }
  },

  selectProfile: (profile: LearningProfile) => {
    set({ selectedProfile: profile });
    saveSelectedProfileId(profile.id);  // Persist selection
  },

  createProfile: async (targetLanguage: string, cefrLevel: string) => {
    set({ isLoading: true, error: null });

    try {
      const profile = await apiClient.createLearningProfile({
        target_language: targetLanguage,
        cefr_level: cefrLevel as any,
      });

      set((state) => ({
        profiles: [...state.profiles, profile],
        selectedProfile: profile,
        isLoading: false,
        error: null,
      }));
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to create profile',
      });
      throw error;
    }
  },

  startSession: async (topic?: string) => {
    const { selectedProfile } = get();

    if (!selectedProfile) {
      set({ error: 'No learning profile selected' });
      throw new Error('No learning profile selected');
    }

    set({ isLoading: true, error: null });

    try {
      const session = await apiClient.startSession({
        profile_id: selectedProfile.id,
        topic,
        difficulty_level: selectedProfile.cefr_level,
      });

      set({
        currentSession: session,
        messages: [],
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to start session',
      });
      throw error;
    }
  },

  endSession: async () => {
    const { currentSession } = get();

    if (!currentSession) {
      return;
    }

    set({ isLoading: true, error: null });

    try {
      const updatedSession = await apiClient.endSession(currentSession.id);
      set({
        currentSession: null,
        messages: [],
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      console.error('Failed to end session:', error);
      // Still clear the session locally
      set({
        currentSession: null,
        messages: [],
        isLoading: false,
        error: null,
      });
    }
  },

  addMessage: (message: ConversationMessage) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },

  loadMessages: async () => {
    const { currentSession } = get();

    if (!currentSession) {
      return;
    }

    set({ isLoading: true, error: null });

    try {
      const messages = await apiClient.getSessionMessages(currentSession.id);
      set({
        messages,
        isLoading: false,
        error: null,
      });
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.message || 'Failed to load messages',
      });
    }
  },

  setCurrentTranscription: (text: string) => {
    set({ currentTranscription: text });
  },

  setIsSpeaking: (speaking: boolean) => {
    set({ isSpeaking: speaking });
  },

  clearError: () => set({ error: null }),

  reset: () => {
    set({
      currentSession: null,
      messages: [],
      currentTranscription: '',
      isSpeaking: false,
      error: null,
    });
  },
}));
