import { StyleSheet, Dimensions } from 'react-native';
import { COLORS } from '../../../constants/theme.js';

const { width } = Dimensions.get('window');

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.white,
  },
  container: {
    flex: 1,
    backgroundColor: COLORS.white,
  },
  scrollContent: {
    paddingHorizontal: 30,
    paddingBottom: 40,
    alignItems: 'center',
    paddingTop: 80,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 60,
  },
  logoIcon: {
    marginRight: 15,
  },
  logoText: {
    fontSize: 30,
    fontWeight: '700',
    color: '#1E13FE',
    letterSpacing: 1.5,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 30,
    textAlign: 'center',
  },
  input: {
    width: '100%',
    height: 50,
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 8,
    paddingHorizontal: 15,
    fontSize: 16,
    color: '#333',
    marginBottom: 15,
  },
  continueButton: {
    width: '100%',
    height: 50,
    backgroundColor: '#0070BA',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 10,
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
    width: '100%',
    marginBottom: 30,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#dee2e6',
  },
  dividerText: {
    marginHorizontal: 15,
    color: '#adb5bd',
    fontSize: 14,
  },
  socialButton: {
    width: '100%',
    height: 52,
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 15,
    marginBottom: 15,
  },
  socialIcon: {
    width: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  socialButtonText: {
    flex: 1,
    textAlign: 'center',
    fontSize: 15,
    color: '#212529',
    fontWeight: '600',
    marginRight: 24,
  },
  errorText: {
    color: COLORS.error,
    marginBottom: 15,
    textAlign: 'center',
  }
});

export default styles;
