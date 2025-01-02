import string
import openpyxl
from PIL import Image
import openpyxl.worksheet
import openpyxl.worksheet.worksheet
from typing import Any
from base64 import b64encode, b64decode
from io import BytesIO

def get_image_data(sheet:openpyxl.worksheet.worksheet.Worksheet) -> dict[tuple[int,int],Any]:
    images = {}
    for image in sheet._images:        
        img = Image.open(BytesIO(image._data()))
        
        with BytesIO() as b:
            img.save(b,format='jpeg',quality=70)
            images[(image.anchor._from.row,image.anchor._from.col)] = b64encode(b.getvalue()).decode()
        
    return images


