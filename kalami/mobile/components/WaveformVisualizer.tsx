// Visual audio feedback component with animated waveform
import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';

interface WaveformVisualizerProps {
  isActive: boolean;
  barCount?: number;
  color?: string;
}

export function WaveformVisualizer({
  isActive,
  barCount = 5,
  color = '#007AFF'
}: WaveformVisualizerProps) {
  const animations = useRef<Animated.Value[]>(
    Array.from({ length: barCount }, () => new Animated.Value(0.2))
  ).current;

  useEffect(() => {
    if (isActive) {
      // Create staggered animations for each bar
      const animationSequences = animations.map((anim, index) => {
        return Animated.loop(
          Animated.sequence([
            Animated.timing(anim, {
              toValue: 1,
              duration: 300 + index * 50,
              useNativeDriver: true,
            }),
            Animated.timing(anim, {
              toValue: 0.2,
              duration: 300 + index * 50,
              useNativeDriver: true,
            }),
          ])
        );
      });

      // Start all animations with slight delay for wave effect
      animationSequences.forEach((animation, index) => {
        setTimeout(() => animation.start(), index * 50);
      });

      return () => {
        animationSequences.forEach(animation => animation.stop());
      };
    } else {
      // Reset to minimum height when inactive
      animations.forEach(anim => {
        Animated.timing(anim, {
          toValue: 0.2,
          duration: 200,
          useNativeDriver: true,
        }).start();
      });
    }
  }, [isActive, animations]);

  return (
    <View style={styles.container}>
      {animations.map((animation, index) => (
        <Animated.View
          key={index}
          style={[
            styles.bar,
            {
              backgroundColor: color,
              transform: [{ scaleY: animation }],
            },
          ]}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 40,
    gap: 4,
  },
  bar: {
    width: 4,
    height: 40,
    borderRadius: 2,
  },
});
