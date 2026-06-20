import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { layout, palette, type } from '@/constants/design';

const checks = [
  { label: 'GAZE COMPLIANCE', fill: 85, value: '85%' },
  { label: 'FACE DETECTION', fill: 92, value: '92%' },
  { label: 'APP FOCUS', fill: 97, value: '97%' },
  { label: 'AUDIO ENVIRONMENT', fill: 88, value: '88%' },
] as const;

const stats = [
  { label: 'QUESTIONS', value: '30/30' },
  { label: 'DURATION', value: '2h 58m' },
  { label: 'FLAGS', value: '1' },
];

const log = [
  { detail: 'Gaze deviation detected', time: '10:14' },
  { detail: 'AI systems nominal', time: '10:28' },
  { detail: 'Exam submitted by student', time: '10:45' },
];

export default function ResultsScreen() {
  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.heroCard}>
          <View>
            <Text style={styles.eyebrow}>POST-EXAM REPORT</Text>
            <Text style={styles.title}>Computer Networks</Text>
            <Text style={styles.meta}>CS 450 - 09 Jun 2025 - 10:00-13:00</Text>
          </View>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>COMPLETED</Text>
          </View>
        </View>

        <View style={styles.sectionBlock}>
          <Text style={styles.sectionLabel}>OVERALL INTEGRITY</Text>

          <View style={styles.integrityRow}>
            <View style={styles.ringWrap}>
              <View style={styles.ringOuter}>
                <View style={styles.ringCutout} />
                <View style={styles.ringInner}>
                  <Text style={styles.ringValue}>90</Text>
                  <Text style={styles.ringScale}>/ 100</Text>
                </View>
              </View>
            </View>

            <View style={styles.integrityCopyWrap}>
              <Text style={styles.integrityTitle}>High Integrity</Text>
              <Text style={styles.integrityCopy}>
                Exam completed with minimal integrity flags. 1 minor gaze deviation recorded.
              </Text>
            </View>
          </View>

          <View style={styles.checkList}>
            {checks.map((check) => (
              <View key={check.label} style={styles.checkRow}>
                <Text style={styles.checkLabel}>{check.label}</Text>
                <View style={styles.track}>
                  <View style={[styles.trackFill, { width: `${check.fill}%` }]} />
                </View>
                <Text style={styles.checkValue}>{check.value}</Text>
              </View>
            ))}
          </View>

          <View style={styles.divider} />

          <View style={styles.statsRow}>
            {stats.map((item) => (
              <View key={item.label} style={styles.statCard}>
                <Text style={styles.statValue}>{item.value}</Text>
                <Text style={styles.statLabel}>{item.label}</Text>
              </View>
            ))}
          </View>

          <View style={styles.divider} />

          <Text style={styles.sectionLabel}>SESSION LOG</Text>
          <View style={styles.logList}>
            {log.map((item) => (
              <View key={item.time} style={styles.logRow}>
                <Text style={styles.logTime}>{item.time}</Text>
                <View style={styles.logDot} />
                <Text style={styles.logDetail}>{item.detail}</Text>
              </View>
            ))}
          </View>

          <Pressable style={styles.primaryButton}>
            <Feather color="#032228" name="download" size={16} />
            <Text style={styles.primaryButtonText}>Download Report</Text>
          </Pressable>

          <Pressable onPress={() => router.navigate('/(tabs)')} style={styles.secondaryButton}>
            <Feather color={palette.mutedStrong} name="home" size={15} />
            <Text style={styles.secondaryButtonText}>Back to Home</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignItems: 'center',
    borderColor: '#107f5f',
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 44,
    minWidth: 88,
    paddingHorizontal: 10,
  },
  badgeText: {
    color: palette.success,
    fontSize: type.tiny,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  checkLabel: {
    color: palette.mutedStrong,
    fontSize: type.tiny,
    width: 88,
  },
  checkList: {
    gap: 12,
    marginTop: 22,
  },
  checkRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  checkValue: {
    color: palette.success,
    fontSize: 12,
    fontWeight: '700',
    width: 34,
  },
  content: {
    alignSelf: 'center',
    maxWidth: layout.maxWidth,
    paddingBottom: layout.bottomPadding,
    paddingHorizontal: layout.screenPaddingWide,
    width: '100%',
  },
  divider: {
    backgroundColor: palette.border,
    height: 1,
    marginTop: 22,
    width: '100%',
  },
  eyebrow: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 2.2,
    marginTop: 2,
  },
  heroCard: {
    alignItems: 'flex-start',
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
    paddingHorizontal: 14,
    paddingVertical: 16,
  },
  integrityCopy: {
    color: palette.mutedStrong,
    fontSize: type.body,
    lineHeight: 20,
    marginTop: 8,
  },
  integrityCopyWrap: {
    flex: 1,
    paddingLeft: 16,
  },
  integrityRow: {
    flexDirection: 'row',
    marginTop: 18,
  },
  integrityTitle: {
    color: palette.text,
    fontSize: type.display - 1,
    fontWeight: '700',
  },
  logDetail: {
    color: palette.text,
    flex: 1,
    fontSize: type.bodyLarge,
  },
  logDot: {
    backgroundColor: palette.warning,
    borderRadius: 99,
    height: 4,
    marginTop: 6,
    width: 4,
  },
  logList: {
    gap: 12,
    marginBottom: 26,
    marginTop: 18,
  },
  logRow: {
    flexDirection: 'row',
    gap: 10,
  },
  logTime: {
    color: '#6f8fbc',
    fontSize: 13,
    width: 36,
  },
  meta: {
    color: palette.muted,
    fontSize: type.body,
    marginTop: 8,
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: '#3ad5cb',
    flexDirection: 'row',
    gap: 10,
    justifyContent: 'center',
    marginBottom: 12,
    paddingVertical: 14,
  },
  primaryButtonText: {
    color: '#032228',
    fontSize: type.bodyLarge,
    fontWeight: '800',
  },
  ringCutout: {
    backgroundColor: palette.background,
    borderRadius: 99,
    height: 24,
    position: 'absolute',
    right: -3,
    top: -3,
    width: 24,
  },
  ringInner: {
    alignItems: 'center',
    backgroundColor: palette.background,
    borderRadius: 999,
    height: 74,
    justifyContent: 'center',
    width: 74,
  },
  ringOuter: {
    alignItems: 'center',
    borderColor: '#26dd88',
    borderRadius: 999,
    borderWidth: 6,
    height: 86,
    justifyContent: 'center',
    width: 86,
  },
  ringScale: {
    color: palette.mutedStrong,
    fontSize: type.tiny,
    marginTop: 2,
  },
  ringValue: {
    color: palette.success,
    fontSize: type.title + 2,
    fontWeight: '800',
  },
  ringWrap: {
    justifyContent: 'center',
  },
  safeArea: {
    backgroundColor: palette.background,
    flex: 1,
  },
  secondaryButton: {
    alignItems: 'center',
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    justifyContent: 'center',
    paddingVertical: 13,
  },
  secondaryButtonText: {
    color: palette.mutedStrong,
    fontSize: type.bodyLarge,
  },
  sectionBlock: {
    borderTopColor: palette.border,
    borderTopWidth: 1,
    paddingTop: 18,
  },
  sectionLabel: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 2,
  },
  statCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flex: 1,
    gap: 6,
    minHeight: 68,
    paddingHorizontal: 12,
    paddingVertical: 11,
  },
  statLabel: {
    color: palette.mutedStrong,
    fontSize: type.tiny,
    letterSpacing: 1.1,
  },
  statValue: {
    color: palette.teal,
    fontSize: type.title + 2,
    fontWeight: '800',
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 22,
  },
  track: {
    backgroundColor: '#203050',
    flex: 1,
    height: 2,
  },
  trackFill: {
    backgroundColor: palette.success,
    height: 2,
  },
  title: {
    color: palette.text,
    fontSize: type.title,
    fontWeight: '800',
    marginTop: 10,
  },
});
