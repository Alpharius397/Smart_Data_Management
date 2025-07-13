import { NativeEventEmitter, NativeModules } from 'react-native';
import { DEFAULT_ERROR } from '../../constants';
import { CardJson } from '../../types/card';
import { NfcModuleType, NfcCardJson, NfcJson } from '../../types/nfc';
import decrypt_data from '../../scripts/encryption';
import { DES3_KEY } from '../../secret';

const { NfcModule } = NativeModules;
const eventType = "onNfcScan";

const emitter = new NativeEventEmitter(NfcModule);

const nfcModule: NfcModuleType = NfcModule

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

export function setListener(callback: (data: CardJson | null) => void): Promise<void> {
    return new Promise<void>(() => {
        try {
            emitter.addListener(eventType, (data: string) => {
                try{
                    let clean_data: string = data.replace(/[\u0000-\u001F]/g, ''); // json related shit
                    let message: NfcJson = JSON.parse(clean_data);
                    let nfcData:CardJson = decrypt_data(message.msg, DES3_KEY);
                    callback(nfcData)
                    emitter.removeAllListeners(eventType);
                }
                catch(error){
                    console.error("Listener Error: ", error)
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
