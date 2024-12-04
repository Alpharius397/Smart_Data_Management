const fs = require('fs');
const zlib = require('zlib');
const crypto = require('crypto');
const path = require("path")

// Encryption parameters
const initial_vector = 8;
const encryptionKey = "123456789012345678901234"; // 24-byte key for 3-DES
const json_content = path.join(__dirname,'result.json');

// Read and process the CSV file
fs.readFile('output_csv/SEM-1.csv', 'utf8', (err, data) => {
    if (err) {
        console.error("Error reading file:", err);
        return;
    }
    
    // Convert CSV to JSON (line by line)
    const lines = data.split('\n').filter(line => line.trim() !== ''); // Remove empty lines
    const headers = lines[0].split(',');
    const rows = lines.slice(1);
    
    rows.forEach((line, index) => {
        const values = line.split(',');
        const jsonObject = headers.reduce((obj, header, i) => {
            obj[header.trim()] = values[i]?.trim();
            return obj;
        }, {});
        
        // Extract the card number from the current line
        const cardNumber = jsonObject['SMART_CARD_NO']; // Adjust column name if different
        if (!cardNumber) {
            console.error(`Card number missing in line ${index + 2}`);
            return;
        }
        
        // Compress the JSON string of the row
        const jsonString = JSON.stringify(jsonObject);
        zlib.gzip(jsonString, (err, compressedData) => {
            if (err) {
                console.error(`Compression error for line ${index + 2}:`, err);
                return;
            }
            
            // Encrypt the compressed data using 3-DES
            const iv = crypto.randomBytes(initial_vector); // 8-byte initialization vector
            const cipher = crypto.createCipheriv('des-ede3-cbc', encryptionKey, iv);
            let encryptedData = cipher.update(compressedData);
            encryptedData = Buffer.concat([iv,encryptedData, cipher.final()]); //  added iv into encrypted data for decryption later
            
            // Output the object
            const output = {
                card_number: cardNumber,
                encrypted_data: encryptedData.toString('base64') // Base64 encoded
            };

            // fs.writeFileSync(json_content,JSON.stringify(output)); // testing file size

            const decompressed = decompress_decrypt(output,encryptionKey);

            console.log(output,decompressed);
            
        })
        });



    });

// Decompress and decrypted the json object
function decompress_decrypt(encrypted_json,encryptionKey){
    
    keys = new Set(Object.keys(encrypted_json));
    
    if(keys.has("encrypted_data") && keys.has("card_number")){
        const data = Buffer.from(encrypted_json.encrypted_data,'base64');

        const iv = data.subarray(0,initial_vector);
        const encryptedData = data.subarray(initial_vector);

        const decipher = crypto.createDecipheriv('des-ede3-cbc', encryptionKey, iv);
        const decryptedData = Buffer.concat([decipher.update(encryptedData),decipher.final()]);

        const decompressedData = zlib.unzipSync(Buffer.from(decryptedData));

        const input = {
            card_number:encrypted_json.card_number,
            decrypted_data:JSON.parse(decompressedData.toString('utf-8'))
        }

        return input;
        
    }
    else{
        console.log("'encrypted_data' and 'card_number' keys not found");
        return JSON.parse({});
    }
}