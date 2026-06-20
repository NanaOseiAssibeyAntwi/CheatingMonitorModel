import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { layout, palette, type } from '@/constants/design';

const monitoringModes = [
  {
    description: 'Gaze, face detection, app monitoring',
    title: 'Standard',
  },
  {
    description: 'All standard + audio + room scan',
    title: 'Strict',
  },
  {
    description: 'Face detection only',
    title: 'Minimal',
  },
] as const;

const aiFeatures = [
  'Real-time gaze tracking',
  'Multi-face detection',
  'App switch detection',
  'Audio anomaly detection',
];

export default function InvigilatorCreateScreen() {
  const [mode, setMode] = useState('Standard');

  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerRow}>
          <Pressable
            onPress={() => router.navigate('/(invigilator-tabs)')}
            style={styles.backButton}>
            <Feather color={palette.mutedStrong} name="chevron-left" size={18} />
          </Pressable>
          <Text style={styles.eyebrow}>NEW SESSION</Text>
        </View>

        <Text style={styles.title}>Create Exam Session</Text>

        <View style={styles.formGroup}>
          <Text style={styles.label}>COURSE CODE</Text>
          <TextInput style={styles.input} value="CS 450" />
        </View>

        <View style={styles.formGroup}>
          <Text style={styles.label}>COURSE NAME</Text>
          <TextInput style={styles.input} value="Computer Networks" />
        </View>

        <View style={styles.twoUp}>
          <View style={styles.twoUpItem}>
            <Text style={styles.label}>DATE</Text>
            <View style={styles.inputWithIcon}>
              <TextInput
                placeholder="mm/dd/yyyy"
                placeholderTextColor={palette.text}
                style={styles.inputInline}
              />
              <Feather color={palette.mutedStrong} name="calendar" size={15} />
            </View>
          </View>
          <View style={styles.twoUpItem}>
            <Text style={styles.label}>START TIME</Text>
            <View style={styles.inputWithIcon}>
              <TextInput
                placeholder="--:-- --"
                placeholderTextColor={palette.text}
                style={styles.inputInline}
              />
              <Feather color={palette.mutedStrong} name="clock" size={15} />
            </View>
          </View>
        </View>

        <View style={styles.twoUp}>
          <View style={styles.twoUpItem}>
            <Text style={styles.label}>DURATION (HRS)</Text>
            <View style={styles.inputWithIcon}>
              <TextInput style={styles.inputInline} value="3" />
              <Feather color={palette.mutedStrong} name="chevron-down" size={15} />
            </View>
          </View>
          <View style={styles.twoUpItem}>
            <Text style={styles.label}>MAX STUDENTS</Text>
            <TextInput style={styles.input} value="50" />
          </View>
        </View>

        <Text style={[styles.label, styles.modeLabel]}>MONITORING MODE</Text>
        <View style={styles.modeList}>
          {monitoringModes.map((item) => {
            const active = item.title === mode;

            return (
              <Pressable
                key={item.title}
                onPress={() => setMode(item.title)}
                style={[styles.modeCard, active ? styles.modeCardActive : null]}>
                <View style={[styles.modeIndicator, active ? styles.modeIndicatorActive : null]} />
                <View>
                  <Text style={styles.modeTitle}>{item.title}</Text>
                  <Text style={styles.modeDescription}>{item.description}</Text>
                </View>
              </Pressable>
            );
          })}
        </View>

        <View style={styles.featureCard}>
          <Text style={styles.label}>AI FEATURES</Text>
          <View style={styles.featureList}>
            {aiFeatures.map((feature) => (
              <View key={feature} style={styles.featureRow}>
                <View style={styles.featureDot} />
                <Text style={styles.featureText}>{feature}</Text>
              </View>
            ))}
          </View>
        </View>

        <Pressable style={styles.primaryButton}>
          <Text style={styles.primaryButtonText}>Create Session</Text>
        </Pressable>

        <Pressable onPress={() => router.back()} style={styles.secondaryButton}>
          <Text style={styles.secondaryButtonText}>Cancel</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  backButton: {
    alignItems: 'center',
    height: 28,
    justifyContent: 'center',
    width: 28,
  },
  content: {
    alignSelf: 'center',
    maxWidth: layout.maxWidth,
    paddingBottom: layout.bottomPadding,
    paddingHorizontal: layout.screenPaddingWide,
    width: '100%',
  },
  eyebrow: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 2.2,
  },
  featureCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    marginTop: 16,
    paddingHorizontal: 14,
    paddingVertical: 16,
  },
  featureDot: {
    backgroundColor: palette.success,
    borderRadius: 99,
    height: 5,
    marginTop: 6,
    width: 5,
  },
  featureList: {
    gap: 10,
    marginTop: 14,
  },
  featureRow: {
    flexDirection: 'row',
    gap: 8,
  },
  featureText: {
    color: '#7fd8ff',
    fontSize: type.bodyLarge,
  },
  formGroup: {
    marginTop: 18,
  },
  headerRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  input: {
    backgroundColor: '#050d18',
    borderColor: palette.border,
    borderWidth: 1,
    color: palette.text,
    fontSize: type.bodyLarge,
    marginTop: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  inputInline: {
    color: palette.text,
    flex: 1,
    fontSize: type.bodyLarge,
    paddingVertical: 12,
  },
  inputWithIcon: {
    alignItems: 'center',
    backgroundColor: '#050d18',
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
    paddingHorizontal: 14,
  },
  label: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 2,
  },
  modeCard: {
    alignItems: 'flex-start',
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  modeCardActive: {
    backgroundColor: '#062126',
    borderColor: '#0d8b86',
  },
  modeDescription: {
    color: palette.mutedStrong,
    fontSize: type.body,
    marginTop: 6,
  },
  modeIndicator: {
    borderColor: palette.border,
    borderWidth: 1,
    height: 14,
    marginTop: 3,
    width: 14,
  },
  modeIndicatorActive: {
    backgroundColor: palette.teal,
    borderColor: palette.teal,
  },
  modeLabel: {
    marginTop: 18,
  },
  modeList: {
    gap: 8,
    marginTop: 10,
  },
  modeTitle: {
    color: palette.text,
    fontSize: type.bodyLarge + 1,
    fontWeight: '700',
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: '#d7a413',
    marginTop: 18,
    paddingVertical: 15,
  },
  primaryButtonText: {
    color: '#1a1300',
    fontSize: type.bodyLarge,
    fontWeight: '800',
  },
  safeArea: {
    backgroundColor: palette.background,
    flex: 1,
  },
  secondaryButton: {
    alignItems: 'center',
    borderColor: palette.border,
    borderWidth: 1,
    marginTop: 10,
    paddingVertical: 14,
  },
  secondaryButtonText: {
    color: palette.mutedStrong,
    fontSize: type.bodyLarge,
  },
  title: {
    color: palette.text,
    fontSize: type.title,
    fontWeight: '800',
    marginTop: 22,
  },
  twoUp: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 18,
  },
  twoUpItem: {
    flex: 1,
  },
});
