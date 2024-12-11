/** NodeJS Code */

const {Image} = require('image-js');
const { Buffer } = require('buffer');
//const sharp = require('sharp');
const path = require('path');
//const { writeFileSync } = require('fs');

//const IMAGE = path.join(path.dirname(path.dirname(__dirname)),'img','sample-1.jpg');
//const GENERATED = path.join(path.dirname(path.dirname(__dirname)),'img','generated-1.jpg');
//const COMPRESSED = path.join(path.dirname(path.dirname(__dirname)),'img','compressed-1.jpg');
//const JSON_CONTENT = path.join(path.dirname(path.dirname(__dirname)),'img','result.json');


/**
 * @typedef {Object} IMAGE_DATA
 * @property {string} data // base64 encoded image data
 * @property {number} width // width of image
 * @property {number} height // height of image
 */

/** 
 * @param {string} img_path 
 * @returns {IMAGE_DATA}
 */
//async function extract_image(img_path){
//    const buffer = sharp(img_path);
//    const reduce_factor = 3;
//    const {width, height} = await buffer.metadata();
//
//    let new_w = parseInt(width/reduce_factor), new_h = parseInt(height/reduce_factor);
//
//    let result = await buffer.resize(new_w,new_h, {fit:sharp.fit.fill}).jpeg({ quality:75 }).toBuffer();
//    return {data:Buffer.from(result).toString('base64'),width,height};
//}

async function generate_image(a) {
    const {data,width,height} = a;

    var image = await Image.load(Buffer.from(data,'base64'));
    // writeFileSync('/home/omnissiah/Project/nodejs/react/Smart_Data_Management/src/scripts/asd.json',JSON.stringify(a));
    return image.resize({width:width,height:height,interpolation:"nearestNeighbor"}).toDataURL();

}

//res = extract_image(IMAGE).then((res) => {return generate_image(res)}).then((res) => {console.log(res)});

module.exports = {generate_image}