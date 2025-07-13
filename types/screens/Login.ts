import { StackNavigationProp } from '@react-navigation/stack';

export type ParamList = {
    Home: {
        user: string
    },
    Register : {}
}

export type LoginNavigator = StackNavigationProp<ParamList>

export type LoginParam = {
    navigation: LoginNavigator
}

export type LoginResponse = {
    status: boolean
    error: string | null
    access: string | null
    refresh: string | null
}