const { Buffer } = require("buffer");
const { Image } = require("image-js");
const Crypto = require('crypto-js');
const path = require('path');
const { fstat, readFileSync } = require("fs");



const IMAGE = path.join(path.dirname(__dirname),'img','sample-1.jpg');
const GENERATED = path.join(path.dirname(__dirname),'img','generated-1.jpg');
const JSON_c = path.join(path.dirname(__dirname),'img','asd.txt');


export async function get_image(buffer_data, size) {
    const image = await Image.load(Buffer.from(buffer_data,'base64')).resize(size);
    return image.toDataURL('image/jpeg');
} 