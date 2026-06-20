import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { layout, palette, type } from '@/constants/design';

const stats = [
  { label: 'SESSIONS', value: '12' },
  { label: 'AVG TRUST', value: '91' },
  { label: 'LEVEL', value: 'L2' },
] as const;

const accountItems = [
  { icon: 'bell-outline', label: 'Notifications', value: 'Alerts, escalations, summaries' },
  { icon: 'shield-lock-outline', label: 'Admin Access', value: 'Enabled for proctoring tools' },
  { icon: 'fingerprint', label: 'Biometric Login', value: 'Enabled - Face ID' },
] as const;

const supportItems = [
  { icon: 'file-document-outline', label: 'Audit History', value: '12 exported reports' },
  { icon: 'help-circle-outline', label: 'Help & Support', value: 'Guides, contact IT' },
] as const;

export default function InvigilatorProfileScreen() {
  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.eyebrow}>INVIGILATOR PROFILE</Text>

        <View style={styles.heroCard}>
          <View style={styles.avatarBox}>
            <Text style={styles.avatarText}>AB</Text>
          </View>
          <View style={styles.heroText}>
            <Text style={styles.name}>Dr. Ama Boateng</Text>
            <Text style={styles.meta}>STAFF/2024/004</Text>
            <Text style={styles.metaSmall}>ROLE: Senior Invigilator</Text>
          </View>
          <Feather color={palette.warning} name="shield" size={18} />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionLabel}>OVERSIGHT RECORD</Text>
          <View style={styles.statsRow}>
            {stats.map((item) => (
              <View key={item.label} style={styles.statCard}>
                <Text style={styles.statValue}>{item.value}</Text>
                <Text style={styles.statLabel}>{item.label}</Text>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionLabel}>ACCOUNT</Text>
          <View style={styles.group}>
            {accountItems.map((item) => (
              <Pressable key={item.label} style={styles.infoCard}>
                <View style={styles.itemRow}>
                  <MaterialCommunityIcons
                    color={palette.warning}
                    name={item.icon as 'bell-outline'}
                    size={20}
                  />
                  <View style={styles.itemText}>
                    <Text style={styles.itemLabel}>{item.label}</Text>
                    <Text style={styles.itemValue}>{item.value}</Text>
                  </View>
                  <Feather color={palette.mutedStrong} name="chevron-right" size={16} />
                </View>
              </Pressable>
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionLabel}>SUPPORT</Text>
          <View style={styles.group}>
            {supportItems.map((item) => (
              <Pressable key={item.label} style={styles.infoCard}>
                <View style={styles.itemRow}>
                  <MaterialCommunityIcons
                    color={palette.warning}
                    name={item.icon as 'file-document-outline'}
                    size={20}
                  />
                  <View style={styles.itemText}>
                    <Text style={styles.itemLabel}>{item.label}</Text>
                    <Text style={styles.itemValue}>{item.value}</Text>
                  </View>
                  <Feather color={palette.mutedStrong} name="chevron-right" size={16} />
                </View>
              </Pressable>
            ))}
          </View>
        </View>

        <View style={styles.footerSpacer} />

        <Pressable onPress={() => router.replace('/invigilator-sign-in')} style={styles.signOutButton}>
          <Feather color="#ff5a61" name="log-out" size={15} />
          <Text style={styles.signOutText}>Sign Out</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  avatarBox: {
    alignItems: 'center',
    borderColor: palette.warning,
    borderWidth: 1,
    height: 50,
    justifyContent: 'center',
    width: 50,
  },
  avatarText: {
    color: palette.warning,
    fontSize: 18,
    fontWeight: '800',
  },
  content: {
    alignSelf: 'center',
    flexGrow: 1,
    maxWidth: layout.maxWidth,
    paddingBottom: 16,
    paddingHorizontal: layout.screenPaddingWide,
    width: '100%',
  },
  eyebrow: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 2.2,
    marginTop: 4,
  },
  footerSpacer: {
    flex: 1,
    minHeight: layout.footerSpacer,
  },
  group: {
    borderTopColor: palette.border,
    borderTopWidth: 1,
    marginTop: 12,
  },
  heroCard: {
    alignItems: 'center',
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 14,
    marginTop: 18,
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  heroText: {
    flex: 1,
  },
  infoCard: {
    borderBottomColor: palette.border,
    borderBottomWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  itemLabel: {
    color: palette.text,
    fontSize: type.bodyLarge,
    fontWeight: '700',
  },
  itemRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 14,
  },
  itemText: {
    flex: 1,
    gap: 6,
  },
  itemValue: {
    color: palette.mutedStrong,
    fontSize: 13,
  },
  meta: {
    color: palette.mutedStrong,
    fontSize: 14,
    marginTop: 4,
  },
  metaSmall: {
    color: palette.mutedStrong,
    fontSize: 12,
    marginTop: 3,
  },
  name: {
    color: palette.text,
    fontSize: type.title + 2,
    fontWeight: '800',
  },
  safeArea: {
    backgroundColor: palette.background,
    flex: 1,
  },
  section: {
    marginTop: 18,
  },
  sectionLabel: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 2.2,
  },
  signOutButton: {
    alignItems: 'center',
    borderColor: '#64131e',
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    justifyContent: 'center',
    paddingVertical: 14,
  },
  signOutText: {
    color: '#ff5a61',
    fontSize: type.bodyLarge,
    fontWeight: '700',
  },
  statCard: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flex: 1,
    gap: 8,
    minHeight: 68,
    paddingHorizontal: 12,
    paddingVertical: 11,
  },
  statLabel: {
    color: palette.mutedStrong,
    fontSize: type.tiny,
    letterSpacing: 1.2,
  },
  statValue: {
    color: palette.warning,
    fontSize: type.display,
    fontWeight: '800',
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 14,
  },
});
