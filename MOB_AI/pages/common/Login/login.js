import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Animated,
  ActivityIndicator,
  Image,
  StatusBar,
} from 'react-native';
import styles from './style';
import {
  Feather,
  Ionicons
} from '@expo/vector-icons';
import { authService } from '../../../services/authService';
import Logo from '../../../components/Logo';
import { useNavigation } from '@react-navigation/native';
import { Alert } from 'react-native';

const Signin = () => {
  const navigation = useNavigation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberPassword, setRememberPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();
  }, []);

  const handleContinue = async () => {
    if (!username || !password) {
        setError('Please enter both username and password');
        return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await authService.login(username, password);
      console.log('Login Success:', response);
      
      const user = response.user;
      const role = (user?.user_role || '').toLowerCase();
      
      if (role === 'admin' || role === 'administrator') {
        navigation.replace('AdminHome', { user });
      } else if (role === 'manager' || role === 'supervisor') {
        navigation.replace('SupervisorHome', { user });
      } else if (role === 'employee') {
        navigation.replace('EmployeeHome', { user });
      } else {
        setError('Unknown user role: ' + role);
      }
      
    } catch (err) {
      console.error('Auth error:', err);
      if (err.banned) {
        Alert.alert(
          "Access Denied",
          err.banned,
          [{ text: "OK" }]
        );
      } else {
        const errorMsg = err.non_field_errors?.[0] || err.detail || 'Authentication failed';
        setError(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: '#FFF' }}>
      <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
      
      {/* Background Image Container */}
      <View style={styles.backgroundContainer}>
        <Image 
          source={require('../../../assets/background.png')} 
          style={styles.backgroundImage}
        />
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <Animated.View style={{ flex: 1, opacity: fadeAnim }}>
          <ScrollView
            style={styles.container}
            contentContainerStyle={{ flexGrow: 1 }}
            showsVerticalScrollIndicator={false}
            bounces={false}
          >
            {/* Top Logo Section */}
            <View style={styles.topSection}>
              <View style={styles.logoContainer}>
                <View style={styles.logoIcon}>
                  <Logo width={60} height={60} color="#FFF" />
                </View>
                <Text style={styles.logoText}>FLOWLOGIX</Text>
              </View>
            </View>

            {/* Form Section */}
            <View style={styles.formContainer}>
              <Text style={styles.title}>Log in</Text>

              {error ? <Text style={styles.errorText}>{error}</Text> : null}

              <View style={styles.inputWrapper}>
                <Feather name="mail" size={20} color="#adb5bd" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Email"
                  placeholderTextColor="#adb5bd"
                  value={username}
                  onChangeText={setUsername}
                  autoCapitalize="none"
                  keyboardType="email-address"
                />
              </View>

              <View style={styles.inputWrapper}>
                <Feather name="lock" size={20} color="#adb5bd" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Password"
                  placeholderTextColor="#adb5bd"
                  secureTextEntry
                  value={password}
                  onChangeText={setPassword}
                />
              </View>

              <TouchableOpacity 
                style={styles.rememberContainer}
                onPress={() => setRememberPassword(!rememberPassword)}
                activeOpacity={0.7}
              >
                <View style={[styles.checkbox, rememberPassword && styles.checkboxChecked]}>
                  {rememberPassword && <Ionicons name="checkmark" size={14} color="#FFF" />}
                </View>
                <Text style={styles.rememberText}>Remember Password</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.continueButton}
                onPress={handleContinue}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.continueButtonText}>Continue</Text>
                )}
              </TouchableOpacity>

              <View style={styles.footer}>
                <Text style={styles.footerText}>Dont have an account? </Text>
                <TouchableOpacity onPress={() => navigation.navigate('SignUp')}>
                  <Text style={styles.footerLink}>Sign up</Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </Animated.View>
      </KeyboardAvoidingView>
    </View>
  );
};

export default Signin;
