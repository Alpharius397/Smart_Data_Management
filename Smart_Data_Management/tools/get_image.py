import string
import openpyxl
from PIL import Image
import openpyxl.worksheet
import openpyxl.worksheet.worksheet
from typing import Any
from base64 import b64encode, b64decode
from io import BytesIO

REDUCE_FACTOR:int = 3

def get_image_data(sheet:openpyxl.worksheet.worksheet.Worksheet) -> dict[tuple[int,int],Any]:
    images = {}
    for image in sheet._images:        
        img = Image.open(BytesIO(image._data()))
        
        with BytesIO() as b:
            img.save(b,format='jpeg',quality=95)
            images[(image.anchor._from.row,image.anchor._from.col)] = f"{img.width}:{img.height}:{b64encode(b.getvalue()).decode()}"
        
    return images

def compress_image(img_data:BytesIO):
    image = Image.open(img_data)
    width, height = image.width, image.height
    compressed = image.reduce(REDUCE_FACTOR)
    
    image_data = BytesIO()
    
    compressed.save(image_data,format='jpeg',quality=85)
    
    return f"{width}:{height}:{b64encode(image_data.getvalue()).decode()}"


