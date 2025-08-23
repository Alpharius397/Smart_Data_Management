import React from 'react';
import { Text, TextInput, Button, StyleSheet, StatusBar, SafeAreaView, TouchableOpacity } from 'react-native';
import { showAlert } from '../../utils/alert';
import { DEFAULT_ERROR } from '../../constants';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Popup from '..';
import { useChangeHook, useOtpHook } from '../../hooks/screens/Settings/OTP';
import { PasswordType, PasswordChangeSchema } from '../../zod/screens/Settings/Change';
import { HomeParam } from '../../zod/screens/Home/Card';
import { BackHandler } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';

export default function ChangePassword({ navigation }: HomeParam) {
    const { control, handleSubmit, formState: { errors, isValid } } = useForm<PasswordType>({
        resolver: zodResolver(PasswordChangeSchema),
        mode: "onChange",
    });

    const success = () => {
        showAlert("Password Change", "Your password was successfully updated!");
        navigation.navigate("Login");
    };

    useFocusEffect(
        React.useCallback(() => {
            const onBackPress = () => {
                // Custom navigation here
                // @ts-ignore
                navigation.navigate("Home", {screen: "Settings"});
                return true; 
            };
        
            BackHandler.addEventListener("hardwareBackPress", onBackPress);
        
            return () => BackHandler.removeEventListener("hardwareBackPress", onBackPress);
            }, [navigation])
    );

    const failure = (error: string[]) => {
        showAlert("Password Change", "Failed due to: " + error.join('\n'));
    };

    const error = () => {
        showAlert("Password Change", DEFAULT_ERROR);
    };

    const [submit, isPending] = useChangeHook('username', success, failure, error);
    const [timer, handleSendOTP] = useOtpHook('username');

    const onSubmit = (data: PasswordType) => {
        submit({ data, validator: PasswordChangeSchema });
    };

    return (
        <SafeAreaProvider>
            <SafeAreaView style={styles.container}>
                <Popup visible={isPending} />
                <StatusBar animated={true} backgroundColor="black" />
                
                <Text style={styles.title}>Change Password</Text>

                <Controller
                    control={control}
                    name="OTP"
                    render={({ field: { onChange, value } }) => (
                        <TextInput
                            style={styles.input}
                            placeholder="Enter OTP"
                            placeholderTextColor="black"
                            value={value}
                            onChangeText={onChange}
                        />
                    )}
                />
                {errors.OTP && <Text style={styles.error}>{errors.OTP.message}</Text>}

                <Controller
                    control={control}
                    name="Password"
                    render={({ field: { onChange, value } }) => (
                        <TextInput
                        style={styles.input}
                        placeholder="Enter Password"
                        placeholderTextColor="black"
                        value={value}
                        onChangeText={onChange}
                        secureTextEntry
                    />
                    )}
                />
                {errors.Password && <Text style={styles.error}>{errors.Password.message}</Text>}

                <Controller
                    control={control}
                    name="ConfirmPassword"
                    render={({ field: { onChange, value } }) => (
                        <TextInput
                        style={styles.input}
                        placeholder="Re-enter Password"
                        placeholderTextColor="black"
                        value={value}
                        onChangeText={onChange}
                        secureTextEntry
                    />
                    )}
                />
                {errors.ConfirmPassword && <Text style={styles.error}>{errors.ConfirmPassword.message}</Text>}

                <Button title="Update Password" onPress={handleSubmit(onSubmit)} disabled={!isValid} />

                {timer > 0 ? (
                    <Text style={styles.timer}>Resend OTP in {timer}s</Text>
                ) : (
                    <TouchableOpacity style={styles.resendBtn} onPress={handleSendOTP}>
                        <Text style={styles.resendText}>Resend OTP</Text>
                    </TouchableOpacity>
                )}

            </SafeAreaView>
        </SafeAreaProvider>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', padding: 16 },
    title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
    input: { color: 'black', borderWidth: 1, padding: 10, marginBottom: 10, borderRadius: 5 },
    link: { color: 'blue', marginTop: 10, textAlign: 'center' },
    error: { color: 'red', marginBottom: 10 },
    timer: { 
        color: 'gray', 
        marginTop: 15, 
        textAlign: 'center', 
        fontSize: 16 
    },
    resendBtn: {
        marginTop: 15,
        alignSelf: 'center',
        backgroundColor: '#007AFF', // iOS blue
        paddingVertical: 10,
        paddingHorizontal: 20,
        borderRadius: 25,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.2,
        shadowRadius: 3,
        elevation: 3, // Android shadow
    },
    resendText: {
        color: 'white',
        fontWeight: '600',
        fontSize: 16,
    },
});
