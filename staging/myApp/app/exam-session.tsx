import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { layout, palette, type } from '@/constants/design';

const options = [
  'TCP/IP Model has exactly 4 abstraction layers',
  'OSI Reference Model has 7 distinct layers',
  'Both A and B are correct statements',
  'Neither statement is accurate',
];

export default function ExamSessionScreen() {
  const [selected, setSelected] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerRow}>
          <Pressable onPress={() => router.back()} style={styles.backButton}>
            <Feather color={palette.mutedStrong} name="chevron-left" size={18} />
          </Pressable>
          <Text style={styles.headerTitle}>CS 450 - COMPUTER NETWORKS</Text>
          <View style={styles.timerBox}>
            <Text style={styles.timerText}>45:17</Text>
          </View>
        </View>

        <View style={styles.warningBar}>
          <Feather color={palette.warning} name="alert-triangle" size={14} />
          <Text style={styles.warningText}>
            Gaze deviation detected. Please keep your eyes on the screen.
          </Text>
          <Feather color={palette.muted} name="x" size={14} />
        </View>

        <View style={styles.monitorCard}>
          <View style={styles.cameraBox}>
            <View style={styles.cameraFrame}>
              <View style={styles.cameraBadge}>
                <Text style={styles.cameraBadgeText}>KA</Text>
              </View>
            </View>
          </View>

          <View style={styles.monitorDetails}>
            <View style={styles.monitorRow}>
              <Text style={styles.monitorLabel}>GAZE</Text>
              <View style={styles.metricTrack}>
                <View style={[styles.metricFill, { width: '85%' }]} />
              </View>
              <Text style={styles.monitorValue}>85%</Text>
            </View>
            <View style={styles.monitorRow}>
              <Text style={styles.monitorLabel}>ID</Text>
              <View style={styles.metricTrack}>
                <View style={[styles.metricFill, { width: '92%' }]} />
              </View>
              <Text style={styles.monitorValue}>92%</Text>
            </View>

            <View style={styles.chipRow}>
              <View style={styles.chip}>
                <Text style={styles.chipText}>FACE OK</Text>
              </View>
              <View style={styles.chip}>
                <Text style={styles.chipText}>ON SCREEN</Text>
              </View>
            </View>
          </View>
        </View>

        <View style={styles.progressHeader}>
          <Text style={styles.progressLabel}>Q5 / 30</Text>
          <Text style={styles.progressLabel}>17%</Text>
        </View>
        <View style={styles.progressBar}>
          <View style={styles.progressFill} />
        </View>

        <Text style={styles.question}>
          Which of the following statements about network layer models is correct?
        </Text>

        <View style={styles.optionsList}>
          {options.map((option, index) => {
            const key = String.fromCharCode(65 + index);
            const active = selected === option;

            return (
              <Pressable
                key={option}
                onPress={() => setSelected(option)}
                style={[styles.optionCard, active ? styles.optionCardActive : null]}>
                <View style={[styles.choiceBox, active ? styles.choiceBoxActive : null]} />
                <Text style={styles.optionKey}>{key}.</Text>
                <Text style={styles.optionText}>{option}</Text>
              </Pressable>
            );
          })}
        </View>

        <Pressable onPress={() => setShowConfirm(true)} style={styles.submitButton}>
          <Text style={styles.submitText}>SUBMIT EXAM</Text>
        </Pressable>
      </ScrollView>

      <Modal animationType="fade" onRequestClose={() => setShowConfirm(false)} transparent visible={showConfirm}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalEyebrow}>CONFIRM SUBMISSION</Text>
            <Text style={styles.modalTitle}>Submit exam?</Text>
            <Text style={styles.modalCopy}>
              You have answered <Text style={styles.modalCopyStrong}>5 of 30</Text> questions. This
              action cannot be undone.
            </Text>

            <Pressable
              onPress={() => {
                setShowConfirm(false);
                router.replace('/(tabs)/results');
              }}
              style={styles.modalPrimaryButton}>
              <Text style={styles.modalPrimaryText}>Yes, submit</Text>
            </Pressable>

            <Pressable onPress={() => setShowConfirm(false)} style={styles.modalSecondaryButton}>
              <Text style={styles.modalSecondaryText}>Cancel</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
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
  cameraBadge: {
    alignItems: 'center',
    borderColor: palette.teal,
    borderWidth: 1,
    height: 30,
    justifyContent: 'center',
    width: 30,
  },
  cameraBadgeText: {
    color: palette.teal,
    fontSize: 10,
    fontWeight: '800',
  },
  cameraBox: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 72,
  },
  cameraFrame: {
    alignItems: 'center',
    backgroundColor: '#0e2134',
    borderColor: palette.border,
    borderWidth: 1,
    height: 48,
    justifyContent: 'center',
    width: 62,
  },
  chip: {
    borderColor: '#106c51',
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  chipRow: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 12,
  },
  chipText: {
    color: palette.success,
    fontSize: type.tiny,
    fontWeight: '700',
    letterSpacing: 0.8,
  },
  choiceBox: {
    borderColor: palette.border,
    borderWidth: 1,
    height: 18,
    marginTop: 2,
    width: 18,
  },
  choiceBoxActive: {
    backgroundColor: palette.teal,
    borderColor: palette.teal,
  },
  content: {
    alignSelf: 'center',
    maxWidth: layout.maxWidth,
    paddingBottom: layout.bottomPadding,
    paddingHorizontal: layout.screenPaddingWide,
    width: '100%',
  },
  headerRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  headerTitle: {
    color: '#7b97c5',
    flex: 1,
    fontSize: 11,
    letterSpacing: 1.2,
    marginLeft: 8,
  },
  metricFill: {
    backgroundColor: palette.success,
    height: 4,
  },
  metricTrack: {
    backgroundColor: '#213457',
    flex: 1,
    height: 4,
  },
  modalCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    paddingHorizontal: 20,
    paddingVertical: 20,
    width: '82%',
  },
  modalCopy: {
    color: palette.mutedStrong,
    fontSize: type.bodyLarge,
    lineHeight: 22,
    marginTop: 12,
  },
  modalCopyStrong: {
    color: palette.text,
    fontWeight: '800',
  },
  modalEyebrow: {
    color: '#ff5a61',
    fontSize: type.label,
    letterSpacing: 2,
  },
  modalOverlay: {
    alignItems: 'center',
    backgroundColor: 'rgba(2, 7, 18, 0.82)',
    flex: 1,
    justifyContent: 'center',
  },
  modalPrimaryButton: {
    alignItems: 'center',
    backgroundColor: '#f14545',
    marginTop: 20,
    paddingVertical: 14,
  },
  modalPrimaryText: {
    color: palette.text,
    fontSize: type.bodyLarge,
    fontWeight: '800',
  },
  modalSecondaryButton: {
    alignItems: 'center',
    borderColor: palette.border,
    borderWidth: 1,
    marginTop: 8,
    paddingVertical: 14,
  },
  modalSecondaryText: {
    color: palette.mutedStrong,
    fontSize: type.bodyLarge,
  },
  modalTitle: {
    color: palette.text,
    fontSize: type.display,
    fontWeight: '800',
    marginTop: 12,
  },
  monitorCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    paddingHorizontal: 10,
    paddingVertical: 12,
  },
  monitorDetails: {
    flex: 1,
    gap: 8,
    paddingLeft: 8,
  },
  monitorLabel: {
    color: palette.mutedStrong,
    fontSize: type.tiny,
    width: 24,
  },
  monitorRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  monitorValue: {
    color: palette.success,
    fontSize: 12,
    fontWeight: '700',
    width: 28,
  },
  optionCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 14,
    paddingVertical: 15,
  },
  optionCardActive: {
    borderColor: palette.teal,
  },
  optionKey: {
    color: '#5f7fb0',
    fontSize: type.bodyLarge,
    marginTop: 1,
  },
  optionText: {
    color: palette.text,
    flex: 1,
    fontSize: type.bodyLarge,
    lineHeight: 23,
  },
  optionsList: {
    gap: layout.cardGap,
    marginTop: 16,
  },
  progressBar: {
    backgroundColor: '#213457',
    height: 2,
    marginTop: 8,
  },
  progressFill: {
    backgroundColor: palette.teal,
    height: 2,
    width: '17%',
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 18,
  },
  progressLabel: {
    color: '#7b97c5',
    fontSize: 11,
  },
  question: {
    color: palette.text,
    fontSize: type.title,
    fontWeight: '800',
    lineHeight: 26,
    marginTop: 18,
  },
  safeArea: {
    backgroundColor: palette.background,
    flex: 1,
  },
  submitButton: {
    alignItems: 'center',
    borderColor: '#0bba70',
    borderWidth: 1,
    justifyContent: 'center',
    marginTop: 18,
    paddingVertical: 15,
  },
  submitText: {
    color: '#1df886',
    fontSize: type.bodyLarge,
    fontWeight: '800',
    letterSpacing: 1.3,
  },
  timerBox: {
    alignItems: 'center',
    borderColor: palette.teal,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 32,
    minWidth: 50,
    paddingHorizontal: 8,
  },
  timerText: {
    color: palette.teal,
    fontSize: type.title,
    fontWeight: '800',
  },
  warningBar: {
    alignItems: 'center',
    backgroundColor: palette.warningSoft,
    borderColor: '#6a4d14',
    borderWidth: 1,
    flexDirection: 'row',
    gap: 8,
    marginBottom: 0,
    paddingHorizontal: 10,
    paddingVertical: 12,
  },
  warningText: {
    color: palette.warning,
    flex: 1,
    fontSize: type.body,
    fontWeight: '600',
    lineHeight: 20,
  },
});
