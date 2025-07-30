import React from 'react';
import { View, Text, StyleSheet,  ActivityIndicator, FlatList } from 'react-native';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { ScrollView } from 'react-native-gesture-handler';
import { CardMeta, CardsJson, InfiniteReactQuery } from '../../types/screens/Home';
import { useInfiniteQuery } from '@tanstack/react-query'
import Axios, { CARDS } from '../../axios';

const Drawer = createDrawerNavigator();

async function fetchCards({ pageParam = 0}: {pageParam: number}): Promise<CardsJson> {
    try {
        const a = await Axios.get(CARDS, {
            params: {
                page: pageParam
            }
        });

        return a.data;

    } catch(err) {
        return {
            cards: [],
            nextPage: 0
        }
    }
}


function LoadingPage(){

    return (
        <View style={waitStyles.container}>
            <ActivityIndicator size="large" color="#4A90E2" style={{marginBottom: 15}} />
            <Text style={waitStyles.text}> "Loading..." </Text>
        </View>
    );
}

const waitStyles = StyleSheet.create({
    container: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
    },
    text: {
        fontSize: 18,
        marginTop: 20,
        marginBottom: 10,
        color: '#333',
        fontWeight: '500',
    },
});

const EmptyList = () => {
    return (
        <View>
            <Text>No Cards Purchased...</Text>
        </View>
    )
}

const Card = ({ cardID, timestamp, university, institute, branch }: CardMeta) => {

    const date = new Date(timestamp);

    function formatDate(date: Date){
        let h = date.getHours(), m = date.getMinutes(), d = date.getDay(), month = date.getMonth(), y = date.getFullYear();
        let denote = (h>12)?('PM'):('AM');

        return `${d%12}:${m} ${denote}, ${d}-${month}-${y}`;

    }

    return (
        <View style={styles.card}>
            <Text style={styles.cardID}>Card ID: {cardID}</Text>
            <Text style={styles.owned}>Owned By: {university}-{institute}-{branch}</Text>
            <Text style={styles.timestamp}>Purchased On: {formatDate(date)}</Text>
        </View>
    )
}

export function CardScreen() {

    const { data, error, fetchNextPage, isFetching, refetch, isFetchingNextPage, hasNextPage } = useInfiniteQuery<CardsJson>({
        queryKey: ['cards'],
        //@ts-expect-error
        queryFn: fetchCards,
        getNextPageParam: (lastPage, pages) => {
            if(lastPage.cards.length == 0) return undefined;
            return lastPage.nextPage;
        }
    });

    const flatList = [];

    if(data && data.pages){
        //@ts-expect-error
        flatList.push(...data.pages.flatMap((card: CardsJson) => card.cards));
    }

    flatList.reverse()

    return (
        <FlatList
            contentContainerStyle={styles.container}
            data={flatList}
            keyExtractor={(item) => {return `${item.cardID}-${item.timestamp}`}}
            renderItem={({ item }) => <Card {...item} />}
            ListEmptyComponent={<EmptyList/>}
            onEndReached={() => {
                if (hasNextPage && !isFetchingNextPage) fetchNextPage();
            }}
            onEndReachedThreshold={0.5}
            ListFooterComponent={
                isFetchingNextPage ? <LoadingPage /> : null
            }
            refreshing={false}
            onRefresh={() => refetch()}
        />
    )

}

// Styles
const styles = StyleSheet.create({
    container: {
        padding: 16,
    },
    card: {
        backgroundColor: '#f8f8f8',
        borderRadius: 12,
        padding: 16,
        marginBottom: 12,
        shadowColor: '#000',
        shadowOpacity: 0.05,
        shadowOffset: { width: 0, height: 2 },
        shadowRadius: 4,
        elevation: 2,
    },
    cardID: {
        fontSize: 18,
        fontWeight: '600',
        color: '#222',
    },
    owned: {
        fontSize: 16,
        color: '#666',
    },
    timestamp: {
        fontSize: 12,
        color: '#666',
        marginTop: 4,
    },
    centeredContainer: {
        flexGrow: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 16,
    },
});



