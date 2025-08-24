import React, { createContext, useContext, useState } from 'react';
import { Text, TextInput, Button, StyleSheet, StatusBar, SafeAreaView, TouchableOpacity } from 'react-native';
import { DEFAULT_ERROR } from '../constants';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import Popup from '.';
import { useChangeHook, useForgotOtpHook, useOTP } from '../hooks/screens/Settings/OTP';
import { ForgotPasswordSchema, ForgotPasswordType, ForgotSchema, ForgotType } from '../zod/screens/Forgot';
import { BackHandler } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { StackParam } from '../zod/screens';
import { ALERT_TYPE, Dialog } from 'react-native-alert-notification';

type ForgotContext = {
    setEmailPage: () => void,
    setPasswordPage: () => void,
    email: string | null,
    setEmail: (emailID: string) => void
}
const Context = createContext({email: null, setEmail: (emailID: string)=>{}, setEmailPage: () => {}, setPasswordPage: () => {}});

function useEmail(): ForgotContext {
    return useContext(Context);
}

/**Actual Password Change */
function PasswordChange({ navigation }: StackParam){ 

    const {email, setEmailPage} = useEmail(); 

    const { control, handleSubmit, formState: { errors, isValid } } = useForm<ForgotType>({
        resolver: zodResolver(ForgotSchema),
        mode: "onChange",
        defaultValues: {
            Email: email
        }
    });

    const success = () => {
        setEmailPage();
        navigation.navigate("Login");

        Dialog.show({
            type: ALERT_TYPE.SUCCESS,
            title: "Password Reset",
            button: 'Ok',
            textBody: "Your password was successfully changed",
        });
    };


    const failure = (error: string[]) => {
        Dialog.show({
            type: ALERT_TYPE.DANGER,
            title: "Password Reset",
            button: 'Ok',
            textBody: "Failed due to: " + error.join('\n'),
        });
    };

    const error = () => {
        Dialog.show({
            type: ALERT_TYPE.DANGER,
            title: "Password Reset",
            button: 'Ok',
            textBody: DEFAULT_ERROR,
        });
    };

    useFocusEffect(
        React.useCallback(() => {
            const onBackPress = () => {
                // Custom navigation here
                // @ts-ignore
                setEmailPage();
                return true; 
            };
        
            BackHandler.addEventListener("hardwareBackPress", onBackPress);
        
            return () => BackHandler.removeEventListener("hardwareBackPress", onBackPress);
            }, [navigation])
    );


    const [submit, isPending] = useChangeHook('forgot', success, failure, error);
    const [timer, handleSendOTP] = useForgotOtpHook(email);

    const onSubmit = (data: ForgotType) => {
        console.log(data)
        submit({ data, validator: ForgotSchema });
    };

    return (
        <SafeAreaProvider>
            <SafeAreaView style={styles.container}>
                <Popup visible={isPending} />
                <StatusBar animated={true} backgroundColor="black" />
                
                <Text style={styles.title}>Account Retrieval</Text>

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

                <Button title="Change Password" onPress={handleSubmit(onSubmit)} disabled={!isValid} />

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

function EnterEmail({ navigation }: StackParam){ 
    const { control, handleSubmit, formState: { errors, isValid }, getValues } = useForm<ForgotPasswordType>({
        resolver: zodResolver(ForgotPasswordSchema),
        mode: "onChange",
    });

    const {setEmail, setPasswordPage} = useEmail();

    useFocusEffect(
        React.useCallback(() => {
            const onBackPress = () => {
                // Custom navigation here
                // @ts-ignore
                navigation.navigate("Login");
                return true; 
            };
        
            BackHandler.addEventListener("hardwareBackPress", onBackPress);
        
            return () => BackHandler.removeEventListener("hardwareBackPress", onBackPress);
            }, [navigation])
    );


    const success = () => {

        Dialog.show({
            type: ALERT_TYPE.SUCCESS,
            title: "Account Retrieval",
            button: 'Ok',
            textBody: "OTP has been send for password reset",
        });

        setEmail(getValues("Email"));
        setTimeout(setPasswordPage, 2000);
    };


    const failure = (error: string[]) => {
        Dialog.show({
            type: ALERT_TYPE.DANGER,
            title: "Account Retrieval",
            button: 'Ok',
            textBody: "Failed due to: " + error.join('\n'),
        });
    };

    const error = () => {
        Dialog.show({
            type: ALERT_TYPE.DANGER,
            title: "Account Retrieval",
            button: 'Ok',
            textBody: DEFAULT_ERROR,
        });
    };

    const [sendOTP, isPending] = useOTP('forgot', success, failure, error);

    const onSubmit = (data: ForgotType) => {
        console.log(data)
        sendOTP({ data, validator: ForgotPasswordSchema });
    };

    return (
        <SafeAreaProvider>
            <SafeAreaView style={styles.container}>
                <Popup visible={isPending} />
                <StatusBar animated={true} backgroundColor="black" />
                
                <Text style={styles.title}>Forgot Password</Text>

                <Controller
                    control={control}
                    name="Email"
                    render={({ field: { onChange, value } }) => (
                        <TextInput
                            style={styles.input}
                            placeholder="Enter Email"
                            placeholderTextColor="black"
                            value={value}
                            onChangeText={onChange}
                        />
                    )}
                />
                {errors.Email && <Text style={styles.error}>{errors.Email.message}</Text>}

                <Button title="Check Account" onPress={handleSubmit(onSubmit)} disabled={!isValid} />

            </SafeAreaView>
        </SafeAreaProvider>
    );
}

export default function ForgotPassword({ navigation }: StackParam) {

    const [email, setEmail] = useState<string>("");
    const [emailPage, _setEmailPage] = useState<boolean>(true);

    const setEmailPage = () => {
        _setEmailPage(true);
        setEmail("");
    }
    const setPasswordPage = () => _setEmailPage(false);

    return (
        <Context.Provider value={{email, setEmail, setEmailPage, setPasswordPage}}>
            {
                (emailPage === true) ? (
                    <EnterEmail navigation={navigation}/>
                ) : (
                    <PasswordChange navigation={navigation}/>
                )

            }
        </Context.Provider>
    )

    
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
