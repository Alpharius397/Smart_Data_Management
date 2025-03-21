/** NodeJS Code */

// const {Image} = require('image-js');
// const { Buffer } = require('buffer');
// const sample = require('../scripts/sample/header');
//const sharp = require('sharp');
// const path = require('path');
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


/**
 * @param {string} a 
 * @returns {Image}
 */
function generate_image(a) {
    const img = a.split(':');
    const [_ ,__ , data] = img;

    if(data){
        return `data:image/jpeg;base64,${data}`;
    }
    else{
        return null;
    }
}

// generate_image(sample.data.Profile_Image).then((res) => {console.log(res)});

module.exports = {generate_image}