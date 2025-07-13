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

export type CheckoutJson = {
    razorpay_order_id: string,
    razorpay_payment_id: string,
}

export type ErrorJsonType = {
    code: string,
    description: string,
    source: string,
    step: string,
    reason: string,
    metadata: object
}

export type CheckoutError = {
    description: JsonSerialized<ErrorJsonType>
}

export type SuccessCallback = (order_id: string, payment_id: string) => void

export type ErrorCallback = (error_data: ErrorJsonType) => void

export type JsonSerialized<T> = string;