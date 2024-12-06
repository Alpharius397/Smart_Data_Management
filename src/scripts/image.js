/** NodeJS Code */

const {readFileSync} = require('fs');
const {Image} = require('image-js');
// const path = require('path');
const {Buffer} = require('buffer');

// const IMAGE = path.join(path.dirname(path.dirname(__dirname)),'img','sample-1.jpg');
// const GENERATED = path.join(path.dirname(path.dirname(__dirname)),'img','generated-1.jpg');

async function extract_image(img_path){
    var image_data = await Image.load(Buffer.from(readFileSync(img_path),'base64'));
    const width = image_data.width, height = image_data.height;

    image_data = Buffer.from(image_data.resize({width:width/3, height:height/3}).toBuffer()).toString('base64');

    return {data:image_data,width:width,height:height};
}

async function generate_image(a) {
    const {data,width,height} = a;

    var image = await Image.load(Buffer.from(data,'base64'))
    return image.resize({width:width,height:height,interpolation:"nearestNeighbor"}).toDataURL('image/jpeg');

}

// res = extract_image(IMAGE).then((res) => {console.log(res);return generate_image(res);}).then((res) => {console.log(res)});

module.exports = {generate_image}