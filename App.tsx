import React from 'react';
import { NavigationIndependentTree, NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import Login from './screens/Login';
import Register from './screens/Register';
import Home from './screens/Home';
import Username from './screens/Settings/Username.Change';
import Password from './screens/Settings/Password.Change';
import Email from './screens/Settings/Email.Change';
import Delete from './screens/Settings/Delete.Account';
import Forgot from './screens/Forgot';
import { View } from 'react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const Stack = createStackNavigator();
const queryClient = new QueryClient()

function AppStack(){

  return (
    <QueryClientProvider client={queryClient}>
    {/** @ts-ignore */}
      <Stack.Navigator 
        screenOptions={{
        headerTitle:'',
        headerTransparent:true,
        headerLeft: () => {return <View></View>}
      }}>
        <Stack.Screen name="Login" component={Login}/>
        <Stack.Screen name="Register" component={Register} />
        <Stack.Screen name="Home" component={Home} />
        <Stack.Screen name="Username" component={Username} />
        <Stack.Screen name="Password" component={Password} />
        <Stack.Screen name="Email" component={Email} />
        <Stack.Screen name="Delete" component={Delete} />
        <Stack.Screen name="Forgot" component={Forgot} />
    </Stack.Navigator>
  </QueryClientProvider>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <AppStack/>
    </NavigationContainer>
  );
}
