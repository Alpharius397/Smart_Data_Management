import { useState } from "react";
import ScanScreen from "./NfcScan";
import PaymentScreen from "./Payment";
import { RefreshControl, StyleSheet, ScrollView } from 'react-native';
import { StackParam } from "../../../zod/screens";
import { Context } from "./context";


export default function ScanSection({ navigation }: StackParam ){
    const [card, setCard] = useState<string | null>(null);
    const [isScan, setScan] = useState<boolean>(true);

    const setScanning = () => {
        console.error(1)
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
            <ScrollView contentContainerStyle={styles.centeredContainer}>
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