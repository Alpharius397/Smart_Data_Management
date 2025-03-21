import React from 'react';
import { View, Text, StyleSheet, Button, Alert } from 'react-native';
import RazorpayCheckout from 'react-native-razorpay';

// Payment Handler Function
const handlePayment = () => {
    var options = {
        description: 'Payment for Order',
        image: 'https://your-logo-url.com/logo.png',
        currency: 'INR',
        key: 'YOUR_RAZORPAY_KEY', // Replace with Razorpay API Key
        amount: 50000, // Amount in paisa (₹500.00)
        name: 'Your Company Name',
        prefill: {
            email: 'user@example.com',
            contact: '9999999999',
            name: 'John Doe'
        },
        theme: {color: '#528FF0'}
    };

    RazorpayCheckout.open(options)
        .then((data) => {
            // Alert.alert('Payment Successful', Payment ID: ${data.razorpay_payment_id});
            alert('Payment Successful', `Payment ID: ${data.razorpay_payment_id}`);
        })
        .catch((error) => {
            alert('Payment Failed', error.description)
            // Alert.alert('Payment Failed', error.description);
        });
};

// Payment Screen Component
export default function PaymentScreen() {
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Razorpay Payment Gateway</Text>
            <Button title="Pay Now" onPress={handlePayment} />
        </View>
    );
}

// Styles
const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 20,
    },
});