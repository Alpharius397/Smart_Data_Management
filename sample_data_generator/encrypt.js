const { Buffer } = require('buffer');
const CryptoJS = require('crypto-js');
const pako = require('pako');
const path = require('path');
const { readFileSync,writeFileSync,createReadStream } = require("fs");
const parse = require('csv-parser');
const sharp = require('sharp');
const {Image} = require('image-js');

const inital_vector = 8;
const iv_length = 12;
const CSV_PATH = path.join(__dirname,'sample_data','csv_data','SEM-1.csv');
const TXT_PATH = path.join(__dirname,'sample_data','csv_data','sample.txt');

function encrypt_data(jsonObject,encryptionKey){
    const data = JSON.stringify(jsonObject);

    try{
        const compressed = Buffer.from(pako.deflate(data,{level:9})).toString('base64'); // bytes (encoder|Buffer) -> base64
        const iv = CryptoJS.lib.WordArray.random(inital_vector);
        const encrypt = CryptoJS.TripleDES.encrypt(compressed,CryptoJS.enc.Utf8.parse(encryptionKey),{iv:iv,mode:CryptoJS.mode.CBC,padding:CryptoJS.pad.Pkcs7}).toString(); // bytes (Crypto) -> base64
        
        const to_send = `${iv.toString(CryptoJS.enc.Base64)}:${encrypt}`; // base64 data
        return to_send;
    }
    catch(error){
        console.log(error);
        return null;
    }
}


async function extract_image(img_path){
   const buffer = sharp(img_path);
   const reduce_factor = 3;
   const {width, height} = await buffer.metadata();

   let new_w = parseInt(width/reduce_factor), new_h = parseInt(height/reduce_factor);

   let result = await buffer.resize(new_w,new_h, {fit:sharp.fit.fill}).jpeg({ quality:70 }).toBuffer();
   return {data:Buffer.from(result).toString('base64'),width,height};
}

function readData(file_path){
    createReadStream(file_path).pipe(parse()).on('data', async function(csvrow) {
        
        const image = await extract_image(csvrow.IMAGE);
        const key = "123456789123456789";
        csvrow.IMAGE = image;

        const encrypt = encrypt_data(csvrow,key);
        
        writeFileSync(TXT_PATH,encrypt);
        console.log(csvrow);

        console.log(decrypt_data(encrypt,key));
        

    })
    .on('end',function() {
            console.log('Done');
    });
}
/**
 * 
 * @param {string} data 
 * @param {string} encryptionKey 
 * @returns 
 */
function decrypt_data(data,encryptionKey){

    const [iv_64, encryptData] = data.split(':');
    const iv = CryptoJS.enc.Base64.parse(iv_64);
    try{
        const decrypt = CryptoJS.TripleDES.decrypt(encryptData,CryptoJS.enc.Utf8.parse(encryptionKey),{iv:iv,mode:CryptoJS.mode.CBC,padding:CryptoJS.pad.Pkcs7}).toString(CryptoJS.enc.Utf8); // bytes (Crypto)-> utf-8 {for js} | Base64 {for python} (to get encrypted data which is of form base64)
        const decompress = pako.inflate(Buffer.from(decrypt,'base64'),{raw:false,to:"string"}); // base64 (buffer) -> byte (pako) -> string
        console.log(decrypt,decompress)
        return JSON.parse(decompress);
    }
    catch(error){
        console.log(error);
        return null;
    }
}

// readData(CSV_PATH)

// var data = '0iL5FjX6Y88=:5Mz0yV4utBF4HP7x6HRqf1/vXyD48reoecnm8jdzc/Y=';
// var comp = encrypt_data({a:1},"123456789123456789123456")
// console.log(comp)
// var decomp = decrypt_data(comp,"123456789123456789123456")