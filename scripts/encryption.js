const { Buffer } = require('buffer');
const CryptoJS = require('crypto-js');
const pako = require('pako');

const inital_vector = 8;
const iv_length = 12;

function encrypt_data(jsonObject,encryptionKey){
    const data = new TextEncoder().encode(JSON.stringify(jsonObject));

    try{
        const compressed = Buffer.from(pako.deflate(data)).toString('base64'); // bytes (encoder|Buffer) -> base64
        const iv = CryptoJS.lib.WordArray.random(inital_vector);
        const encrypt = CryptoJS.TripleDES.encrypt(compressed,encryptionKey,{iv:iv,mode:CryptoJS.mode.CBC,padding:CryptoJS.pad.Pkcs7}).toString('base64'); // bytes (Crypto) -> base64
        
        const to_send = iv.toString(CryptoJS.enc.Base64) + ':' + encrypt; // base64 data
        return to_send;
    }
    catch(error){
        console.log(error);
        return null;
    }
}

/**
 * 
 * @param {string} data 
 * @param {*} encryptionKey 
 * @returns 
 */
function decrypt_data(data,encryptionKey){

    const iv_64 = data.slice(0, iv_length), encryptData = data.slice(iv_length);
    const iv = CryptoJS.enc.Base64.parse(iv_64);
    try{
        const decrypt = CryptoJS.TripleDES.decrypt(encryptData,CryptoJS.enc.Utf8.parse(encryptionKey),{iv:iv,mode:CryptoJS.mode.CBC,padding:CryptoJS.pad.Pkcs7}).toString(CryptoJS.enc.Base64); // bytes (Crypto)-> utf-8 {for js} | Base64 {for python} (to get encrypted data which is of form base64)
        const decompress = pako.inflate(Buffer.from(decrypt,'base64'),{raw:false,to:"string"}); // base64 (buffer) -> byte (pako) -> string
        console.log(decompress)
        return JSON.parse(decompress);
    }
    catch(error){
        console.log(error);
        return null;
    }
}

module.exports = {decrypt_data}