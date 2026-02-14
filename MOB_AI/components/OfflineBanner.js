import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { connectionService } from '../services/connectionService';

const OfflineBanner = () => {
    const [status, setStatus] = useState(connectionService.getStatus());
    const [animation] = useState(new Animated.Value(0));

    useEffect(() => {
        const unsubscribe = connectionService.subscribe((newStatus) => {
            setStatus(newStatus);
            
            // Show banner if any of these are false
            const isOffline = !newStatus.isConnected || !newStatus.isInternetReachable || !newStatus.isServerReachable;
            
            Animated.timing(animation, {
                toValue: isOffline ? 1 : 0,
                duration: 300,
                useNativeDriver: false,
            }).start();
        });

        // Periodic check for server presence
        const interval = setInterval(() => {
            connectionService.checkServerPresence();
        }, 10000);

        return () => {
            unsubscribe();
            clearInterval(interval);
        };
    }, []);

    const height = animation.interpolate({
        inputRange: [0, 1],
        outputRange: [0, 40],
    });

    const getMessage = () => {
        if (!status.isConnected) return "Pas de connexion réseau";
        if (!status.isInternetReachable) return "Pas d'accès Internet";
        if (!status.isServerReachable) return "Serveur non disponible (Mode Hors-ligne)";
        return "";
    };

    return (
        <Animated.View style={[styles.container, { height }]}>
            <View style={styles.content}>
                <Feather name="wifi-off" size={16} color="#FFF" />
                <Text style={styles.text}>{getMessage()}</Text>
            </View>
        </Animated.View>
    );
};

const styles = StyleSheet.create({
    container: {
        backgroundColor: '#EF4444',
        width: '100%',
        overflow: 'hidden',
        justifyContent: 'center',
    },
    content: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingHorizontal: 16,
    },
    text: {
        color: '#FFF',
        fontSize: 13,
        fontWeight: '600',
        marginLeft: 8,
    },
});

export default OfflineBanner;
