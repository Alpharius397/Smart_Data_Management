import { StackNavigationProp } from "@react-navigation/stack"

export type StackNavigationParam = {
    Login: {},
    Register: {},
    Home: {},
    Card: {},
    Username: {},
    Password: {},
    Email: {},
    Delete: {},
    Forgot: {},
}

export type StackParam = {
    navigation: StackNavigationProp<StackNavigationParam>
}
