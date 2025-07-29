import { StackNavigationProp } from "@react-navigation/stack"
import { ReactNode } from "react"

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

export type LoadingParams = {
    children: ReactNode;
    loadingText: string
}