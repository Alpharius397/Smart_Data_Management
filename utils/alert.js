import { Alert } from 'react-native';

export const showAlert = (msg,action) =>
    Alert.alert( msg, action, [{ text: 'Ok', style: 'cancel' }], { cancelable: true });