import { Alert } from 'react-native';

export const showAlert = (msg: string, action: string) =>
    Alert.alert( msg, action, [{ text: 'Ok', style: 'cancel' }], { cancelable: true });