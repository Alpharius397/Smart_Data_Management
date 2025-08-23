import { StackNavigationProp } from "@react-navigation/stack"
import { BottomTabNavigationProp } from "@react-navigation/bottom-tabs"

type StackNavigationParam = {
    Login: {},
    Register: {},
    Home: {},
    Username: {},
    Password: {},
    Email: {},
    Delete: {},
    Forgot: {},
}

// type TabNavigationParam = {
//     Home: {},
//     Scan: {},
//     Settings: {},
// }

export type StackParam = {
    navigation: StackNavigationProp<StackNavigationParam>
}
