import { Feather, Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { layout, palette, type } from '@/constants/design';

const metrics = [
  { label: 'SESSIONS', value: '3', valueColor: palette.teal },
  { label: 'ONLINE', value: '115', valueColor: palette.success },
  { label: 'FLAGGED', value: '12', valueColor: palette.warning },
  { label: 'DONE', value: '8', valueColor: '#8aa0c4' },
];

const sessions = [
  { code: 'CS 450', flagCount: '8 flagged', level: 'HIGH', levelColor: '#ef476f', students: '42 students', title: 'Computer Networks' },
  { code: 'CS 352', flagCount: '3 flagged', level: 'MED', levelColor: '#f1bf21', students: '38 students', title: 'Data Structures' },
  { code: 'CS 451', flagCount: '1 flagged', level: 'LOW', levelColor: '#28ef8d', students: '35 students', title: 'Algorithms' },
] as const;

const alerts = [
  { color: '#ef476f', name: 'Yaw Mensah', time: '2mago', text: 'Multiple face detection' },
  { color: '#d7a413', name: 'Ama Asante', time: '5mago', text: 'App switch detected' },
  { color: '#d7a413', name: 'Kofi Owusu', time: '8mago', text: 'Gaze off-screen x4' },
] as const;

export default function InvigilatorDashboardScreen() {
  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerMetaRow}>
          <Text style={styles.staffMeta}>STAFF/2024/004 - L2</Text>
          <View style={styles.headerActions}>
            <View style={styles.bellWrap}>
              <Ionicons color={palette.mutedStrong} name="notifications-outline" size={18} />
              <View style={styles.alertCount}>
                <Text style={styles.alertCountText}>3</Text>
              </View>
            </View>
            <View style={styles.avatarBox}>
              <Text style={styles.avatarText}>AB</Text>
            </View>
          </View>
        </View>

        <Text style={styles.staffName}>Dr. Ama Boateng</Text>

        <View style={styles.metricRow}>
          {metrics.map((metric) => (
            <View key={metric.label} style={styles.metricCard}>
              <Text style={[styles.metricValue, { color: metric.valueColor }]}>{metric.value}</Text>
              <Text style={styles.metricLabel}>{metric.label}</Text>
            </View>
          ))}
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionLabel}>LIVE SESSIONS</Text>
          <View style={styles.sectionState}>
            <View style={styles.sectionDot} />
            <Text style={styles.sectionAccent}>3 active</Text>
          </View>
        </View>

        <View style={styles.cardList}>
          {sessions.map((session) => (
            <View
              key={session.title}
              style={[styles.sessionCard, { borderLeftColor: session.levelColor }]}>
              <View style={styles.sessionHeader}>
                <View style={styles.sessionTitleBlock}>
                  <View style={styles.sessionMetaRow}>
                    <Text style={styles.sessionCode}>{session.code}</Text>
                    <View
                      style={[
                        styles.levelBadge,
                        {
                          backgroundColor: `${session.levelColor}20`,
                          borderColor: `${session.levelColor}55`,
                        },
                      ]}>
                      <Text style={[styles.levelText, { color: session.levelColor }]}>
                        {session.level}
                      </Text>
                    </View>
                  </View>
                  <Text style={styles.sessionTitle}>{session.title}</Text>
                </View>
                <Pressable
                  onPress={() => router.push('/(invigilator-tabs)/monitor')}
                  style={styles.monitorButton}>
                  <Text style={styles.monitorText}>Monitor</Text>
                  <Feather color={palette.teal} name="arrow-right" size={14} />
                </Pressable>
              </View>
              <Text style={styles.sessionFoot}>
                <Text style={styles.sessionStudents}>{session.students}</Text>
                <Text style={styles.sessionFlags}>   {session.flagCount}</Text>
              </Text>
            </View>
          ))}
        </View>

        <Text style={[styles.sectionLabel, styles.alertsHeader]}>RECENT ALERTS</Text>

        <View style={styles.cardList}>
          {alerts.map((alert) => (
            <View key={alert.name} style={styles.alertCard}>
              <View style={styles.alertLead}>
                <View style={[styles.alertMarker, { backgroundColor: alert.color }]} />
                <View>
                  <Text style={styles.alertName}>{alert.name}</Text>
                  <Text style={styles.alertText}>{alert.text}</Text>
                </View>
              </View>
              <Text style={styles.alertTime}>{alert.time}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  alertCard: {
    alignItems: 'flex-start',
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  alertCount: {
    alignItems: 'center',
    backgroundColor: palette.danger,
    borderRadius: 99,
    height: 16,
    justifyContent: 'center',
    position: 'absolute',
    right: -6,
    top: -6,
    width: 16,
  },
  alertCountText: {
    color: palette.text,
    fontSize: 9,
    fontWeight: '800',
  },
  alertLead: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    gap: 12,
  },
  alertMarker: {
    borderRadius: 99,
    height: 7,
    marginTop: 6,
    width: 7,
  },
  alertName: {
    color: palette.text,
    fontSize: 16,
    fontWeight: '700',
  },
  alertText: {
    color: palette.mutedStrong,
    fontSize: 13,
    marginTop: 6,
  },
  alertTime: {
    color: '#6f8fbc',
    fontSize: 11,
  },
  alertsHeader: {
    marginBottom: 14,
    marginTop: 28,
  },
  avatarBox: {
    alignItems: 'center',
    borderColor: palette.warning,
    borderWidth: 1,
    height: 30,
    justifyContent: 'center',
    width: 30,
  },
  avatarText: {
    color: palette.warning,
    fontSize: 12,
    fontWeight: '800',
  },
  bellWrap: {
    padding: 2,
    position: 'relative',
  },
  cardList: {
    gap: 10,
  },
  content: {
    alignSelf: 'center',
    maxWidth: layout.maxWidth,
    paddingBottom: layout.bottomPadding,
    paddingHorizontal: layout.screenPaddingWide,
    width: '100%',
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
  levelBadge: {
    borderWidth: 1,
    paddingHorizontal: 6,
    paddingVertical: 3,
  },
  levelText: {
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
    paddingHorizontal: 10,
    paddingVertical: 11,
  },
  metricLabel: {
    color: palette.mutedStrong,
    fontSize: type.tiny,
    letterSpacing: 1.2,
  },
  metricRow: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: 22,
    marginTop: 18,
  },
  metricValue: {
    fontSize: type.display,
    fontWeight: '800',
  },
  monitorButton: {
    alignItems: 'center',
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  monitorText: {
    color: palette.teal,
    fontSize: type.body,
    fontWeight: '700',
  },
  safeArea: {
    backgroundColor: palette.background,
    flex: 1,
  },
  sectionAccent: {
    color: '#ff6a6a',
    fontSize: type.body,
    fontWeight: '700',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  sectionDot: {
    backgroundColor: palette.danger,
    borderRadius: 99,
    height: 6,
    width: 6,
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
    letterSpacing: 2.1,
  },
  sectionState: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  sessionCard: {
    backgroundColor: palette.panel,
    borderBottomWidth: 1,
    borderColor: palette.border,
    borderLeftWidth: 2,
    borderRightWidth: 1,
    borderTopWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 14,
  },
  sessionCode: {
    color: palette.muted,
    fontSize: 11,
  },
  sessionFlags: {
    color: palette.warning,
    fontSize: 13,
    fontWeight: '700',
  },
  sessionFoot: {
    color: palette.mutedStrong,
    fontSize: 13,
    marginTop: 12,
  },
  sessionHeader: {
    flexDirection: 'row',
    gap: 12,
  },
  sessionMetaRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  sessionStudents: {
    color: palette.mutedStrong,
  },
  sessionTitle: {
    color: palette.text,
    fontSize: type.title,
    fontWeight: '700',
    marginTop: 10,
  },
  sessionTitleBlock: {
    flex: 1,
  },
  staffMeta: {
    color: palette.warning,
    fontSize: 11,
    letterSpacing: 1.1,
  },
  staffName: {
    color: palette.text,
    fontSize: type.display,
    fontWeight: '800',
    marginTop: 6,
  },
});
