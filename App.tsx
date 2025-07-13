import React from 'react';
import { NavigationIndependentTree, NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import Login from './screens/Login';
import Register from './screens/Register';
import Main from './screens/Home/scan';
import { View } from 'react-native';


const Stack = createStackNavigator();

function AppStack(){

  return (
    // @ts-ignore
    <Stack.Navigator 
      screenOptions={{
      headerTitle:'',
      headerTransparent:true,
      headerLeft: () => {return <View></View>}
    }}>
      <Stack.Screen name="Login" component={Login}/>
      <Stack.Screen name="Register" component={Register} />
      <Stack.Screen name="Home" component={Main} />
  </Stack.Navigator>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <AppStack/>
    </NavigationContainer>
  );
}
