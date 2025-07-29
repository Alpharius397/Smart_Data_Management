import { useEffect, useState } from 'react';
import { isSupported, removeListener, setListener, startNfcScan } from '../../utils/NfcModule';
import { CardJson, useLoadingTextType, usePageType, usePurchaseType, useScanType } from '../../types/card';
import Axios, { SUBSCRIBER } from '../../axios';
import { isAxiosError } from 'axios';
import { DEFAULT_ERROR } from '../../constants';

const NFC_SCAN_DURATION: number = 1000 * 60; // 1 minute

export function useNFC() {
    const [value, setValue] = useState<boolean>(false);

    useEffect(() => {
        isSupported().then((ok) => {
            setValue(ok);
        });
    }, []);

    return value;
}

export function useScan(
    okCallBack: (data: CardJson | null) => void, 
    errorCallBack: (error: string) => void, 
    paymentNeeded: (message: string) => void,
    timeoutCallback: () => void,

    decryptCallBack: () => void,
    cardFoundCallBack: () => void,
    validityCallBack: () => void,
): useScanType {
    const [isScanning, setScan] = useState<boolean>(false);
    var scanTimer: NodeJS.Timeout | null = null;

    const startScan = () => {
        setScan(true);
    }

    const endScan = () => {
        setScan(false);
    }

    useEffect(() => {

        if(isScanning){
            setListener(okCallBack, errorCallBack, paymentNeeded, decryptCallBack, cardFoundCallBack, validityCallBack);

            scanTimer = setTimeout(() => {
                timeoutCallback();
                setScan(false);
            }, NFC_SCAN_DURATION);

        } else {
            removeListener();
        }

        return () => {
            clearTimeout(scanTimer);
        }

    }, [isScanning]);

    return [isScanning, startScan, endScan];
}

export function usePurchaser(): usePurchaseType {
    const [isLoading, setLoading] = useState<boolean>(false);

    const makePurchase = async (
        cardID:string, 
        order_id: string, 
        payment_id: string,
        paymentOk: () => void,

        /** payment failed */
        paymentFailed: (error: string) => void, 
        
        /** Failed to Pay */
        paymentError: (error: string) => void,
    ) => {
        setLoading(true);
        try{
            const response = await Axios.post(SUBSCRIBER, 
                {
                    cardID: cardID,
                    order_id: order_id,
                    payment_id: payment_id
                }
            )

            const { status, error }:{ status: boolean, error: string | null} = response.data;

            if((status === true) && (error !== null)){
                paymentOk();
            } else {
                paymentFailed(error);
            }
        }
        catch(error){
            if(isAxiosError(error)){
                try {
                    let err: string | null = error.response.data.error;
                    let status_code: number = error.status;

                    if(status_code == 500){
                        paymentError(DEFAULT_ERROR);
                    }
                    else if(err){
                        paymentFailed(err);
                    } else {
                        paymentError(err);
                    }
                } catch(err) {
                    paymentError(DEFAULT_ERROR);
                }

            console.warn(error);

            } else {
                paymentError(DEFAULT_ERROR);
            }
        }
        setLoading(false);
    }

    return [isLoading, makePurchase];
}

export function usePage(scanning_as_default: boolean): usePageType {
    const [value, setValue] = useState<boolean>(scanning_as_default);
    const isScanning = value;
    const isPurchasing = !value;

    const setScanning = () => {
        setValue(true);
    }

    const setPurchasing = () => {
        setValue(false);
    }

    useEffect(() => {
        console.log("running");
        setValue(value);
        console.warn("RUNNING");
    }, [value]);

    return [isScanning, isPurchasing, setScanning, setPurchasing];
}

export function useLoadingText(): useLoadingTextType {
    const [value, setValue] = useState<string>("Waiting for NFC card")

    const cardFound = () => {
        setValue("NFC Card found. Processing card");
    }

    const validity = () => {
        setValue("Verifying Card ownership");
    }

    const decrypt = () => {
        setValue("Decrypting Card data");
    }

    return [value, cardFound, validity, decrypt]

}