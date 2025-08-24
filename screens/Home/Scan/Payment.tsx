import React from 'react';
import { Text, StyleSheet, TouchableHighlight, View, Image } from 'react-native';
import { beginPayment, generateOption } from '../../../razorpay/payment';
import { ErrorJsonType } from '../../../zod/razorpay';
import { usePurchaser } from '../../../hooks/screens/Home/Purchase';
import { PurchaseSchema } from '../../../zod/screens/Home/Purchase';
import Popup from '../..';
import { useCard } from './context';
import {ALERT_TYPE, Dialog} from 'react-native-alert-notification';

export default function PaymentScreen({ switchToScan }: {switchToScan: () => void}) {

    const { card } = useCard();

    const paymentGUIOk = () => {
        Dialog.show({
            type: ALERT_TYPE.SUCCESS,
            title: "Payment Status",
            textBody: "Payment Successful! Please re-scan the card",
        });
        switchToScan()
    } 

    const paymentGUIError = () => {
        Dialog.show({
            type: ALERT_TYPE.WARNING,
            title: "Payment Status",
            textBody: "Failed to send Payment Status!",
        });
    }

    const paymentGUIFailed = (error: string[]) => {
        Dialog.show({
            type: ALERT_TYPE.WARNING,
            title: "Payment Status",
            textBody:"Failed to send Payment Status for the following reasons: " + error.join('\n'),
        });
    }

    const [purchaseCard, isLoading] = usePurchaser(paymentGUIOk, paymentGUIFailed, paymentGUIError);

    function paymentSuccess(order_id: string, payment_id: string){
        purchaseCard({data: {cardID: card, order_id, payment_id}, validator: PurchaseSchema});
    }

    function paymentError(error_data: ErrorJsonType){
        Dialog.show({
            type: ALERT_TYPE.WARNING,
            title: "Payment Status",
            textBody:`Payment Failed for the following reason: ${error_data.reason}, done by: ${error_data.source}, at step: ${error_data.step}`,
        });
    }

    function onClick() {
        return beginPayment(generateOption(), paymentSuccess, paymentError)
    }

    return (
        <View style={styles.centeredContainer}>
        
        <Image source={require('../../../assets/images/payment.png')} style={styles.imageNoNfc}/>
        <View style={styles.horizontal}>
            <Popup visible={isLoading} message='Processing Payment'/>

            <TouchableHighlight onPress={onClick}>
                <Text style={styles.payment}>
                    Begin Payment
                </Text>
            </TouchableHighlight>
            <TouchableHighlight onPress={switchToScan}>
                <Text style={styles.scanButton}>
                    Back to Scanning
                </Text>
            </TouchableHighlight>
        </View>
        
        </View>
    )

}

// Styles
const styles = StyleSheet.create({
    scanButton: {
        backgroundColor: '#4A90E2',
        borderRadius: 5,
        padding: 10,
        color: 'white',
        fontWeight: 'bold',
        fontSize: 18,
        margin: 5,
        textAlign: 'center'

    },
    centeredContainer: {
        flex: 1,
        padding: 16,
    },
    payment: {
        backgroundColor: "#F57C00",
        borderRadius: 5,
        padding: 10,
        color: 'white',
        fontWeight: 'bold',
        fontSize: 18,
        margin: 5,
        textAlign: 'center'

    },
    horizontal: {
        flex: 1,
        justifyContent:'space-around',
        padding: 16,
    },
    imageNoNfc: {
        width: 300,
        height: 300,
        margin: 'auto',
    }
    
});





