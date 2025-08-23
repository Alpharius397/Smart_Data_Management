import RazorpayCheckout from 'react-native-razorpay';
import { RAZORPAY } from '../secret';
import { OptionJson, SuccessCallBack, ErrorCallBack, CheckoutJsonType, CheckoutError, CheckoutJson } from '../zod/razorpay';

const IMAGE_URL = 'https://static.wikia.nocookie.net/warhammer40k/images/0/07/Adeptus_mecanics.jpg'

function amountValue(value: number): string {
    return value.toString() + '00';
}

export function generateOption(
    email: string ='asd', 
    contact: string ='9874563210',
    amount: number =100,
    name: string='NFC RazorPay',
    description: string ='NFC Payment' 
    ): OptionJson {

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

export function beginPayment(option: OptionJson, successCallback: SuccessCallBack, errorCallback: ErrorCallBack){

    RazorpayCheckout.open(option)
        .then((data: CheckoutJsonType) => {

            let jsonData = CheckoutJson.safeParse(data);

            if(jsonData.success === true){
                successCallback(jsonData.data.razorpay_order_id, jsonData.data.razorpay_payment_id);
            } else {
                errorCallback({code: 'RazorPay-Fail', description: 'Failed to parse Razorpay Response', source: 'Razorpay', step: 'After Payment', reason: 'Zod', metadata:{}});

            }
        })
        .catch((error: CheckoutError) => {
            errorCallback(JSON.parse(error.description).error);
    });
}