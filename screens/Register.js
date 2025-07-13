import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet } from 'react-native';
import Axios, { REGISTER } from '../axios';
import { isAxiosError } from 'axios';
import { showAlert } from '../utils/alert';

export default function Register({ navigation }) {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleRegister = () => {

    async function register() {

      try{
        const response = await Axios.post(REGISTER, 
          {
            "user": username,
            "email": email,
            "password_1":password,
            "password_2": confirmPassword
          });

        const { status, error } = response.data;

        if((error==null && status) || response.status==200){
          showAlert("Register Success", "Registration Successful! Please proceed to Login Page")
        }

        navigation.navigate('Login')
      }

      catch(error){
        if(isAxiosError(error)){
          if(error.status==401){
            if(password!=confirmPassword){
              showAlert("Register Failure", error.response.data.error)
            } 
            else{
              showAlert("Register Failure", error.response.data.error)
            }
          }
          else if(error.status==422){
            showAlert("Register Failure", error.response.data.error)
          }
          else if(error.status==500){
            showAlert("Register Failure", "Server Error Occurred")
          }
          else if(error.status==403){
            showAlert("Login Failure", "Unauthorized Entry")
          }
        }
        console.warn(e);
      }
    }
    register().then();
};

  const emptyCheck = (value) => {
    return (value==null || value=='');
  }

  const checkInput = () => {
    return (false || (emptyCheck(email)) || (emptyCheck(username)) || (emptyCheck(password)) || (emptyCheck(confirmPassword)))
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Register</Text>
      <TextInput
        style={styles.input}
        placeholder="UserName"
        value={username}
        onChangeText={setUsername}
      />
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <TextInput
        style={styles.input}
        placeholder="Confirm Password"
        value={confirmPassword}
        onChangeText={setConfirmPassword}
        secureTextEntry
      />
      <Button title="Register" onPress={handleRegister} disabled={checkInput()}/>
      <Text style={styles.link} onPress={() => navigation.navigate('Login')}>
        Already have an account? Login
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
  input: { borderWidth: 1, padding: 10, marginBottom: 10, borderRadius: 5 },
  link: { color: 'blue', marginTop: 10, textAlign: 'center' },
});
