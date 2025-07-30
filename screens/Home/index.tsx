import { NavigationIndependentTree } from "@react-navigation/native";
import { CardScreen } from "./Card";
import { ScanScreen } from "./Scan";
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Home, Nfc, Settings } from 'lucide-react-native';
import { View } from "react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const Tab = createBottomTabNavigator();
const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>

      <NavigationIndependentTree>
          {/** @ts-expect-error */}
          <Tab.Navigator>
              <Tab.Screen 
                  name="Home" 
                  component={CardScreen} 
                  options={{
                      tabBarIcon: ({ size, color }) => (
                      <View>
                          <Home size={size} color={color} />
                      </View>
                      ),
                  }} 
              />
              <Tab.Screen 
                  name="Scan" 
                  component={ScanScreen} 
                  options={{
                      tabBarIcon: ({ size, color }) => (
                      <View>
                          <Nfc size={size} color={color} />
                      </View>
                      ),
                  }} 
              />
              {/* <Tab.Screen 
                  name="Settings" 
                  component={ScanScreen} 
                  options={{
                      tabBarIcon: ({ size, color }) => (
                      <View>
                          <Settings size={size} color={color} />
                      </View>
                      ),
                  }} 
              /> */}
          </Tab.Navigator>
      </NavigationIndependentTree>
      </QueryClientProvider>
  
  );
}