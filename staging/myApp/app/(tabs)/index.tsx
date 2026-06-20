import { Feather, Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { layout, palette, type } from '@/constants/design';

const metrics = [
  { label: 'EXAMS TAKEN', value: '4' },
  { label: 'AVG SCORE', value: '78%' },
  { label: 'INTEGRITY', value: '94' },
];

const exams = [
  {
    code: 'CS 450',
    isLive: true,
    meta: '10:00 AM   Today   3h',
    title: 'Computer Networks',
  },
  {
    code: 'CS 352',
    meta: '2:00 PM   Thu 12 Jun   2h',
    title: 'Data Structures',
  },
  {
    code: 'CS 451',
    meta: '9:00 AM   Fri 13 Jun   3h',
    title: 'Algorithms',
  },
];

const activity = [
  { date: '06 Jun', integrity: '96', score: '71%', title: 'Operating Systems' },
  { date: '02 Jun', integrity: '91', score: '84%', title: 'Database Systems' },
];

export default function DashboardScreen() {
  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerMetaRow}>
          <Text style={styles.studentId}>UG/CS/2021/0042</Text>
          <View style={styles.headerActions}>
            <View style={styles.bellWrap}>
              <Ionicons color={palette.mutedStrong} name="notifications-outline" size={18} />
              <View style={styles.bellDot} />
            </View>
            <Pressable onPress={() => router.push('/(tabs)/profile')} style={styles.avatarBox}>
              <Text style={styles.avatarText}>KA</Text>
            </Pressable>
          </View>
        </View>

        <Text style={styles.studentName}>Kwame Asante</Text>

        <View style={styles.metricRow}>
          {metrics.map((metric) => (
            <View key={metric.label} style={styles.metricCard}>
              <Text style={styles.metricValue}>{metric.value}</Text>
              <Text style={styles.metricLabel}>{metric.label}</Text>
            </View>
          ))}
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionLabel}>EXAM SCHEDULE</Text>
          <Text style={styles.sectionAccent}>3 upcoming</Text>
        </View>

        <View style={styles.cardList}>
          {exams.map((exam) => (
            <View
              key={exam.title}
              style={[styles.examCard, exam.isLive ? styles.examCardLive : null]}>
              <View style={styles.examRow}>
                <View style={styles.examInfo}>
                  <View style={styles.examCodeRow}>
                    <Text style={styles.examCode}>{exam.code}</Text>
                    {exam.isLive ? (
                      <View style={styles.liveFlag}>
                        <View style={styles.liveDot} />
                        <Text style={styles.liveText}>LIVE</Text>
                      </View>
                    ) : null}
                  </View>
                  <Text style={styles.examTitle}>{exam.title}</Text>
                </View>
                {exam.isLive ? (
                  <Pressable onPress={() => router.push('/exam-session')} style={styles.joinButton}>
                    <Text style={styles.joinButtonText}>Join</Text>
                    <Feather color="#05303a" name="arrow-right" size={14} />
                  </Pressable>
                ) : null}
              </View>
              <Text style={styles.examMeta}>{exam.meta}</Text>
            </View>
          ))}
        </View>

        <Text style={[styles.sectionLabel, styles.activityHeader]}>RECENT ACTIVITY</Text>

        <View style={styles.cardList}>
          {activity.map((item) => (
            <Pressable
              key={item.title}
              onPress={() => router.push('/(tabs)/results')}
              style={styles.activityCard}>
              <View>
                <Text style={styles.activityTitle}>{item.title}</Text>
                <Text style={styles.activityDate}>{item.date}</Text>
              </View>
              <View style={styles.activityStats}>
                <Text style={styles.activityScore}>{item.score}</Text>
                <Text style={styles.activityIntegrity}>INTEGRITY {item.integrity}</Text>
              </View>
            </Pressable>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  activityCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 16,
  },
  activityDate: {
    color: palette.muted,
    fontSize: 11,
    marginTop: 12,
  },
  activityHeader: {
    marginBottom: 14,
    marginTop: 26,
  },
  activityIntegrity: {
    color: palette.mutedStrong,
    fontSize: type.tiny,
    letterSpacing: 1.2,
    marginTop: 6,
  },
  activityScore: {
    color: palette.success,
    fontSize: 20,
    fontWeight: '800',
    textAlign: 'right',
  },
  activityStats: {
    alignItems: 'flex-end',
  },
  activityTitle: {
    color: palette.text,
    fontSize: 18,
    fontWeight: '700',
  },
  avatarBox: {
    alignItems: 'center',
    borderColor: palette.teal,
    borderWidth: 1,
    height: 30,
    justifyContent: 'center',
    width: 30,
  },
  avatarText: {
    color: palette.teal,
    fontSize: 12,
    fontWeight: '800',
  },
  bellDot: {
    backgroundColor: palette.danger,
    borderRadius: 99,
    height: 6,
    position: 'absolute',
    right: 0,
    top: 1,
    width: 6,
  },
  bellWrap: {
    padding: 2,
    position: 'relative',
  },
  cardList: {
    gap: 12,
  },
  content: {
    alignSelf: 'center',
    maxWidth: layout.maxWidth,
    paddingBottom: layout.bottomPadding,
    paddingHorizontal: layout.screenPaddingWide,
    width: '100%',
  },
  examCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  examCardLive: {
    borderColor: '#1db9c6',
  },
  examCode: {
    color: palette.muted,
    fontSize: 11,
  },
  examCodeRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
  },
  examInfo: {
    flex: 1,
    gap: 8,
  },
  examMeta: {
    color: palette.mutedStrong,
    fontSize: 12,
    marginTop: 14,
  },
  examRow: {
    flexDirection: 'row',
    gap: 12,
  },
  examTitle: {
    color: palette.text,
    fontSize: type.title,
    fontWeight: '700',
  },
  headerActions: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 14,
  },
  headerMetaRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  joinButton: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#36e2d6',
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  joinButtonText: {
    color: '#05303a',
    fontSize: type.body,
    fontWeight: '800',
  },
  liveDot: {
    backgroundColor: palette.danger,
    borderRadius: 99,
    height: 6,
    width: 6,
  },
  liveFlag: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 5,
  },
  liveText: {
    color: '#ff7c8f',
    fontSize: type.tiny,
    fontWeight: '700',
    letterSpacing: 0.8,
  },
  metricCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flex: 1,
    gap: 8,
    minHeight: 68,
    paddingHorizontal: 12,
    paddingVertical: 11,
  },
  metricLabel: {
    color: palette.mutedStrong,
    fontSize: type.tiny,
    letterSpacing: 1.3,
  },
  metricRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 22,
    marginTop: 18,
  },
  metricValue: {
    color: palette.teal,
    fontSize: type.display,
    fontWeight: '800',
  },
  safeArea: {
    backgroundColor: palette.background,
    flex: 1,
  },
  sectionAccent: {
    color: palette.success,
    fontSize: type.body,
    fontWeight: '700',
  },
  sectionHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  sectionLabel: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 2,
  },
  studentId: {
    color: '#7aa0d6',
    fontSize: 11,
  },
  studentName: {
    color: palette.text,
    fontSize: type.display,
    fontWeight: '800',
    marginTop: 6,
  },
});
