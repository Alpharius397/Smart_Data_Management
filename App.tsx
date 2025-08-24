import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
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
import {AlertNotificationRoot} from 'react-native-alert-notification';

const Stack = createStackNavigator();
const queryClient = new QueryClient()

function AppStack(){

  return (
    <QueryClientProvider client={queryClient}>
      <AlertNotificationRoot>
        {/** @ts-ignore */}
        <Stack.Navigator 
          screenOptions={{
          headerTitle:'',
          headerTransparent:true,
          headerLeft: () => {return <View></View>}
        }}>
          <Stack.Screen name="Login" component={Login}/>
          <Stack.Screen name="Register" component={Register} />
          <Stack.Screen name="Card" component={Home} />
          <Stack.Screen name="Username" component={Username} />
          <Stack.Screen name="Password" component={Password} />
          <Stack.Screen name="Email" component={Email} />
          <Stack.Screen name="Delete" component={Delete} />
          <Stack.Screen name="Forgot" component={Forgot} />
      </Stack.Navigator>
    </AlertNotificationRoot>
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
