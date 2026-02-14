export const lightTheme = {
  // Primary colors - BMS Electric Brand
  primary: '#007A8C', // Teal - main brand color
  secondary: '#FFDD1C', // Yellow - accent color
  thirdary: '#5DB86D', // Green - success/positive
  accent: '#8B9556', // Olive - from logo
  
  // Neutral colors
  white: '#FFFFFF',
  black: '#000000',
  background: '#F8F9FA',
  cardBackground: '#FFFFFF',
  
  // Text colors
  textPrimary: '#1A1A1A',
  textSecondary: '#7D7D7D',
  textLight: '#999999',
  textMuted: '#666666',
  textOnPrimary: '#FFFFFF',
  
  // UI Elements
  border: '#F0F0F0',
  divider: '#F5F5F5',
  inputBackground: '#F5F5F5',
  placeholder: '#CCCCCC',
  
  // Specialty colors
  bgHighlight: '#F7FCF9', // Very light green highlight
  borderHighlight: '#E8F5EE', // Light green border
  
  // Status
  error: '#FF3B30',
  success: '#34C759',
  warning: '#FFCC00',
  notification: '#FF3B30',
  
  // Transparency/Overlays
  overlay: 'rgba(0, 0, 0, 0.3)',
  overlayDark: 'rgba(0, 0, 0, 0.6)',
  overlayLight: 'rgba(255, 255, 255, 0.15)',
  overlayWhite: 'rgba(255, 255, 255, 0.8)',
};

export const darkTheme = {
  // Primary colors - BMS Electric Brand (Dark Mode)
  primary: '#00A3BA', // Lighter teal for dark mode
  secondary: '#FFE54D', // Brighter yellow for dark mode
  thirdary: '#5DB86D', // Green
  accent: '#A8B26E', // Lighter olive
  
  // Neutral colors
  white: '#FFFFFF',
  black: '#000000',
  background: '#000000',
  cardBackground: '#121212',
  
  // Text colors
  textPrimary: '#FFFFFF',
  textSecondary: '#B0B0B0',
  textLight: '#808080',
  textMuted: '#999999',
  textOnPrimary: '#000000',
  
  // UI Elements
  border: '#1F1F1F',
  divider: '#1A1A1A',
  inputBackground: '#1A1A1A',
  placeholder: '#555555',
  
  // Specialty colors
  bgHighlight: '#0A1A12', // Subtle dark green for unread/highlights
  borderHighlight: '#0F2F1F',
  
  // Status
  error: '#FF453A',
  success: '#32D74B',
  warning: '#FFD60A',
  notification: '#FF453A',
  
  // Transparency/Overlays
  overlay: 'rgba(255, 255, 255, 0.1)',
  overlayDark: 'rgba(0, 0, 0, 0.8)',
  overlayLight: 'rgba(255, 255, 255, 0.05)',
  overlayWhite: 'rgba(255, 255, 255, 0.2)',
};

// Default export for backward compatibility during transition
export const COLORS = lightTheme;

export const SIZES = {
  padding: 20,
  margin: 20,
  radius: 12,
  radiusLarge: 20,
  fontSmall: 12,
  fontMedium: 14,
  fontLarge: 16,
  fontXL: 20,
  fontXXL: 24,
};

export const SHADOWS = {
  light: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  medium: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
  },
};

const theme = { COLORS, SIZES, SHADOWS };

export default theme;
