const path = require('path');
const { readFileSync, writeFileSync } = require('fs')
const sharp = require('sharp');
const { json } = require('body-parser');
const { default: test } = require('node:test');


const IMAGE = path.join(__dirname,'img','sample-1.jpg');
const GENERATED = path.join(__dirname,'img','generated-1.jpg');
const IMAGE_CONTENT = path.join(__dirname,'img','asd.txt');
const JSON_PATH = path.join(__dirname,'img','result.json');

// console.log(IMAGE,GENERATED,IMAGE_CONTENT,JSON_PATH)

async function extract_image(img_path){
    const buffer = sharp(img_path);
    const reduce_factor = 3;
    const {width, height} = await buffer.metadata();

    let new_w = parseInt(width/reduce_factor), new_h = parseInt(height/reduce_factor);

    let result = await buffer.resize(new_w,new_h, {fit:sharp.fit.fill}).jpeg({ quality:75 }).toBuffer();
    return result;
}

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
    dump_json(JSON.stringify({image:text.toString()}),JSON_PATH);
    json_data = await get_json(JSON_PATH);
    get_image(json_data.image,GENERATED,{width:300,height:300});
}

function dump_json(data,file_path){
    writeFileSync(file_path,data);
}

function get_json(file_path){
    return JSON.parse(readFileSync(file_path).toString());
}

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

main()
