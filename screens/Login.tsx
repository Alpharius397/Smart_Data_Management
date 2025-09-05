import React from 'react';
import { Text, TextInput, Button, StyleSheet, StatusBar, SafeAreaView } from 'react-native';
import { DEFAULT_ERROR } from '../constants';
import { useLogin } from '../hooks/screens/Login';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { LoginForm, LoginSchema } from '../zod/screens/Login';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Popup from '.';
import { StackParam } from '../zod/screens';
import {ALERT_TYPE, Dialog, Toast} from 'react-native-alert-notification';
import { generateRsa } from '../scripts/encryption';
import { setPrivateKey, setPublicKey } from '../storage';

export default function Login({ navigation }: StackParam) {
    
    const { control, handleSubmit, formState: { errors, isValid } } = useForm<LoginForm>({
        resolver: zodResolver(LoginSchema),
        mode: "onChange",
        defaultValues: {
            username: "Student",
            password: "1234567890"
        }
    });

    const success = () => {

        generateRsa().then((key) => {
            setPrivateKey(key.private);
            setPublicKey(key.public);
        });

        navigation.navigate("Card");

        Toast.show({
            type: ALERT_TYPE.SUCCESS,
            title: 'Authentication Status',
            autoClose: 1000,
            textBody: 'Login Successful'
        });            
    };

    const failure = (error: string[]) => {
        Dialog.show({
            type: ALERT_TYPE.WARNING,
            title: 'Authentication Status',
            button: 'Try Again?',
            textBody: error.join('\n')
        });    
    };

    const error = () => {
        Dialog.show({
            type: ALERT_TYPE.DANGER,
            title: 'Authentication Status',
            button: 'Ok',
            textBody: DEFAULT_ERROR
        });  
    };

    const [submit, isPending] = useLogin(success, failure, error);

    const onSubmit = (data: LoginForm) => {
        submit({data: data, validator: LoginSchema});
    }

    return (
        <SafeAreaProvider>
            <SafeAreaView style={styles.container}>
                <Popup visible={isPending} />
                <StatusBar
                    animated={true}
                    backgroundColor="black"
                    />
                
                <Text style={styles.title}>Login</Text>

                <Controller
                    control={control}
                    name="username"
                    render={({ field: { onChange, value } }) => (
                    <TextInput
                        style={styles.input}
                        placeholderTextColor="black"
                        placeholder="Enter Username"
                        value={value}
                        onChangeText={onChange}
                    />
                    )}
                />
                {errors.username && <Text style={styles.error}>{errors.username.message}</Text>}

                <Controller
                    control={control}
                    name="password"
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
                {errors.password && <Text style={styles.error}>{errors.password.message}</Text>}

                <Text style={{...styles.forgot, textAlign: 'right'}} onPress={() => navigation.navigate('Forgot')}>
                    Forgot Password
                </Text>

                <Button title="Login" onPress={handleSubmit(onSubmit)} disabled={!isValid} />

                <Text style={styles.link} onPress={() => navigation.navigate('Register')}>
                    Don't have an account? Register
                </Text>
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
    forgot: { color: 'blue', marginBottom: 5, textAlign: 'center' }
});
