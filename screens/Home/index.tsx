import { CardScreen } from "./Card";
import SettingsScreen  from "../Settings";
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Home, Nfc, Settings } from 'lucide-react-native';
import { View } from "react-native";
import ScanScreen from './Scan';
import { StackParam } from "../../zod/screens";

const Tab = createBottomTabNavigator();

export default function App({ navigation }: StackParam) {
    
    return (
        //@ts-ignore
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
            <Tab.Screen 
                name="Settings" 
                children={
                    () => (<SettingsScreen navigation={navigation} />)
                }
                options={{
                    tabBarIcon: ({ size, color }) => (
                    <View>
                        <Settings size={size} color={color} />
                    </View>
                    ),
                }} 
            />
    </Tab.Navigator>
);
}