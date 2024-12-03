const { readFile, writeFile } = require("fs");
const path = require("path");
const file = path.join(__dirname, "img","sample-1.jpg");
const log = path.join(__dirname, "img","asd.log");
const img = path.join(__dirname, "img","generated-1.jpg");

console.log(file);


const image = readFile(file, (err,data) => {
    if(err){ console.log(err); }
    console.log(data.toString('base64'));

    writeFile(img, Buffer.from(data.toString('hex'),'hex'),'binary',(err) => {
        if(err){ console.log(err); }
        
    })

});

