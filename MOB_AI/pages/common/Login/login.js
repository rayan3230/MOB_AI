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
  Modal,
  TouchableWithoutFeedback,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import styles from './style';
import {
  FontAwesome
} from '@expo/vector-icons';
import { COLORS } from '../../../constants/theme.js';

const Dropfield = ({ label, value, options, onSelect }) => {
  const [modalVisible, setModalVisible] = useState(false);

  return (
    <View>
      <TouchableOpacity
        style={styles.dropfield}
        onPress={() => setModalVisible(true)}
        activeOpacity={0.7}
      >
        <Text style={styles.dropfieldText}>{value}</Text>
        <FontAwesome name="chevron-down" size={18} color={COLORS.primary} />
      </TouchableOpacity>

      <Modal visible={modalVisible} transparent animationType="fade">
        <TouchableWithoutFeedback onPress={() => setModalVisible(false)}>
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>{label}</Text>
                <TouchableOpacity onPress={() => setModalVisible(false)}>
                  <FontAwesome name="close" size={24} color="#333" />
                </TouchableOpacity>
              </View>

              <ScrollView showsVerticalScrollIndicator={false}>
                {options.map((option, index) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.modalOption,
                      value === option && styles.modalOptionSelected,
                    ]}
                    onPress={() => {
                      onSelect(option);
                      setModalVisible(false);
                    }}
                  >
                    <Text
                      style={[
                        styles.modalOptionText,
                        value === option && styles.modalOptionTextSelected,
                      ]}
                    >
                      {option}
                    </Text>

                    {value === option && (
                      <FontAwesome
                        name="check-circle"
                        size={24}
                        color={COLORS.primary}
                      />
                    )}
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          </View>
        </TouchableWithoutFeedback>
      </Modal>
    </View>
  );
};

const SigninSignup = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [selectedRole, setSelectedRole] = useState('voyager');
  const [selectedCountry, setSelectedCountry] = useState('Wilaya');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();
  }, [isLogin]);

  const countries = [
    'Wilaya','Adrar','Chlef','Laghouat','Batna','Béjaïa',
    'Blida','Tlemcen','Tizi Ouzou','Algiers','Oran','Tipaza'
  ];

  const handleContinue = () => {
    setLoading(true);
    setError('');

    setTimeout(() => {
      console.log('FAKE FRONTEND SUBMIT', {
        email,
        password,
        confirmPassword,
        firstName,
        lastName,
        phoneNumber,
        selectedCountry,
        selectedRole,
        isLogin,
      });

      setLoading(false);
    }, 1000);
  };

  return (  /* Signup */
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <Animated.View style={{ flex: 1, opacity: fadeAnim }}>
          <ScrollView
            style={styles.container}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >

            <View style={styles.logoContainer}>
              <Text style={styles.logoText}>MOB AI</Text>
            </View>


            <Text style={styles.title}>
              {isLogin ? 'Welcome Back!' : 'Create Account'}
            </Text>

            <Text style={styles.subtitle}>
              {isLogin
                ? 'Login to continue'
                : 'Join our community of Algerian explorers'}
            </Text>

            <Text style={styles.inputLabel}>Email</Text>
            <View style={styles.inputContainer}>
              <FontAwesome
                name="envelope"
                size={18}
                color={COLORS.primary}
                style={styles.inputIcon}
              />
              <TextInput
                style={styles.input}
                placeholder="your@email.com"
                value={email}
                onChangeText={setEmail}
              />
            </View>

            {!isLogin && (
              <>
                <Text style={styles.inputLabel}>First Name</Text>
                <View style={styles.inputContainer}>
                  <TextInput
                    style={styles.input}
                    placeholder="First Name"
                    value={firstName}
                    onChangeText={setFirstName}
                  />
                </View>

                <Text style={styles.inputLabel}>Last Name</Text>
                <View style={styles.inputContainer}>
                  <TextInput
                    style={styles.input}
                    placeholder="Last Name"
                    value={lastName}
                    onChangeText={setLastName}
                  />
                </View>
              </>
            )}

            <Text style={styles.inputLabel}>Password</Text>
            <View style={styles.inputContainer}>
              <FontAwesome
              name="lock"
              size={18}
              color={COLORS.primary}
              style={styles.inputIcon}
            />
              <TextInput
                style={styles.input}
                placeholder='Enter Your Password'
                secureTextEntry
                value={password}
                onChangeText={setPassword}

              />
            </View>

            {!isLogin && (
              <>
                <Text style={styles.inputLabel}>Confirm Password</Text>
                <View style={styles.inputContainer}>
                  <TextInput
                    style={styles.input}
                    secureTextEntry
                    value={confirmPassword}
                    onChangeText={setConfirmPassword}
                  />
                </View>

                <Text style={styles.inputLabel}>Where are you from?</Text>
                <Dropfield
                  label="Select Wilaya"
                  value={selectedCountry}
                  options={countries}
                  onSelect={setSelectedCountry}
                />

                <Text style={styles.inputLabel}>Phone Number</Text>
                <View style={styles.inputContainer}>
                  <Text style={styles.countryCode}>+213</Text>
                  <TextInput
                    style={styles.input}
                    value={phoneNumber}
                    onChangeText={setPhoneNumber}
                  />
                </View>
              </>
            )}

            <TouchableOpacity
              style={styles.continueButton}
              onPress={handleContinue}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.continueButtonText}>
                  {isLogin ? 'Sign In' : 'Continue'}
                </Text>
              )}
            </TouchableOpacity>

          </ScrollView>
        </Animated.View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

export default SigninSignup;
