const fs = require('fs');
const zlib = require('zlib');
const crypto = require('crypto');

// Encryption parameters
const encryptionKey = "123456789012345678901234"; // 24-byte key for 3-DES
const iv = crypto.randomBytes(8); // 8-byte initialization vector

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
            const cipher = crypto.createCipheriv('des-ede3-cbc', encryptionKey, iv);
            let encryptedData = cipher.update(compressedData);
            encryptedData = Buffer.concat([encryptedData, cipher.final()]);

            // Output the object
            const output = {
                card_number: cardNumber,
                encrypted_data: encryptedData.toString('base64') // Base64 encoded
            };
            console.log(output);
        });
    });
});
