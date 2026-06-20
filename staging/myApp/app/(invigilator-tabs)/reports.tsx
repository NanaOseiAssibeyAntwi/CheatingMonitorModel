import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { layout, palette, type } from '@/constants/design';

const summary = [
  { label: 'SESSIONS', value: '12', valueColor: palette.warning },
  { label: 'AVG TRUST', value: '91', valueColor: palette.success },
  { label: 'FLAGS', value: '23', valueColor: '#ff6a6a' },
] as const;

const reports = [
  {
    course: 'Computer Networks',
    date: '09 Jun 2025',
    flags: '8 flagged',
    integrity: '90',
    status: 'Completed',
  },
  {
    course: 'Data Structures',
    date: '12 Jun 2025',
    flags: '3 flagged',
    integrity: '94',
    status: 'Completed',
  },
  {
    course: 'Algorithms',
    date: '13 Jun 2025',
    flags: '1 flagged',
    integrity: '97',
    status: 'Completed',
  },
] as const;

export default function InvigilatorReportsScreen() {
  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.eyebrow}>SESSION REPORTS</Text>
        <Text style={styles.title}>Exam Oversight Reports</Text>
        <Text style={styles.subtitle}>
          Review completed session summaries, integrity scores, and flagged incidents across active courses.
        </Text>

        <View style={styles.summaryRow}>
          {summary.map((item) => (
            <View key={item.label} style={styles.summaryCard}>
              <Text style={[styles.summaryValue, { color: item.valueColor }]}>{item.value}</Text>
              <Text style={styles.summaryLabel}>{item.label}</Text>
            </View>
          ))}
        </View>

        <View style={styles.exportCard}>
          <View>
            <Text style={styles.exportTitle}>Weekly Export</Text>
            <Text style={styles.exportCopy}>Generate CSV and PDF exports for audit review.</Text>
          </View>
          <View style={styles.exportButton}>
            <Feather color="#1b1200" name="download" size={15} />
            <Text style={styles.exportButtonText}>Export</Text>
          </View>
        </View>

        <View style={styles.list}>
          {reports.map((report) => (
            <View key={report.course} style={styles.reportCard}>
              <View style={styles.reportHeader}>
                <View>
                  <Text style={styles.reportCourse}>{report.course}</Text>
                  <Text style={styles.reportDate}>{report.date}</Text>
                </View>
                <View style={styles.statusBadge}>
                  <Text style={styles.statusText}>{report.status}</Text>
                </View>
              </View>

              <View style={styles.reportFooter}>
                <View style={styles.reportMeta}>
                  <MaterialCommunityIcons color={palette.warning} name="alert-outline" size={16} />
                  <Text style={styles.flagsText}>{report.flags}</Text>
                </View>
                <Text style={styles.integrityText}>TRUST {report.integrity}</Text>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  content: {
    alignSelf: 'center',
    maxWidth: layout.maxWidth,
    paddingBottom: layout.bottomPadding,
    paddingHorizontal: layout.screenPaddingWide,
    width: '100%',
  },
  exportButton: {
    alignItems: 'center',
    backgroundColor: '#d7a413',
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
    minWidth: 96,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  exportButtonText: {
    color: '#1b1200',
    fontSize: type.body,
    fontWeight: '800',
  },
  exportCard: {
    alignItems: 'center',
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  exportCopy: {
    color: palette.mutedStrong,
    fontSize: type.body,
    marginTop: 6,
  },
  exportTitle: {
    color: palette.text,
    fontSize: type.title,
    fontWeight: '700',
  },
  eyebrow: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 2.2,
    marginTop: 4,
  },
  flagsText: {
    color: palette.warning,
    fontSize: 13,
    fontWeight: '700',
  },
  integrityText: {
    color: palette.success,
    fontSize: 13,
    fontWeight: '700',
  },
  list: {
    gap: 12,
    marginTop: 18,
  },
  reportCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  reportCourse: {
    color: palette.text,
    fontSize: type.title,
    fontWeight: '700',
  },
  reportDate: {
    color: palette.muted,
    fontSize: 13,
    marginTop: 8,
  },
  reportFooter: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
  },
  reportHeader: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  reportMeta: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
  },
  safeArea: {
    backgroundColor: palette.background,
    flex: 1,
  },
  statusBadge: {
    borderColor: '#6c5211',
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  statusText: {
    color: palette.warning,
    fontSize: type.tiny,
    fontWeight: '700',
    letterSpacing: 1.1,
  },
  subtitle: {
    color: palette.mutedStrong,
    fontSize: type.bodyLarge,
    lineHeight: 22,
    marginTop: 12,
  },
  summaryCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flex: 1,
    gap: 8,
    minHeight: 68,
    paddingHorizontal: 12,
    paddingVertical: 11,
  },
  summaryLabel: {
    color: palette.mutedStrong,
    fontSize: type.tiny,
    letterSpacing: 1.2,
  },
  summaryRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 20,
  },
  summaryValue: {
    fontSize: type.display,
    fontWeight: '800',
  },
  title: {
    color: palette.text,
    fontSize: type.display,
    fontWeight: '800',
    marginTop: 10,
  },
});
