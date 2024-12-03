from io import BytesIO
from PIL import Image
import os
from base64 import b64decode,b64encode
from typing import IO
import json

IMAGE = os.path.join(os.path.dirname(__file__),'img','sample-1.jpg')
GENERATED = os.path.join(os.path.dirname(__file__),'img','generated-1.jpg')
IMAGE_CONTENT = os.path.join(os.path.dirname(__file__),'img','asd.txt')
JSON_PATH = os.path.join(os.path.dirname(__file__),'img','result.json')

def extract_image(buffer:BytesIO, img_path:IO) -> None:
    """ Places image in binary format in the buffer """
    img = Image.open(img_path)
    img = img.reduce(3)
    img.save(buffer, format='jpeg',optimize=True, quality=75)


def get_buffer_content(buffer:BytesIO, file_path:str=None) -> bytes:
    """ Get the content of buffer. Dumps content in file_path is given """
    
    data = b64encode(buffer.getvalue())
    
    if(file_path is not None):
        try:
            with open(file_path,'wb') as f:
                f.write(data)
                
        except Exception as e:
            print(f"{e.__class__.__module__}.{e.__class__.__name__} : {e}") 
        
    return data


def dump_json(data:dict[str,], file_path:os.PathLike) -> None:
    """ Dumps serialized data into json """
    try:    
        with open(file_path,'w') as f:
            json.dump(data,f)
            
    except Exception as e:
        print(f"{e.__class__.__module__}.{e.__class__.__name__} : {e}") 
    
def get_json(file_path:os.PathLike) -> dict[str,] | None:
    """ Load json data """
    value = None
    with open(file_path,'r') as f:
        value = json.load(f)
    return value


def get_image(img_byte:str, image_store:str | bytes, size: tuple[int,int]) -> None:
    """ Recreate image from byte of given size """
    image = Image.open(BytesIO(b64decode(img_byte)))
    image = image.resize(size,resample=Image.Resampling.BICUBIC)
    
    image.save(image_store)
    

# Sample use

data_byte = BytesIO()

# Get byte data into buffer
extract_image(data_byte, IMAGE)

# Printing buffer content
print(f'Buffer content {str(get_buffer_content(data_byte,IMAGE_CONTENT))}')

# JSON Dump
values = {'image':{'data':get_buffer_content(data_byte).decode(),'size':(780,438)}}
dump_json(values,JSON_PATH)

# Retrieve JSON
json_data = get_json(JSON_PATH)
print(json_data)

# Generating image
data, size = json_data['image'].values()
print(data)
get_image(data,GENERATED,size)