import { NativeEventEmitter, NativeModules } from 'react-native';
import { DEFAULT_ERROR } from '../constants';
import { CardJson } from '../types/card';
import { NfcModuleType, NfcCardJson, NfcJson } from '../types/NfcModule';
import decrypt_data from '../scripts/encryption';
import { DES3_KEY } from '../secret';
import Axios, { CARDS } from '../axios';
import { subscriberCheckResponse } from '../types/screens/Login';
import { check_format } from './DataChecker';

const { NfcModule } = NativeModules;
const eventType = "onNfcScan";

const emitter = new NativeEventEmitter(NfcModule);

const nfcModule: NfcModuleType = NfcModule

async function checkCardValidity(uid: string): Promise<boolean> {
    try{
        let response = await Axios.get(CARDS, {
            params: {
                cardID: uid
            }
        });

        const {status, error}: subscriberCheckResponse = response.data;

        return (status === true) && (error === null);
    } catch(err) {
        return false;
    }
}

export function isSupported(): Promise<boolean> {
    
    return new Promise<boolean>(async (resolve) => {
        try{
            let supported = await nfcModule.isSupported();
            resolve(supported)
        } catch(err) {
            resolve(false);
        }
    });
}

export function isEnabled(): Promise<boolean> {
    
    return new Promise<boolean>(async (resolve) => {
        try{
            let supported = await nfcModule.isEnabled();
            resolve(supported)
        } catch(err) {
            resolve(false);
        }
    });
}


export function readyState(): Promise<NfcJson> {
    return new Promise<NfcJson>(async (resolve) => {
        try{
            let res = await nfcModule.readyState();
            resolve(res);
        } catch(err){
            console.warn(err);
            resolve({ok: false, msg: DEFAULT_ERROR});
        }
    });
}

export function startNfcScan(): Promise<void> {
    return new Promise<void>(async () => {
        try {
            await nfcModule.startNfcScan()
        } catch(err){
            console.warn(err);
        }
    });
}

export function DESFireCheck(): Promise<NfcJson> {
    return new Promise<NfcJson>(async (resolve) => {
        try {
            let a = await nfcModule.DESFireCheck()
            resolve(a);
        } catch(err){
            console.warn(err);
            resolve({ok: false, msg: DEFAULT_ERROR});
        }
    });
}

export function setListener(
    okCallBack: (data: CardJson) => void, 
    errorCallBack: (error: string) => void, 
    paymentNeeded: (cardID:string, message: string) => void,

    decryptCallBack: () => void,
    cardFoundCallBack: () => void,
    validityCallBack: () => void,
): Promise<void> {
    return new Promise<void>(() => {
        try {
            emitter.addListener(eventType, async (nfc_data_card: string) => {
                try{
                    cardFoundCallBack();
                    
                    let clean_data: string = nfc_data_card.replace(/[\u0000-\u001F]/g, ''); // json related 
                    let { ok, data, uid }: NfcCardJson = JSON.parse(clean_data);

                    if(ok === false){
                        errorCallBack(DEFAULT_ERROR);
                    }

                    if( uid === null ){
                        errorCallBack("Failed to retrieve Card ID!")
                    }

                    validityCallBack();
                    
                    let ownsIt = await checkCardValidity(uid)

                    if(ownsIt){
                        decryptCallBack();
                        let nfcData: CardJson | null = decrypt_data(data, DES3_KEY);

                        if(nfcData == null){
                            errorCallBack("Failed to decrypt card data!")
                        }

                        if(check_format(nfcData)){
                            okCallBack(nfcData);
                        } else {
                            errorCallBack("Failed to parse the card!")
                        }

                    } else {
                        paymentNeeded(uid, "Card must be purchased first!");
                    }

                }
                catch(error){
                    console.error("Listener Error: ", error)
                } finally {
                    emitter.removeAllListeners(eventType);
                }
            });
        
        } catch(err){
            console.warn(err);
        }
    });
}

export function removeListener(): void {
    emitter.removeAllListeners(eventType);
}

export function endNfcScan(): Promise<void> {
    return new Promise<void>(async () => {
        try{
            await nfcModule.endNfcScan()
        } catch(err) {
            console.warn(err);
        }
    })
}

export default nfcModule;
