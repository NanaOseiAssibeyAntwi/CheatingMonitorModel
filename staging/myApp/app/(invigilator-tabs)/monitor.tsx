import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { layout, palette, type } from '@/constants/design';

const students = [
  {
    flags: [
      { color: palette.success, label: 'G' },
      { color: '#ef476f', label: 'F' },
      { color: palette.success, label: 'A' },
      { color: palette.success, label: 'M' },
    ],
    id: '0042',
    initials: 'KA',
    name: 'Kwame Asante',
    risk: 'MED',
    riskColor: palette.warning,
    score: '72',
  },
  {
    flags: [
      { color: palette.success, label: 'G' },
      { color: palette.success, label: 'F' },
      { color: palette.success, label: 'A' },
      { color: palette.success, label: 'M' },
    ],
    id: '0038',
    initials: 'AM',
    name: 'Ama Mensah',
    risk: 'LOW',
    riskColor: palette.success,
    score: '45',
  },
  {
    flags: [
      { color: '#ef476f', label: 'G' },
      { color: palette.success, label: 'F' },
      { color: '#ef476f', label: 'A' },
      { color: palette.success, label: 'M' },
    ],
    id: '0051',
    initials: 'YO',
    name: 'Yaw Owusu',
    risk: 'HIGH',
    riskColor: '#ef476f',
    score: '88',
  },
  {
    flags: [
      { color: palette.success, label: 'G' },
      { color: palette.success, label: 'F' },
      { color: palette.success, label: 'A' },
      { color: palette.success, label: 'M' },
    ],
    id: '0029',
    initials: 'EB',
    name: 'Efua Boateng',
    risk: 'LOW',
    riskColor: palette.success,
    score: '35',
  },
  {
    flags: [
      { color: palette.success, label: 'G' },
      { color: '#ef476f', label: 'F' },
      { color: palette.success, label: 'A' },
      { color: palette.success, label: 'M' },
    ],
    id: '0067',
    initials: 'KA',
    name: 'Kofi Adjei',
    risk: 'MED',
    riskColor: palette.warning,
    score: '61',
  },
  {
    flags: [
      { color: palette.success, label: 'G' },
      { color: palette.success, label: 'F' },
      { color: palette.success, label: 'A' },
      { color: palette.success, label: 'M' },
    ],
    id: '0045',
    initials: 'AO',
    name: 'Akua Ofori',
    risk: 'LOW',
    riskColor: palette.success,
    score: '29',
  },
] as const;

const filters = ['ALL', 'FLAGGED', 'CRITICAL'] as const;

