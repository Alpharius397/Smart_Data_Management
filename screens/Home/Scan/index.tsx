import { createContext, useContext, useState } from "react";
import ScanScreen from "./NfcScan";
import PaymentScreen from "./Payment";
import { RefreshControl, StyleSheet, ScrollView } from 'react-native';
import { StackParam } from "../../../zod/screens";

type ContextType = {
    card: string | null,
    setCard: (cardID: string) => void
}
const Context = createContext({card: null, setCard: (cardID: string)=>{}});

export function useCard(): ContextType {
    return useContext(Context);
}

export default function ScanSection({ navigation }: StackParam ){
    const [card, setCard] = useState<string | null>(null);
    const [isScan, setScan] = useState<boolean>(true);

    const setScanning = () => {
        setCard(null);
        setScan(true);
    }

    const setPurchasing = () => {
        setScan(false);
    }

    const Component = () => {
        if(isScan){
            return <ScanScreen switchPurchase={setPurchasing} />
        } else {
            return <PaymentScreen switchToScan={setScanning} />
        }
    }

    return (
        <Context.Provider value={{card, setCard}}>
            <ScrollView contentContainerStyle={styles.centeredContainer} 
                refreshControl={
                    <RefreshControl onRefresh={setScanning} refreshing={false}></RefreshControl>
                    }
                >
                <Component />
                
            </ScrollView>
        </Context.Provider>
    )
}

const styles = StyleSheet.create({
    centeredContainer: {
        flexGrow: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 16,
    }    
});