import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { Tabs } from 'expo-router';
import React from 'react';

import { HapticTab } from '@/components/haptic-tab';
import { layout, palette, type } from '@/constants/design';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: palette.background },
        tabBarActiveTintColor: palette.teal,
        tabBarButton: HapticTab,
        tabBarInactiveTintColor: '#6b7f9c',
        tabBarItemStyle: {
          paddingTop: layout.tabBarPaddingTop,
        },
        tabBarLabelStyle: {
          fontSize: type.tiny,
          fontWeight: '700',
          letterSpacing: 1.1,
          marginTop: 1,
          textTransform: 'uppercase',
        },
        tabBarStyle: {
          backgroundColor: palette.background,
          borderTopColor: palette.border,
          borderTopWidth: 1,
          height: layout.tabBarHeight,
          paddingBottom: layout.tabBarPaddingBottom,
          paddingTop: layout.tabBarPaddingTop + 1,
        },
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => <Ionicons color={color} name="home-outline" size={19} />,
        }}
      />
      <Tabs.Screen
        name="results"
        options={{
          title: 'Results',
          tabBarStyle: { display: 'none' },
          tabBarIcon: ({ color }) => (
            <MaterialCommunityIcons color={color} name="file-document-outline" size={19} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarStyle: { display: 'none' },
          tabBarIcon: ({ color }) => <Ionicons color={color} name="person-outline" size={18} />,
        }}
      />
    </Tabs>
  );
}
