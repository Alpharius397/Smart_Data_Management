import { useEffect, useMemo, useState } from 'react';
import { endNfcScan, isSupported, removeListener, setListener, startNfcScan } from '../../../utils/NfcModule';
import { useScanType } from '../../../zod/screens/Home/Scan';
import { CardProtoType, HeaderProtoType, HeaderSchema, HeaderType } from '../../../zod/screens/Home/Scan';
import Axios, {URL} from '../../../axios';
import { DEFAULT_ERROR } from '../../../constants';
import { isAxiosError } from 'axios';
import { zodError } from '../../../zod';
import { useQuery } from '@tanstack/react-query';

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
    okCallBack: (data: CardProtoType, uid: string) => void, 
    errorCallBack: (error: string) => void, 
    paymentNeeded: (cardID: string, message: string) => void,
    timeoutCallback: () => void,

    decryptCallBack: () => void, // GUI hooks
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

        startNfcScan();

        if(isScanning){
            setListener(okCallBack, errorCallBack, paymentNeeded, decryptCallBack, cardFoundCallBack, validityCallBack);

            scanTimer = setTimeout(() => {
                timeoutCallback();
                setScan(false);
            }, NFC_SCAN_DURATION);

        } else {
            removeListener();
            endNfcScan();
        }

        return () => {
            clearTimeout(scanTimer);
        }

    }, [isScanning]);

    return [isScanning, startScan, endScan];
}

async function getHeading(data: HeaderProtoType): Promise<HeaderType> {
    try {

        const response = await Axios.get(URL.CARD.HEADING, {
            params: data
        });

        let a = await HeaderSchema.parseAsync(response.data);

        return a;

    } catch(err){

        if(err instanceof zodError){
            console.warn(err)
            throw new Error("Received Invalid Data");
        }

        if(isAxiosError(err)){
            try {
                if(err.response?.status !== 500){
                    throw new Error("Unauthorized Fetch detected!")
                }
                else{
                    throw new Error(DEFAULT_ERROR);
                }
            } catch(eRR) {
                console.warn(eRR);
                throw new Error(DEFAULT_ERROR);
                
            }
        } else {
            throw new Error(DEFAULT_ERROR);
        }
    }

}

export function useHeader(headerData: HeaderProtoType) {
    const {data, isError, isLoading} = useQuery({
        queryKey: ['heading'],
        queryFn: () => getHeading(headerData),
    });

    const transform = useMemo(() => {
        
        let a = HeaderSchema.safeParse(data);

        if(a.success === true){
            return a.data;
        }
        
        return {
            university: "University Not Found",
            institute: "Institute Not Found",
            branch: "Branch Not Found",
        }
    }, [data]);

    return {transform, isError, isLoading};
}