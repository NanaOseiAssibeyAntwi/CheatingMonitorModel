import { DarkTheme, ThemeProvider } from '@react-navigation/native';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import 'react-native-reanimated';

import { palette } from '@/constants/design';

const navigationTheme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    background: palette.background,
    border: palette.border,
    card: palette.panel,
    notification: palette.danger,
    primary: palette.teal,
    text: palette.text,
  },
};

export default function RootLayout() {
  return (
    <ThemeProvider value={navigationTheme}>
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: palette.background } }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="sign-in" />
        <Stack.Screen name="invigilator-sign-in" />
        <Stack.Screen name="exam-session" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="(invigilator-tabs)" />
      </Stack>
      <StatusBar style="light" backgroundColor={palette.background} />
    </ThemeProvider>
  );
}
