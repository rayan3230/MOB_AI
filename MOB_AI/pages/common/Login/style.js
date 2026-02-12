import { StyleSheet, Dimensions } from 'react-native';
import { COLORS, SIZES, SHADOWS } from '../../../constants/theme.js';

const { width } = Dimensions.get('window');

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.white,
    marginTop: 20, 
  },
  container: {
    flex: 1,
    backgroundColor: COLORS.white,
  },
  scrollContent: {
    paddingHorizontal: 25,
    paddingBottom: 40,
  },
  header: {
    paddingVertical: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },
  backButton: {
    fontSize: 28,
    color: COLORS.textPrimary,
    fontWeight: '400',
  },
  logoContainer: {
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 40,
  },
  logoText: {
    fontSize: 42,
    fontWeight: '900',
    color: COLORS.primary,
    letterSpacing: -1,
  },
  logoSubtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 5,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: COLORS.textSecondary,
    marginBottom: 30,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 8,
    marginLeft: 4,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.bgHighlight,
    borderWidth: 1,
    borderColor: COLORS.borderHighlight,
    borderRadius: 16,
    paddingHorizontal: 15,
    height: 56,
    marginBottom: 20,
  },
  countryCode: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.primary,
    marginRight: 10,
  },
  inputIcon: {
    marginRight: 10,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: COLORS.textPrimary,
    paddingVertical: 0,
  },
  pickerWrapper: {
    backgroundColor: COLORS.bgHighlight,
    borderWidth: 1,
    borderColor: COLORS.borderHighlight,
    borderRadius: 16,
    marginBottom: 20,
    overflow: 'hidden',
    height: 56,
    justifyContent: 'center',
  },
  picker: {
    width: '100%',
    color: COLORS.textPrimary,
  },
  // Dropfield Styles for consistency
  dropfield: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.bgHighlight,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.borderHighlight,
    paddingHorizontal: 15,
    height: 56,
    marginBottom: 20,
  },
  dropfieldText: {
    fontSize: 16,
    color: COLORS.textPrimary,
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: COLORS.white,
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    maxHeight: '70%',
    paddingBottom: 30,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 25,
    borderBottomWidth: 1,
    borderBottomColor: '#F5F5F5',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  modalOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 18,
    marginHorizontal: 15,
    borderRadius: 15,
    marginVertical: 4,
  },
  modalOptionSelected: {
    backgroundColor: '#F0FAF5',
  },
  modalOptionText: {
    fontSize: 17,
    color: '#333',
    fontWeight: '500',
  },
  modalOptionTextSelected: {
    color: COLORS.primary,
    fontWeight: '700',
  },
  infoText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    lineHeight: 18,
    marginBottom: 25,
    textAlign: 'center',
  },
  continueButton: {
    backgroundColor: COLORS.primary,
    height: 56,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    ...SHADOWS.medium,
    marginBottom: 30,
  },
  continueButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
  },
  dividerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 30,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: COLORS.border,
  },
  dividerText: {
    paddingHorizontal: 15,
    color: COLORS.textLight,
    fontSize: 14,
  },
  socialButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  socialButtonCircle: {
    width: (width - 70) / 3, 
    height: 56,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.white,
  },
  socialButtonFull: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    height: 56,
    paddingHorizontal: 20,
    marginBottom: 15,
  },
  socialIcon: {
    marginRight: 15,
  },
  socialButtonText: {
    fontSize: 15,
    color: COLORS.textPrimary,
    fontWeight: '600',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 10,
  },
  footerText: {
    color: COLORS.textSecondary,
    fontSize: 14,
  },
  linkText: {
    color: COLORS.primary,
    fontSize: 14,
    fontWeight: '700',
    marginLeft: 5,
  },
});

export default styles;
