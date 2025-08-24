import React from 'react';
import { Text, TextInput, Button, StyleSheet, StatusBar, SafeAreaView, TouchableOpacity } from 'react-native';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Popup from '..';
import { useChangeHook, useOtpHook } from '../../hooks/screens/Settings/OTP';
import { EmailType, EmailChangeSchema } from '../../zod/screens/Settings/Change';
import { StackParam } from '../../zod/screens';
import { changeCallbacks, customNavigation } from '../../hooks/screens/Settings/Alert';

export default function ChangeEmail({ navigation }: StackParam) {
    const { control, handleSubmit, formState: { errors, isValid } } = useForm<EmailType>({
        resolver: zodResolver(EmailChangeSchema),
        mode: "onChange",
    });
    
    customNavigation(navigation);

    const {success, error, failure} = changeCallbacks(navigation, 'email');

    const [submit, isPending] = useChangeHook('username', success, failure, error);
    const [timer, handleSendOTP] = useOtpHook('username');

    const onSubmit = (data: EmailType) => {
        submit({ data, validator: EmailChangeSchema });
    };

    return (
        <SafeAreaProvider>
            <SafeAreaView style={styles.container}>
                <Popup visible={isPending} />
                <StatusBar animated={true} backgroundColor="black" />
                
                <Text style={styles.title}>Change Email</Text>

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
                    name="Email"
                    render={({ field: { onChange, value } }) => (
                        <TextInput
                        style={styles.input}
                        placeholder="Enter email"
                        placeholderTextColor="black"
                        value={value}
                        onChangeText={onChange}
                    />
                    )}
                />
                {errors.Email && <Text style={styles.error}>{errors.Email.message}</Text>}

                <Button title="Update Email" onPress={handleSubmit(onSubmit)} disabled={!isValid} />

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
