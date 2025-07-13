import { StackNavigationProp } from "@react-navigation/stack"

export type ParamList = {
    Home: {
        user: string
    },
    Register : {},
    Login: {}
}

export type HomeNavigator = StackNavigationProp<ParamList>

export type HomeParam = {
    navigation: HomeNavigator
}