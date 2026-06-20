import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { layout, palette, type } from '@/constants/design';

export default function InvigilatorSignInScreen() {
  const [staffId, setStaffId] = useState('STAFF/2024/004');
  const [password, setPassword] = useState('password');
  const [showPassword, setShowPassword] = useState(false);

  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.select({ ios: 'padding', default: undefined })}
        style={styles.safeArea}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <View style={styles.topRow}>
            <Pressable onPress={() => router.back()} style={styles.backButton}>
              <Feather color={palette.mutedStrong} name="chevron-left" size={18} />
            </Pressable>
            <View style={styles.topDivider} />
            <Text style={styles.topLabel}>INVIGILATOR AUTH</Text>
          </View>

          <View style={styles.authIconBox}>
            <MaterialCommunityIcons color={palette.warning} name="lock-outline" size={22} />
          </View>

          <Text style={styles.title}>Invigilator Sign In</Text>
          <Text style={styles.subtitle}>Staff credentials - elevated access</Text>

          <View style={styles.formBlock}>
            <Text style={styles.fieldLabel}>STAFF ID</Text>
            <TextInput
              autoCapitalize="characters"
              autoCorrect={false}
              onChangeText={setStaffId}
              placeholder="STAFF/2024/004"
              placeholderTextColor="#547099"
              style={styles.input}
              value={staffId}
            />

            <Text style={styles.fieldLabel}>PASSWORD</Text>
            <View style={styles.passwordField}>
              <TextInput
                autoCapitalize="none"
                autoCorrect={false}
                onChangeText={setPassword}
                placeholder="Password"
                placeholderTextColor="#547099"
                secureTextEntry={!showPassword}
                style={styles.passwordInput}
                value={password}
              />
              <Pressable hitSlop={10} onPress={() => setShowPassword((value) => !value)}>
                <Feather
                  color={palette.muted}
                  name={showPassword ? 'eye-off' : 'eye'}
                  size={18}
                />
              </Pressable>
            </View>
          </View>

          <View style={styles.biometricCard}>
            <View style={styles.biometricLeft}>
              <MaterialCommunityIcons color={palette.warning} name="fingerprint" size={22} />
              <View>
                <Text style={styles.biometricTitle}>Biometric Login</Text>
                <Text style={styles.biometricMeta}>TOUCH ID / FACE ID</Text>
              </View>
            </View>
            <View style={styles.biometricDot} />
          </View>

          <Pressable
            onPress={() => router.replace('/(invigilator-tabs)')}
            style={styles.primaryButton}>
            <Text style={styles.primaryButtonText}>Authenticate</Text>
          </Pressable>

          <Text style={styles.supportCopy}>
            Access issues? <Text style={styles.supportAccent}>Contact administrator</Text>
          </Text>

          <View style={styles.footerSpacer} />

          <View style={styles.securityBar}>
            <Text style={styles.securityLabel}>ACCESS LEVEL</Text>
            <Text style={styles.securityText}>INVIGILATOR - L2</Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  authIconBox: {
    alignItems: 'center',
    borderColor: palette.warning,
    borderWidth: 1,
    height: 40,
    justifyContent: 'center',
    marginTop: 22,
    width: 40,
  },
  backButton: {
    alignItems: 'center',
    borderColor: palette.border,
    borderWidth: 1,
    height: 30,
    justifyContent: 'center',
    width: 30,
  },
  biometricCard: {
    alignItems: 'center',
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 22,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  biometricDot: {
    backgroundColor: palette.success,
    borderRadius: 99,
    height: 6,
    width: 6,
  },
  biometricLeft: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 12,
  },
  biometricMeta: {
    color: palette.mutedStrong,
    fontSize: type.tiny,
    letterSpacing: 1.4,
    marginTop: 4,
  },
  biometricTitle: {
    color: palette.text,
    fontSize: 17,
    fontWeight: '700',
  },
  content: {
    alignSelf: 'center',
    flexGrow: 1,
    paddingBottom: 12,
    paddingHorizontal: layout.screenPadding,
    maxWidth: layout.maxWidth,
    width: '100%',
  },
  fieldLabel: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 1.9,
    marginBottom: 8,
  },
  footerSpacer: {
    flex: 1,
    minHeight: layout.footerSpacer + 12,
  },
  formBlock: {
    gap: 14,
    marginTop: 26,
  },
  input: {
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    color: palette.text,
    fontSize: type.bodyLarge,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  passwordField: {
    alignItems: 'center',
    backgroundColor: palette.panel,
    borderColor: palette.border,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 14,
  },
  passwordInput: {
    color: palette.text,
    flex: 1,
    fontSize: type.bodyLarge,
    paddingVertical: 12,
  },
  primaryButton: {
    alignItems: 'center',
    backgroundColor: '#d7a413',
    marginTop: 24,
    paddingVertical: 14,
  },
  primaryButtonText: {
    color: '#1b1200',
    fontSize: type.bodyLarge,
    fontWeight: '800',
  },
  safeArea: {
    backgroundColor: palette.background,
    flex: 1,
  },
  securityBar: {
    alignItems: 'center',
    backgroundColor: palette.panel,
    borderColor: '#6c5211',
    borderWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  securityLabel: {
    color: palette.warning,
    fontSize: type.tiny,
    letterSpacing: 1.4,
  },
  securityText: {
    color: palette.warning,
    fontSize: type.label,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  subtitle: {
    color: '#6f88aa',
    fontSize: type.subtitle,
    marginTop: 8,
  },
  supportAccent: {
    color: palette.warning,
    fontWeight: '700',
  },
  supportCopy: {
    color: palette.mutedStrong,
    fontSize: type.body,
    marginTop: 16,
    textAlign: 'center',
  },
  title: {
    color: palette.text,
    fontSize: type.title + 1,
    fontWeight: '800',
    marginTop: 22,
  },
  topDivider: {
    backgroundColor: palette.border,
    height: 20,
    width: 1,
  },
  topLabel: {
    color: palette.mutedStrong,
    fontSize: type.label,
    letterSpacing: 2,
  },
  topRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 12,
  },
});
