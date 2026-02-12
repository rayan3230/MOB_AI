export const lightTheme = {
  // Primary colors
  primary: '#1E13FE',
  secondary: '#AFD3FF',
  thirdary: '#04324C',
  
  
  // Neutral colors
  white: '#FFFFFF',
  black: '#000000',
  background: '#FFFFFF',
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
  // Primary colors (Neon green inspired by the image)
  primary: '#00FF9D',
  secondary: '#2ECC71',
  
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
