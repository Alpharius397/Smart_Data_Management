import { useState } from 'react';
import { useLoadingTextType } from '../../../zod/screens/Home/Purchase';
import { URL } from '../../../axios';
import { onErrorType, onFailureType, onSuccessType, useAuthHook } from '../..';


export function usePurchaser(onSuccess: onSuccessType, onFailure: onFailureType, onError: onErrorType) {
    return useAuthHook(URL.CARD.STATUS, 'POST', onSuccess, onFailure, onError);
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