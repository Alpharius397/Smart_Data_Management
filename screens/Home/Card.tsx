import React, { useEffect } from 'react';
import { View, Text, StyleSheet,  ActivityIndicator, FlatList, Image, RefreshControl } from 'react-native';
import { useCard } from '../../hooks/screens/Home/Card';
import { CardJson, CardMeta, CardReactList } from '../../zod/screens/Home/Card';
import { DEFAULT_ERROR } from '../../constants';

function LoadingPage(){

    return (
        <View style={waitStyles.container}>
            <ActivityIndicator size="large" color="#4A90E2" />
            <Text style={waitStyles.text}>Loading More Data...</Text>
        </View>
    );
}

const waitStyles = StyleSheet.create({
    container: {
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'row'
    },
    text: {
        fontSize: 18,
        margin: 'auto',
        marginLeft: 10,
        marginRight: 0,
        color: '#333',
        fontWeight: '500',
    },
});

const EmptyList = () => {
    return (
        <View style={{...styles.container, flexGrow: 1}}>
            <View style={{margin: 'auto'}}>
                <Image source={require('../../assets/images/empty.png')} style={styles.image}/>
                    <Text style={{marginLeft: 'auto', marginRight: 'auto', fontSize: 18, fontWeight: 'bold', color: '#666', fontStyle: 'italic'}}>No Cards Purchased</Text>
            </View>
        </View>
    )
}

const ErrorList = () => {
    return (
        <View style={{...styles.container, flexGrow: 1}}>
            <View style={{margin: 'auto'}}>
                <Image source={require('../../assets/images/failed.png')} style={styles.image}/>
                    <Text style={{marginLeft: 'auto', marginRight: 'auto', fontSize: 18, fontWeight: 'bold', color: '#666', fontStyle: 'italic'}}>{DEFAULT_ERROR}</Text>
            </View>
        </View>
    )
}

const Card = ({ cardID, timestamp, university, institute, branch }: CardMeta) => {

    const date = new Intl.DateTimeFormat("en-GB").format(timestamp);

    return (
        <View style={styles.card}>
            <Text style={styles.cardID}>Card ID: {cardID}</Text>
            <Text style={styles.owned}>Owned By: {university}-{institute}-{branch}</Text>
            <Text style={styles.timestamp}>Purchased On: {date}</Text>
        </View>
    )
}

export function CardScreen() {

    const {data, hasNextPage, isFetchingNextPage, fetchNextPage, refetch, isError} = useCard();
    const flatList: CardReactList = [];

    useEffect(() => {
        if(data === undefined) return;
        flatList.push(...data.pages.flatMap((card) => card.cards));
    }, [data]);


    return (
        (!isError) ?
        <FlatList
            contentContainerStyle={{...styles.container, flexGrow: 1, flex: 1}}
            data={flatList}
            keyExtractor={(item) => {return `${item.cardID}-${new Intl.DateTimeFormat("en-GB").format(item.timestamp)}`}}
            renderItem={({ item }) => <Card {...item} />}
            ListEmptyComponent={(!(hasNextPage || isFetchingNextPage)) ? <EmptyList/> : null}
            
            onEndReached={() => {
                if (hasNextPage && !isFetchingNextPage) fetchNextPage({cancelRefetch: false});
            }}

            onEndReachedThreshold={0.5}
            ListFooterComponent={
                (isFetchingNextPage || hasNextPage) ? <LoadingPage /> : null
            }
            refreshControl={
                <RefreshControl refreshing={false} onRefresh={refetch} title='Retry'/>
            }
        /> : 
        <FlatList
            contentContainerStyle={{...styles.container, flexGrow: 1, flex: 1}}
            data={[]}
            renderItem={() => (<></>)}
            ListEmptyComponent={<ErrorList />}
        />
    )

}

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
    image: {
        width: 300,
        height: 300,
        margin: 'auto',
    }
});



