import { Dimensions, PixelRatio } from 'react-native';

const { height, width } = Dimensions.get('window');
const shortEdge = Math.min(width, height);
const longEdge = Math.max(width, height);

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);
const widthScale = clamp(shortEdge / 390, 0.92, 1);
const heightScale = clamp(longEdge / 844, 0.94, 1);
const uiScale = Math.min(widthScale, heightScale);

const normalize = (size: number, factor = uiScale) =>
  Math.round(PixelRatio.roundToNearestPixel(size * factor));

export const palette = {
  background: '#030712',
  backgroundAlt: '#07111f',
  panel: '#091427',
  panelSoft: '#0c1930',
  panelRaised: '#101d32',
  border: '#17305a',
  borderSoft: '#12304b',
  text: '#f3f6fb',
  muted: '#7890b2',
  mutedStrong: '#9fb4d4',
  teal: '#2de4d8',
  tealSoft: '#0f4b52',
  tealGlow: '#1bcad5',
  warning: '#f1bf21',
  warningSoft: '#342911',
  danger: '#ff4d6d',
  success: '#28ef8d',
};

export const layout = {
  bottomPadding: normalize(26, heightScale),
  cardGap: normalize(10),
  footerSpacer: normalize(shortEdge < 360 ? 104 : 128, heightScale),
  heroTop: normalize(shortEdge < 360 ? 30 : 36, heightScale),
  maxWidth: shortEdge >= 768 ? 560 : 480,
  screenPadding: normalize(shortEdge < 360 ? 14 : 16),
  screenPaddingWide: normalize(shortEdge < 360 ? 12 : 14),
  sectionGap: normalize(18, heightScale),
  tabBarHeight: normalize(shortEdge < 360 ? 62 : 66, heightScale),
  tabBarPaddingBottom: normalize(8, heightScale),
  tabBarPaddingTop: normalize(6, heightScale),
};

export const type = {
  body: normalize(13),
  bodyLarge: normalize(15),
  display: normalize(26),
  hero: normalize(shortEdge < 360 ? 42 : 48),
  label: normalize(10),
  subtitle: normalize(15),
  tiny: normalize(9),
  title: normalize(20),
};
