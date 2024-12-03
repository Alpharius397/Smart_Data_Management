const { readFileSync, writeFileSync } = require("fs");
const path = require("path");
const file = path.join(__dirname, "img","sample-1.jpg");
const log = path.join(__dirname, "img","asd.log");
const img = path.join(__dirname, "img","generated-1.jpg");

console.log(file);

function extract_image(img_path){
    return readFileSync(img_path, {encoding:'base64'})
}

function reconstruct_image(data, img_path){
    writeFileSync(img_path, Buffer.from(data,'base64'), 'binary')
}

function compress_hex(data,file){
    writeFileSync(file, Buffer.from(data,'base64').toString('hex'))
}

var img_data = extract_image(file);
// compress_hex(img_data,log)
// console.log(img_data)

// reconstruct_image(extract_image(log),img)
reconstruct_image(img_data, img);
compress_hex(img_data, log);

