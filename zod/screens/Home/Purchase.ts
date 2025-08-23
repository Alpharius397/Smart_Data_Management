import * as z from "zod";
import { validString } from '../../';

export const PurchaseSchema = z.object({
    cardID: validString,
    order_id: validString,
    payment_id: validString
});

export type PurchaseType = z.infer<typeof PurchaseSchema>;


export type usePurchaseType = [
    boolean, 
    (
        cardID:string, 
        order_id: string, 
        payment_id: string,
        paymentOk: () => void,

        /** payment failed */
        paymentFailed: (error: string) => void, 
        
        /** Failed to Pay */
        paymentError: (error: string) => void,
    ) => Promise<void>
]

export type useLoadingTextType = [
    string,
    () => void,
    () => void,
    () => void,
]