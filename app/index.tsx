import React from 'react';
import { NavigationIndependentTree } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import Login from './src/screens/Login';
import Register from './src/screens/Register';
import Main from './src/screens/Main';
import { View } from 'react-native';


const Stack = createStackNavigator();

function AppStack(){

  return (
    <Stack.Navigator screenOptions={{
      headerTitle:'',
      headerTransparent:true,
      headerLeft: () => {return <View></View>}
    }}>
      <Stack.Screen name="Login" component={Login} />
      <Stack.Screen name="Register" component={Register} />
      <Stack.Screen name="Main" component={Main} />
  </Stack.Navigator>
  );
}

export default function App() {
  return (
    <NavigationIndependentTree>
      <AppStack/>
    </NavigationIndependentTree>
  );
}
