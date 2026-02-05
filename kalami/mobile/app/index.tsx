// Home/landing screen - redirects based on auth status
import { useEffect, useState } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter, useRootNavigationState } from 'expo-router';
import { useAuthStore } from '@/store/authStore';

export default function Index() {
  const router = useRouter();
  const rootNavigationState = useRootNavigationState();
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const isLoading = useAuthStore(state => state.isLoading);

  useEffect(() => {
    // Wait for navigation to be ready and auth check to complete
    if (!rootNavigationState?.key) return;

    if (!isLoading) {
      if (isAuthenticated) {
        router.replace('/(main)/conversation');
      } else {
        router.replace('/(auth)/login');
      }
    }
  }, [isAuthenticated, isLoading, router, rootNavigationState?.key]);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#007AFF" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
});
