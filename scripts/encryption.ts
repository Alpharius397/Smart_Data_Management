import { Buffer } from 'buffer';
import CryptoJS from 'crypto-js';
import pako from 'pako';
import { CardData } from '../protobuf/build/cardData.v3';
import {RSA} from 'react-native-rsa-native';
import { getPrivateKey } from '../storage';

const iv_length = 8;

function unpad(buffer: Buffer): Buffer {
    
    let last_byte = buffer[buffer.length - 1];

    
    let last_slice = buffer.slice(buffer.length - last_byte, buffer.length).toString('hex');
    let verify_slice = Buffer.alloc(last_byte, last_byte).toString('hex');

    if( last_slice !== verify_slice ) {
        throw new Error("Invalid Padding")
    }

    return buffer.slice(0, buffer.length - last_byte);
}

function b64decode(data: string): Buffer {
    return unpad(Buffer.from(data.replace('-','+').replace('_','/'), 'base64'));
}

export default function decrypt_data(data: string, encryptionKey: Uint8Array): CardData | null {

    try{
        const decode_string = b64decode(data);
        const iv = CryptoJS.lib.WordArray.create(Buffer.from(decode_string.subarray(0, iv_length)))
        const data_buffer = CryptoJS.lib.WordArray.create(Buffer.from(decode_string.subarray(iv_length)))
        const key = CryptoJS.lib.WordArray.create(encryptionKey)

        const decrypt = CryptoJS.TripleDES.decrypt(
            //@ts-ignore
            { ciphertext: data_buffer }, 
            key, 
            {
                iv: iv,
                mode: CryptoJS.mode.CBC,
                padding:CryptoJS.pad.Pkcs7
            }
        ).toString(CryptoJS.enc.Hex)

        const decompress = pako.inflate(Buffer.from(decrypt, 'hex'),{ raw:false });
        return CardData.decode(decompress); // protobuffing
    } catch(err) {
        console.warn(err);
        return null;
    }
}

export async function decrypt_key(data: string, decryptionKey: string): Promise<Uint8Array | null> {

    try{
        const decode_string = b64decode(data);
        const iv = CryptoJS.lib.WordArray.create(Buffer.from(decode_string.subarray(0, iv_length)))
        const data_buffer = CryptoJS.lib.WordArray.create(Buffer.from(decode_string.subarray(iv_length)));

        const privateKey = await getPrivateKey();

        /** RSA.decrypt accepts base64 string */
        const key = CryptoJS.enc.Utf8.parse((await RSA.decrypt(b64decode(decryptionKey).toString('base64'), privateKey)));

        const decrypt = CryptoJS.TripleDES.decrypt(
            //@ts-ignore
            { ciphertext: data_buffer }, 
            key, 
            {
                iv: iv,
                mode: CryptoJS.mode.CBC,
                padding:CryptoJS.pad.Pkcs7
            }
        ).toString(CryptoJS.enc.Base64)

        const decompress = pako.inflate(Buffer.from(decrypt, 'base64'),{ raw:false });
        return decompress;
    } catch(err) {
        console.warn(err, "key decrypt");
        return null;
    }
}

export async function generateRsa() {
    const keys = await RSA.generateKeys(2048);
    return keys;
}