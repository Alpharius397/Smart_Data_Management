const path = require('path');
const { readFileSync, writeFileSync } = require('fs')
const sharp = require('sharp');


const IMAGE = path.join(__dirname,'img','sample-1.jpg');
const GENERATED = path.join(__dirname,'img','generated-1.jpg');
const IMAGE_CONTENT = path.join(__dirname,'img','asd.txt');
const JSON_PATH = path.join(__dirname,'img','result.json');



/**
 * @typedef {Object} IMAGE_DATA
 * @property {Buffer} result // image data
 * @property {number} width // width of image
 * @property {number} height // height of image
 */

/** 
 * @param {string} img_path 
 * @returns {IMAGE_DATA}
 */
async function extract_image(img_path){
    const buffer = sharp(img_path);
    const reduce_factor = 3;
    const {width, height} = await buffer.metadata();

    let new_w = parseInt(width/reduce_factor), new_h = parseInt(height/reduce_factor);

    let result = await buffer.resize(new_w,new_h, {fit:sharp.fit.fill}).jpeg({ quality:75 }).toBuffer();
    return {result,width,height};
}

/**
 * @param {Buffer} buffer 
 * @param {string|null} file_path 
 * @returns {string}
 */
function get_buffer_content(buffer, file_path=null){
    let result = Buffer.from(buffer).toString('base64');

    if(file_path!=null){
        writeFileSync(file_path,result);
    }

    return result;
}

async function main() {
    res = await extract_image(IMAGE)
    text = get_buffer_content(res,IMAGE_CONTENT);
    dump_json(JSON.stringify({image:text}),JSON_PATH);
    json_data = await get_json(JSON_PATH);
    get_image(json_data.image,GENERATED,{width:780,height:438});
}

function dump_json(data,file_path){
    writeFileSync(file_path,data);
}

/**
 * @param {string} file_path 
 * @returns {JSON}
 */
function get_json(file_path){
    return JSON.parse(readFileSync(file_path).toString());
}

/**
 * @typedef SIZE
 * @property {number} width
 * @property {number} height
 */

/**
 * @param {string} img_byte 
 * @param {string} image_store 
 * @param {SIZE} size 
 */
async function get_image(img_byte,image_store,size){
    const {width, height} = size;
    const data = Buffer.from(img_byte,'base64');
    
    console.log(data)
    
    sharp(data).resize(width,height,{fit:sharp.fit.fill}).toFile(image_store, function(error,info){
        if(error){
            console.log(error);
        }
        else{
            console.log(info);
        }
    });
}

// main()
module.exports = {extract_image,get_buffer_content,get_image}
