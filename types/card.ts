export type Dictionary<T, K> = {
    //@ts-ignore
    [key: T]: K 
}

export type CardJson = {
    university: string, 
    institute: string, 
    branch: string, 
    images:Dictionary<string, string>,
    sem_data: Dictionary<string, Dictionary<string, [string, number | string]>>,
    personal: Dictionary<string, string>
}

export type useScanType = [
    boolean, 
    () => void,
    () => void
]

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

export type usePageType = [
    boolean,
    boolean,
    () => void,
    () => void,
]