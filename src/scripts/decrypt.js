const { Buffer } = require('buffer');
const CryptoJS = require('crypto-js');
const pako = require('pako');
const zlib = require('zlib');

function decompress_decrypt(encrypted_json, encryptionKey) {
    const keys = new Set(Object.keys(encrypted_json));

    if (keys.has("encrypted_data") && keys.has("card_number")) {
        try {

            const data = Buffer.from(encrypted_json.encrypted_data).toString('utf-8');

            const bytes = CryptoJS.TripleDES.decrypt(data,encryptionKey);

            const jsonData = CryptoJS.enc.Base64.stringify(bytes);
            console.log(bytes,jsonData);

            // Prepare the output
            return {
                card_number: encrypted_json.card_number,
                // decrypted_data: JSON.parse(jsonData)
            };
        } catch (error) {
            console.error('Error in decompression or decryption:', error);
            return null;
        }
    } else {
        console.error("'encrypted_data' and 'card_number' keys not found");
        return null;
    }
}

async function main() {
    try {
        zlib.gzip("asd", (err,res) => {

            if(err){
                console.log(err);
                return;
               }
            else{
            console.log(res);}
        });
    } catch (error) {
        console.error('Error in fetching or processing data:', error.message);
    }
}
main()