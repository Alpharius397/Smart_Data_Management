import { StackNavigationProp } from "@react-navigation/stack"
import { FetchNextPageOptions, InfiniteData, InfiniteQueryObserverResult, QueryObserverResult, RefetchOptions } from "@tanstack/react-query"
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

export type CardMeta = {
    cardID: string,
    timestamp: string
    university: string,
    institute: string,
    branch: string,
}

export type CardsJson = {
    cards: Array<CardMeta>
    nextPage: number
}

export type InfiniteReactQuery = {
    data: undefined | CardsJson
    error: Error,
    fetchNextPage: (options?: FetchNextPageOptions) => Promise<InfiniteQueryObserverResult<InfiniteData<CardsJson[], unknown>, Error>>
    isFetching: boolean,
    refetch:  (options?: RefetchOptions) => Promise<QueryObserverResult<InfiniteData<CardsJson[], unknown>, Error>>,
    isFetchingNextPage: boolean,
    hasNextPage: boolean
}