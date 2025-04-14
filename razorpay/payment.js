import RazorpayCheckout from 'react-native-razorpay';
import { RAZORPAY } from '../secret/apiKey';

const IMAGE_URL = 'https://static.wikia.nocookie.net/warhammer40k/images/0/07/Adeptus_mecanics.jpg'

export function generateOption(email='asd', contact='9874563210', amount=100, name='NFC RazorPay', description='NFC Payment'){
    return {
        description: description,
        image: IMAGE_URL,
        currency: 'INR',
        key: RAZORPAY, // Your api key
        amount: amountValue(amount),
        name: name,
        prefill: {
            email: email,
            contact: contact,
            name: name,
        },
        theme: {color: '#F37254'},
    };
}

/**
 * @param {number} value 
 * @returns {string}
 */
function amountValue(value){
    return value.toString() + '00';
}

/**
 * @param {{description: string, image: string, currency: string, key: string, amount: number, name: string, prefill: {email: string, contact: string, name: string}, theme: {color: string}}} option 
 * @param {(order_id: string, payment_id: string) => void} successCallback 
 * @param {(error: {code: string, description: string, source: string, step: string, reason: string, metadata: object}) => void} errorCallback
 */
export function beginPayment(option, successCallback, errorCallback){

    RazorpayCheckout.open(option)
        .then(data => {
            console.log('Yes');
            successCallback(data.razorpay_order_id, data.razorpay_payment_id)
        })
        .catch(error => {
            console.log('No');
            console.log(error.description)
            errorCallback(JSON.parse(error.description));
    });
}