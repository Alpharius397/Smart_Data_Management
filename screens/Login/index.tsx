
import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet } from 'react-native';
import Axios, { LOGIN } from '../../axios';
import { isAxiosError } from 'axios';
import { showAlert } from '../../utils/alert';
import { DEFAULT_ERROR } from '../../constants';
import { LoginParam, LoginResponse } from '../../types/screens/Login';

export default function Login({ navigation }: LoginParam): React.JSX.Element {
    const [user, setUser] = useState<string>('');
    const [password, setPassword] = useState<string>('');

    const handleLogin = () => {

        Axios.post(LOGIN, { "user": user, "password": password }).then((response) => {

            try {
                const { status, error }: LoginResponse = response.data;
            
                if( status === true && error === null){
                    showAlert("Login Success", "Login was successful! Redirecting to Home");
                    navigation.navigate('Home', { user: user });
                } else if (error !== null ) {
                    showAlert("Login Failed", `Login was unsuccessful! ${error}`);
                } else {
                    showAlert("Login Failed", "Login was unsuccessful!");
                }
            } catch {
                showAlert("Login Failed", DEFAULT_ERROR);
            }

        })
        .catch((error: Error) => {
            if(isAxiosError(error)){
                if(error.status==401){
                showAlert("Login Failure", "Login Failed! Check username / password")
                }
                else if(error.status==500){
                    showAlert("Login Failure", "Server Error Occurred")
                }
                else if(error.status==403){
                    showAlert("Login Failure", "Unauthorized Entry")
                }
            } else {
                showAlert("Login Failed", DEFAULT_ERROR);
            }
        })

    }

    const canLoginNow = () => {
        return (user ==='' || password ==='')
    }

    return (
        <View style={styles.container}>
            <Text style={styles.title}>
                Login
            </Text>
            <TextInput
                style={styles.input}
                placeholderTextColor={'black'}
                placeholder="Enter Username"
                value={user}
                onChangeText={setUser}
            />
            <TextInput
                style={styles.input}
                placeholder="Enter Password"
                placeholderTextColor={'black'}
                value={password}
                onChangeText={setPassword}
                secureTextEntry
            />
            <Button title="Login" onPress={handleLogin} disabled={canLoginNow()}/>
            <Text style={styles.link} onPress={() => navigation.navigate('Register')}>
                Don't have an account? Register
            </Text>
        </View>
    )
}

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', padding: 16 },
    title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
    input: { color:'black', borderWidth: 1, padding: 10, marginBottom: 10, borderRadius: 5 },
    link: { color: 'blue', marginTop: 10, textAlign: 'center' },
});
