import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert } from 'react-native';


export default function Login({ navigation }) {
  const [user, setUser] = useState('');
  const [password, setPassword] = useState('');

  const showAlert = (msg,action) =>
    Alert.alert(
      msg,
      action,
      [
        {
          text: 'Ok',
          style: 'cancel',
        },
      ],
      {
        cancelable: true
      },
    );

  const handleLogin = () => {
    // Add your login logic here

    if(user=='test' && password=='1234' || true){
        showAlert('Login','Login Successful');
        navigation.navigate("Main",{user:user});
    }
    else{
        showAlert('Login','Login Failed');
    }


  };

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
      <Button title="Login" onPress={handleLogin} />
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
