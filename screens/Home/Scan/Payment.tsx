import React from 'react';
import { Text, StyleSheet, TouchableHighlight } from 'react-native';
import { beginPayment, generateOption } from '../../../razorpay/payment';
import { showAlert } from '../../../utils/alert';
import { ErrorJsonType } from '../../../zod/razorpay';
import { usePurchaser } from '../../../hooks/screens/Home/Purchase';
import { PurchaseSchema } from '../../../zod/screens/Home/Purchase';
import Popup from '../..';
import { useCard } from '.';

export default function PaymentScreen({ switchToScan }: {switchToScan: () => void}) {

    const { card } = useCard();

    const paymentGUIOk = () => {
        showAlert("Payment Status", "Payment Successful! Please re-scan the card");
        switchToScan()
    } 

    const paymentGUIError = () => {
        showAlert("Payment Status", "Failed to send Payment Status!");
    }

    const paymentGUIFailed = (error: string[]) => {
        showAlert("Payment Status", "Failed to send Payment Status for the following reasons: " + error.join('\n'));
    }

    const [purchaseCard, isLoading] = usePurchaser(paymentGUIOk, paymentGUIFailed, paymentGUIError);

    function paymentSuccess(order_id: string, payment_id: string){
        purchaseCard({data: {cardID: card, order_id, payment_id}, validator: PurchaseSchema});
    }

    function paymentError(error_data: ErrorJsonType){
        showAlert("Payment Failed", `Payment Failed for the following reason: ${error_data.reason}, done by: ${error_data.source}, at step: ${error_data.step}`);
    }

    function onClick() {
        return beginPayment(generateOption(), paymentSuccess, paymentError)
    }

    return (
        <>
            <Popup visible={isLoading} message='Processing Payment'/>
            <TouchableHighlight onPress={onClick}>
                <Text style={styles.scanButton}>
                    Begin Payment
                </Text>
            </TouchableHighlight>
        </>
    )

}

// Styles
const styles = StyleSheet.create({
    scanButton: {
        backgroundColor: 'lightblue',
        borderRadius: 5,
        padding: 10,
        color: 'white',
        fontWeight: 'bold',
        fontSize: 18
    },
    centeredContainer: {
        flexGrow: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 16,
    },
    
});





