import { Buffer } from 'buffer';
import CryptoJS from 'crypto-js';
import pako from 'pako';
import { CardJson } from '../types/card';

const iv_length = 8;

function unpad(buffer: Buffer): Buffer {
    
    let last_byte = buffer[buffer.length - 1];

    let last_slice = Uint8Array.prototype.slice.call(buffer, buffer.length - last_byte, buffer.length).toString('hex');
    let verify_slice = Buffer.alloc(last_byte, last_byte).toString('hex');

    if( last_slice !== verify_slice ) {
        throw new Error("Invalid Padding")
    }

    return Uint8Array.prototype.slice.call(buffer, 0, buffer.length - last_byte);
}

export default function decrypt_data(data: string, encryptionKey: string): CardJson | null {

    try{
        const decode_string = unpad(Buffer.from(data, 'base64url'));
        const iv = CryptoJS.lib.WordArray.create(Buffer.from(decode_string.subarray(0, iv_length)))
        const data_buffer = CryptoJS.lib.WordArray.create(Buffer.from(decode_string.subarray(iv_length)))
        const key = CryptoJS.enc.Utf8.parse(encryptionKey)

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

        const decompress = pako.inflate(Buffer.from(decrypt, 'base64'),{ raw:false, to:"string"});
        function check_format(jsonData: CardJson): boolean {

        try {
                const { university, institute, branch, images, sem_data, personal } = jsonData;
        
                if(!(
                    check_value(university, ["string"]) &&
                    check_value(institute, ["string"]) &&
                    check_value(branch, ["string"]) &&
                    check_object(images, [["string"], ["string"]]) &&
                    check_object(personal, [["string"], ["string"]]) &&
                    check_object(sem_data, [["string"], ["string"], ["string"], ["string", "number"]])
                )){
                    throw new Error("Invalid Format")
                }
        
                return true;
        
            }
            catch(err) {
                console.warn(err);
                return false;
            }
        
        }
        return JSON.parse(decompress);
    } catch(err) {
        console.warn(err);
        return null;
    }
}