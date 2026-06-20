import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { layout, palette, type } from '@/constants/design';

const roles = [
  {
    accent: palette.teal,
    description: 'JOIN EXAM SESSION',
    href: '/sign-in' as const,
    icon: <Feather color={palette.teal} name="user" size={20} />,
    title: 'Student',
  },
  {
    accent: palette.warning,
    href: '/invigilator-sign-in' as const,
    description: 'MONITOR SESSIONS',
    icon: <MaterialCommunityIcons color={palette.warning} name="lock-outline" size={20} />,
    title: 'Invigilator',
  },
] as const;

export default function LandingScreen() {
  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.badge}>
          <View style={styles.badgeDot} />
          <Text style={styles.badgeText}>SYSTEM ONLINE</Text>
        </View>

        <View style={styles.heroBlock}>
          <Text style={styles.heroLine}>Academic</Text>
          <Text style={[styles.heroLine, styles.heroAccent]}>Integrity</Text>
          <Text style={styles.heroLine}>Enforced.</Text>
          <Text style={styles.heroCopy}>
            AI-powered exam proctoring for KNUST. Real-time monitoring, zero compromise.
          </Text>
        </View>

        <View style={styles.divider} />

        <Text style={styles.sectionLabel}>SELECT YOUR ROLE</Text>

        <View style={styles.roleList}>
          {roles.map((role) => (
            <Pressable
              key={role.title}
              android_ripple={{ color: '#102447' }}
              onPress={() => router.push(role.href)}
              style={({ pressed }) => [
                styles.roleCard,
                { borderColor: `${role.accent}35` },
                pressed && styles.roleCardPressed,
              ]}>
              <View style={[styles.roleIconBox, { borderColor: role.accent }]}>{role.icon}</View>
              <View style={styles.roleTextBlock}>
                <Text style={styles.roleTitle}>{role.title}</Text>
                <Text style={styles.roleDescription}>{role.description}</Text>
              </View>
              <Feather color={role.accent} name="arrow-right" size={18} />
            </Pressable>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#041120',
    borderColor: '#17476d',
    borderWidth: 1,
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  badgeDot: {
    backgroundColor: palette.teal,
    borderRadius: 99,
    height: 6,
    width: 6,
  },
  badgeText: {
    color: '#8fe8ff',
    fontSize: type.tiny,
    fontWeight: '700',
    letterSpacing: 1.8,
  },
  content: {
    alignSelf: 'center',
    flexGrow: 1,
    maxWidth: layout.maxWidth,
    paddingBottom: layout.bottomPadding + 6,
    paddingHorizontal: layout.screenPadding,
    paddingTop: 4,
    width: '100%',
  },
  divider: {
    backgroundColor: palette.border,
    height: 1,
    marginBottom: 24,
    marginTop: layout.heroTop - 4,
    width: '100%',
  },
  heroAccent: {
    color: palette.teal,
  },
  heroBlock: {
    marginTop: layout.heroTop,
  },
  heroCopy: {
    color: palette.mutedStrong,
    fontSize: type.bodyLarge,
    lineHeight: 24,
    marginTop: 18,
    maxWidth: 312,
  },
  heroLine: {
    color: palette.text,
    fontSize: type.hero,
    fontWeight: '800',
    letterSpacing: -1.5,
    lineHeight: type.hero + 7,
  },
  roleCard: {
    alignItems: 'center',
    backgroundColor: palette.panel,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 14,
    minHeight: 78,
    paddingHorizontal: 16,
  },
  roleCardPressed: {
    opacity: 0.92,
    transform: [{ scale: 0.995 }],
  },
  roleDescription: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 1.4,
  },
  roleIconBox: {
    alignItems: 'center',
    borderWidth: 1,
    height: 32,
    justifyContent: 'center',
    width: 32,
  },
  roleList: {
    gap: layout.cardGap,
  },
  roleTextBlock: {
    flex: 1,
    gap: 4,
  },
  roleTitle: {
    color: palette.text,
    fontSize: type.title,
    fontWeight: '700',
  },
  safeArea: {
    backgroundColor: palette.background,
    flex: 1,
  },
  sectionLabel: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 2.1,
    marginBottom: 14,
  },
});