export default function InvigilatorMonitorScreen() {
  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerRow}>
          <Pressable
            onPress={() => router.navigate('/(invigilator-tabs)')}
            style={styles.backButton}>
            <Feather color={palette.mutedStrong} name="chevron-left" size={18} />
          </Pressable>
          <View style={styles.headerText}>
            <Text style={styles.courseCode}>CS 450</Text>
            <Text style={styles.courseTitle}>Computer Networks</Text>
          </View>
          <View style={styles.liveWrap}>
            <View style={styles.liveDot} />
            <Text style={styles.liveText}>LIVE</Text>
          </View>
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>42</Text>
            <Text style={styles.statLabel}>TOTAL</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={[styles.statValue, { color: palette.success }]}>40</Text>
            <Text style={styles.statLabel}>ACTIVE</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={[styles.statValue, { color: palette.warning }]}>8</Text>
            <Text style={styles.statLabel}>FLAGGED</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={[styles.statValue, { color: '#7a95c3' }]}>34</Text>
            <Text style={styles.statLabel}>DONE</Text>
          </View>
        </View>

        <View style={styles.filterRow}>
          {filters.map((filter, index) => (
            <View key={filter} style={styles.filterItem}>
              <Text style={[styles.filterText, index === 0 ? styles.filterTextActive : null]}>
                {filter}
              </Text>
              <View
                style={[
                  styles.filterUnderline,
                  index === 0 ? styles.filterUnderlineActive : null,
                ]}
              />
            </View>
          ))}
        </View>

        <View style={styles.grid}>
          {students.map((student) => (
            <View key={student.id} style={styles.studentCard}>
              <View style={[styles.scanBox, { borderTopColor: student.riskColor }]}>
                <View style={styles.scanGrid} />
                <View
                  style={[
                    styles.riskBadge,
                    {
                      backgroundColor: `${student.riskColor}18`,
                      borderColor: `${student.riskColor}70`,
                    },
                  ]}>
                  <Text style={[styles.riskText, { color: student.riskColor }]}>{student.risk}</Text>
                </View>
                <View style={styles.faceBox}>
                  <Text style={[styles.faceInitials, { color: student.riskColor }]}>
                    {student.initials}
                  </Text>
                </View>
                <Text style={[styles.score, { color: student.riskColor }]}>{student.score}</Text>
              </View>

              <View style={styles.studentBody}>
                <Text style={styles.studentName}>{student.name}</Text>
                <Text style={styles.studentId}>{student.id}</Text>

                <View style={styles.flagRow}>
                  {student.flags.map((flag) => (
                    <View
                      key={`${student.id}-${flag.label}`}
                      style={[
                        styles.flagChip,
                        {
                          backgroundColor: `${flag.color}18`,
                          borderColor: `${flag.color}55`,
                        },
                      ]}>
                      <Text style={[styles.flagText, { color: flag.color }]}>{flag.label}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </View>
          ))}
        </View>
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
  courseCode: {
    color: '#6f8fbc',
    fontSize: type.label,
    letterSpacing: 2,
  },
  courseTitle: {
    color: palette.text,
    fontSize: type.title,
    fontWeight: '800',
    marginTop: 6,
  },
  faceBox: {
    alignItems: 'center',
    borderColor: '#205477',
    borderWidth: 1,
    height: 30,
    justifyContent: 'center',
    left: '38%',
    position: 'absolute',
    top: '38%',
    width: 30,
  },
  faceInitials: {
    fontSize: 11,
    fontWeight: '800',
  },
  filterItem: {
    alignItems: 'center',
    flex: 1,
  },
  filterRow: {
    borderBottomColor: palette.border,
    borderBottomWidth: 1,
    flexDirection: 'row',
    marginBottom: 16,
    marginTop: 6,
  },
  filterText: {
    color: '#6f8fbc',
    fontSize: type.label,
    letterSpacing: 1.8,
    paddingBottom: 12,
  },
  filterTextActive: {
    color: palette.teal,
    fontWeight: '700',
  },
  filterUnderline: {
    backgroundColor: 'transparent',
    height: 2,
    width: '100%',
  },
  filterUnderlineActive: {
    backgroundColor: palette.warning,
  },
  flagChip: {
    alignItems: 'center',
    borderWidth: 1,
    height: 18,
    justifyContent: 'center',
    minWidth: 18,
    paddingHorizontal: 5,
  },
  flagRow: {
    flexDirection: 'row',
    gap: 4,
    marginTop: 12,
  },
  flagText: {
    fontSize: 9,
    fontWeight: '700',
  },
  grid: {
    columnGap: 8,
    flexDirection: 'row',
    flexWrap: 'wrap',
    rowGap: 10,
  },
  headerRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  headerText: {
    flex: 1,
    marginLeft: 6,
  },
  liveDot: {
    backgroundColor: palette.danger,
    borderRadius: 99,
    height: 6,
    width: 6,
  },
  liveText: {
    color: palette.danger,
    fontSize: type.label,
    fontWeight: '700',
    letterSpacing: 1.1,
  },
  liveWrap: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
  },
  riskBadge: {
    borderWidth: 1,
    paddingHorizontal: 6,
    paddingVertical: 3,
    position: 'absolute',
    right: 8,
    top: 8,
  },
  riskText: {
    fontSize: type.tiny,
    fontWeight: '700',
    letterSpacing: 0.8,
  },
  safeArea: {
    backgroundColor: palette.background,
    flex: 1,
  },
  scanBox: {
    backgroundColor: '#07121f',
    borderTopWidth: 2,
    height: 120,
    overflow: 'hidden',
    position: 'relative',
  },
  scanGrid: {
    borderColor: '#0d3552',
    borderWidth: 1,
    bottom: 10,
    left: 10,
    position: 'absolute',
    right: 10,
    top: 10,
  },
  score: {
    bottom: 10,
    fontSize: type.title,
    fontWeight: '800',
    position: 'absolute',
    right: 10,
  },
  statCard: {
    alignItems: 'center',
    borderRightColor: palette.border,
    borderRightWidth: 1,
    flex: 1,
    gap: 6,
    justifyContent: 'center',
    minHeight: 58,
  },
  statLabel: {
    color: '#6f8fbc',
    fontSize: type.tiny,
    letterSpacing: 1.2,
  },
  statValue: {
    color: palette.text,
    fontSize: type.display,
    fontWeight: '800',
  },
  statsRow: {
    borderBottomColor: palette.border,
    borderBottomWidth: 1,
    borderTopColor: palette.border,
    borderTopWidth: 1,
    flexDirection: 'row',
    marginBottom: 8,
    paddingVertical: 10,
  },
  studentBody: {
    paddingHorizontal: 10,
    paddingVertical: 10,
  },
  studentCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    width: '48.5%',
  },
  studentId: {
    color: '#6f8fbc',
    fontSize: 10,
    marginTop: 4,
  },
  studentName: {
    color: palette.text,
    fontSize: type.bodyLarge,
    fontWeight: '700',
  },
});
