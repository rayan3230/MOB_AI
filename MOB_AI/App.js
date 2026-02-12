import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';
import Login from './pages/common/Login/login';

export default function App() {
  return (
    <>
      <StatusBar style="dark" />
      <Login />
    </>
  )
}

