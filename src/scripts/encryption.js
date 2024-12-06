const { Buffer } = require('buffer');
const CryptoJS = require('crypto-js');
const pako = require('pako');



function encrypt_data(jsonObject,encryptionKey){
    const data = JSON.stringify(jsonObject);

    try{
        const compressed = pako.deflate(data);
        const encrypt = CryptoJS.TripleDES.encrypt(Buffer.from(compressed).toString('base64'),encryptionKey).toString();
        return encrypt
    }
    catch(error){
        console.log(error);
        return null;
    }
}

function decrypt_data(data,encryptionKey){

    try{
        const decrypt = Buffer.from(CryptoJS.TripleDES.decrypt(data,encryptionKey).toString()).toString('base64');
        const decompress = pako.inflate(decrypt,{to:'string'});
        return JSON.parse(decompress)
    }
    catch(error){
        console.log(error);
        return null;
    }
}

var data = {asd:123}
var enc = encrypt_data(data,"123")
console.log(decrypt_data(enc,"123"));