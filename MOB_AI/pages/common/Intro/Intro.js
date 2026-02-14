import React from 'react';
import { View, Text, TouchableOpacity, Image, StatusBar } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import styles from './style';
import Logo from '../../../components/Logo';

const Intro = () => {
    const navigation = useNavigation();

    return (
        <View style={styles.container}>
            <StatusBar barStyle="light-content" translucent backgroundColor="transparent" />
            
            <View style={styles.backgroundContainer}>
                <Image 
                    source={require('../../../assets/background.png')} 
                    style={styles.backgroundImage}
                />
            </View>

            <View style={styles.topSection} />

            <View style={styles.contentSection}>
                <View style={styles.logoWrapper}>
                    <Logo width={60} height={60} />
                </View>

                <Text style={styles.description}>
                    Advanced stock management with integrated AI for peak optimization. Streamline your inventory and warehouse operations all in one place.
                </Text>

                <TouchableOpacity 
                    style={styles.button}
                    onPress={() => navigation.navigate('Login')}
                >
                    <Text style={styles.buttonText}>Start the journey</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
};

export default Intro;
