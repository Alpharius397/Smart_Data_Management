import { NativeEventEmitter, NativeModules } from 'react-native';
import { DEFAULT_ERROR } from '../constants';
import { NfcModuleType, NfcCardJson, NfcJson, subscriberSchema, subscriberType } from '../zod/screens/Home/NfcModule';
import decrypt_data, { decrypt_key } from '../scripts/encryption';
import Axios, { URL } from '../axios';
import data from '../protobuf/test.proto';
import { CardProto, CardProtoType } from '../zod/screens/Home/Scan';
import { getPublicKey } from '../storage';

const { NfcModule } = NativeModules;
const eventType = "onNfcScan";

const emitter = new NativeEventEmitter(NfcModule);

const nfcModule: NfcModuleType = NfcModule

async function checkCardValidity(uid: string): Promise<[boolean, Uint8Array | null]> {
    try{
        const pubKey = await getPublicKey();
        const response = await Axios.get(URL.CARD.STATUS, {
            params: {
                cardID: uid,
                pubKey
            }
        });
        const {status, error, key, decryptionKey}: subscriberType = await subscriberSchema.parseAsync(response.data);
        return [((status) === true) && (error.length === 0), await decrypt_key(key, decryptionKey)];
    } catch(err) {
        return [false, null];
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
    okCallBack: (data: CardProtoType, uid: string) => void, 
    errorCallBack: (error: string) => void, 
    paymentNeeded: (cardID:string, message: string) => void,

    decryptCallBack: () => void,
    cardFoundCallBack: () => void,
    validityCallBack: () => void,
): Promise<void> {
    return new Promise<void>(async () => {
        try {
            let nfc_data_card = `{"data": "${data}","ok": true,"uid": 1}`;
            // emitter.addListener(eventType, async (nfc_data_card: string) => {
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
                    
                    let [ownsIt, key] = await checkCardValidity(uid)
                    

                    if(ownsIt){
                        decryptCallBack();
                        let nfcData = await CardProto.safeParseAsync(decrypt_data(data, key));

                        if(nfcData.success === false){
                            console.warn(nfcData.error)
                            errorCallBack("Failed to decrypt card data!")
                        } else {
                            okCallBack(nfcData.data, uid);
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
            // });

        
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
