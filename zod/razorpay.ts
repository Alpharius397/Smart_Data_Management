import * as z from "zod";
import { validString } from ".";

export type OptionJson = {
    description: string,
    image: string,
    currency: 'INR',
    key: string, // Your api key
    amount: string,
    name: string,
    prefill: {
        email: string,
        contact: string,
        name: string,
    },
    theme: {
        color: string
    }
}

export type JsonSerialized<T> = string;

export type CheckoutError = {
    description: JsonSerialized<ErrorJsonType>
}

export type SuccessCallBack = (order_id: string, payment_id: string, razorpay_signature: string) => void

export type ErrorCallBack = (error_data: ErrorJsonType) => void

export const ErrorJson = z.object({
    code: validString,
    description: validString,
    source: validString,
    step: validString,
    reason: validString,
    metadata: z.record(
        z.any(), z.any()
    )
});

export const CheckoutJson = z.object({
    razorpay_order_id: validString,
    razorpay_payment_id: validString,
    razorpay_signature: validString,
});


export type ErrorJsonType = z.infer<typeof ErrorJson>
export type CheckoutJsonType = z.infer<typeof CheckoutJson>