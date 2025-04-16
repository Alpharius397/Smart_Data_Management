
import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert } from 'react-native';
import Axios, { LOGIN } from '../http/axios';
import { isAxiosError } from 'axios';
import { showAlert } from '../utils/alert';

export default function Login({ navigation }) {
  const [user, setUser] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = () => {

      async function login() {

        try{
          await Axios.post(LOGIN, 
            {
              "user": user,
              "password": password
            });

          showAlert("Login Success", "Login Successful");
          navigation.navigate('Main', {user:user})
        }

        catch(error){
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
          }
          console.warn(error);
        }
      }

      login().then().catch();
    

  };

  const canLoginNow = () => {
    return (user=='' || password=='')
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Login</Text>
      <TextInput
        style={styles.input}
        placeholderTextColor={'black'}
        placeholder="User"
        value={user}
        onChangeText={setUser}
        keyboardType="user-address"
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
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
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
  input: { color:'black', borderWidth: 1, padding: 10, marginBottom: 10, borderRadius: 5 },
  link: { color: 'blue', marginTop: 10, textAlign: 'center' },
});
