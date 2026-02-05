// User profile and language selection screen
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '@/store/authStore';
import { useConversationStore } from '@/store/conversationStore';
import { LearningProfile, CEFRLevel } from '@/types';

// Cross-platform alert helper
const showAlert = (title: string, message: string) => {
  if (Platform.OS === 'web') {
    window.alert(`${title}\n\n${message}`);
  } else {
    import('react-native').then(({ Alert }) => {
      Alert.alert(title, message);
    });
  }
};

const LANGUAGES = [
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
  { code: 'it', name: 'Italian', flag: '🇮🇹' },
  { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
  { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', flag: '🇰🇷' },
  { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
  { code: 'ar', name: 'Arabic', flag: '🇸🇦' },
  { code: 'ru', name: 'Russian', flag: '🇷🇺' },
];

const CEFR_LEVELS: { level: CEFRLevel; name: string; description: string }[] = [
  { level: 'A1', name: 'Beginner', description: 'Can understand basic phrases' },
  { level: 'A2', name: 'Elementary', description: 'Can communicate simple tasks' },
  { level: 'B1', name: 'Intermediate', description: 'Can handle everyday situations' },
  { level: 'B2', name: 'Upper Intermediate', description: 'Can interact fluently' },
  { level: 'C1', name: 'Advanced', description: 'Can use language flexibly' },
  { level: 'C2', name: 'Proficient', description: 'Can express with precision' },
];

export default function ProfileScreen() {
  const router = useRouter();
  const user = useAuthStore(state => state.user);
  const {
    profiles,
    selectedProfile,
    isLoading,
    loadProfiles,
    selectProfile,
    createProfile,
  } = useConversationStore();

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newLanguage, setNewLanguage] = useState('');
  const [newLevel, setNewLevel] = useState<CEFRLevel>('A1');

  useEffect(() => {
    loadProfiles().catch(error => {
      showAlert('Error', 'Failed to load profiles');
    });
  }, [loadProfiles]);

  const handleSelectProfile = (profile: LearningProfile) => {
    selectProfile(profile);
    router.push('/(main)/conversation');
  };

  const handleCreateProfile = async () => {
    if (!newLanguage) {
      showAlert('Error', 'Please select a language');
      return;
    }

    try {
      await createProfile(newLanguage, newLevel);
      setShowCreateForm(false);
      setNewLanguage('');
      setNewLevel('A1');
      showAlert('Success', 'Learning profile created successfully');
    } catch (error: any) {
      showAlert('Error', 'Failed to create profile');
    }
  };

  const formatPracticeTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const getLanguageInfo = (code: string) => {
    return LANGUAGES.find(lang => lang.code === code) || { name: code, flag: '🌐' };
  };

  const renderProfileCard = (profile: LearningProfile) => {
    const langInfo = getLanguageInfo(profile.target_language);
    const isSelected = selectedProfile?.id === profile.id;

    return (
      <TouchableOpacity
        key={profile.id}
        style={[styles.profileCard, isSelected && styles.profileCardSelected]}
        onPress={() => handleSelectProfile(profile)}
      >
        <View style={styles.profileHeader}>
          <Text style={styles.profileFlag}>{langInfo.flag}</Text>
          <View style={styles.profileInfo}>
            <Text style={styles.profileLanguage}>{langInfo.name}</Text>
            <Text style={styles.profileLevel}>Level: {profile.cefr_level}</Text>
          </View>
          {isSelected && <Text style={styles.selectedBadge}>✓</Text>}
        </View>

        <View style={styles.profileStats}>
          <View style={styles.stat}>
            <Text style={styles.statValue}>{profile.conversation_count}</Text>
            <Text style={styles.statLabel}>Conversations</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.statValue}>
              {formatPracticeTime(profile.total_practice_time)}
            </Text>
            <Text style={styles.statLabel}>Practice Time</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.statValue}>{profile.current_streak}</Text>
            <Text style={styles.statLabel}>Day Streak</Text>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Text style={styles.backIcon}>←</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Profile</Text>
          <View style={styles.headerSpacer} />
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.userSection}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{user?.email?.charAt(0).toUpperCase() || '?'}</Text>
            </View>
            <Text style={styles.userEmail}>{user?.email}</Text>
            <Text style={styles.nativeLanguage}>
              Native: {user?.native_language?.toUpperCase() || 'EN'}
            </Text>
          </View>

          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Learning Profiles</Text>
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => setShowCreateForm(!showCreateForm)}
              >
                <Text style={styles.addButtonText}>
                  {showCreateForm ? '✕' : '+ Add'}
                </Text>
              </TouchableOpacity>
            </View>

            {showCreateForm && (
              <View style={styles.createForm}>
                <Text style={styles.formLabel}>Select Language</Text>
                <View style={styles.languageGrid}>
                  {LANGUAGES.map((lang) => (
                    <TouchableOpacity
                      key={lang.code}
                      style={[
                        styles.languageOption,
                        newLanguage === lang.code && styles.languageOptionSelected,
                      ]}
                      onPress={() => setNewLanguage(lang.code)}
                    >
                      <Text style={styles.languageFlag}>{lang.flag}</Text>
                      <Text style={styles.languageName}>{lang.name}</Text>
                    </TouchableOpacity>
                  ))}
                </View>

                <Text style={styles.formLabel}>Select Level</Text>
                <View style={styles.levelList}>
                  {CEFR_LEVELS.map((level) => (
                    <TouchableOpacity
                      key={level.level}
                      style={[
                        styles.levelOption,
                        newLevel === level.level && styles.levelOptionSelected,
                      ]}
                      onPress={() => setNewLevel(level.level)}
                    >
                      <Text
                        style={[
                          styles.levelCode,
                          newLevel === level.level && styles.levelCodeSelected,
                        ]}
                      >
                        {level.level}
                      </Text>
                      <View style={styles.levelInfo}>
                        <Text
                          style={[
                            styles.levelName,
                            newLevel === level.level && styles.levelNameSelected,
                          ]}
                        >
                          {level.name}
                        </Text>
                        <Text style={styles.levelDescription}>{level.description}</Text>
                      </View>
                    </TouchableOpacity>
                  ))}
                </View>

                <TouchableOpacity
                  style={[styles.createButton, isLoading && styles.createButtonDisabled]}
                  onPress={handleCreateProfile}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text style={styles.createButtonText}>Create Profile</Text>
                  )}
                </TouchableOpacity>
              </View>
            )}

            {profiles.length === 0 && !showCreateForm ? (
              <View style={styles.emptyProfiles}>
                <Text style={styles.emptyIcon}>🌍</Text>
                <Text style={styles.emptyText}>
                  No learning profiles yet. Create one to start practicing!
                </Text>
              </View>
            ) : (
              <View style={styles.profilesList}>
                {profiles.map(renderProfileCard)}
              </View>
            )}
          </View>
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#fff',
  },
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backIcon: {
    fontSize: 24,
    color: '#007AFF',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  headerSpacer: {
    width: 40,
  },
  scrollContent: {
    paddingBottom: 32,
  },
  userSection: {
    alignItems: 'center',
    paddingVertical: 32,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5E5',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 36,
    color: '#fff',
    fontWeight: '600',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  nativeLanguage: {
    fontSize: 12,
    color: '#999',
  },
  section: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  addButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  createForm: {
    backgroundColor: '#F5F5F5',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  formLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  languageGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 20,
  },
  languageOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#E5E5E5',
    gap: 6,
  },
  languageOptionSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#E8F4FF',
  },
  languageFlag: {
    fontSize: 20,
  },
  languageName: {
    fontSize: 14,
    fontWeight: '500',
  },
  levelList: {
    gap: 8,
    marginBottom: 16,
  },
  levelOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#E5E5E5',
    gap: 12,
  },
  levelOptionSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#E8F4FF',
  },
  levelCode: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#666',
    width: 36,
  },
  levelCodeSelected: {
    color: '#007AFF',
  },
  levelInfo: {
    flex: 1,
  },
  levelName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  levelNameSelected: {
    color: '#007AFF',
  },
  levelDescription: {
    fontSize: 13,
    color: '#666',
  },
  createButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  createButtonDisabled: {
    opacity: 0.5,
  },
  createButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyProfiles: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  profilesList: {
    gap: 12,
  },
  profileCard: {
    backgroundColor: '#F5F5F5',
    padding: 16,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  profileCardSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#E8F4FF',
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  profileFlag: {
    fontSize: 32,
    marginRight: 12,
  },
  profileInfo: {
    flex: 1,
  },
  profileLanguage: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  profileLevel: {
    fontSize: 14,
    color: '#666',
  },
  selectedBadge: {
    fontSize: 24,
    color: '#007AFF',
  },
  profileStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  stat: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
  },
});
