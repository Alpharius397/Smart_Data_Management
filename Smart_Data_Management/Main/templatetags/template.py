import re
from django import template
from Main.templatetags.bad_image import bad_image
from typing import NamedTuple
from datetime import datetime

class Image(NamedTuple):
    img:str
    width:int
    height:int
    
register = template.Library()

@register.filter(name='getID')
def get_id(obj, attr):
    return obj.get(attr,None)

@register.filter(name='all')
def all_check(obj:list,attr:str):
    return obj if all(i[attr] for i in obj) else []

@register.filter(name='str')
def str_convert(obj):
    return str(obj)

@register.filter(name='addOne')
def addOne(obj:int | float):
    return int(obj)+1

@register.filter(name='check')
def check(obj) -> bool: 
    return obj is not None

@register.filter(name='enum')
def enum(obj) -> tuple[list[int], list]:
    return enumerate(obj)

@register.filter(name='img')
def image(obj) -> Image:
    raw_img = obj.split(':')
    
    default_height = 150
    
    try:
        width, height, img = raw_img

        width = int((int(width)/int(height))*default_height)
        height = default_height
    except:
        width, height = 150,150
        img = bad_image
        
    return Image(f"data:image/jpeg;base64,{img}",width,height)
        

@register.filter(name='in')
def in_check(obj,vector):
    return bool(obj in vector)

@register.filter(name='index')
def index(vector,index):
    return vector[int(index)] if (index is not None) else None

@register.filter(name='index_str')
def index(vector,index):
    return vector.get(str(index),None)

@register.filter(name='full_img')
def full_image(obj):
    raw_img = obj.split(':')
    
    try:
        width, height, img = raw_img
    except:
        width, height = 100,100
        img = bad_image
        
    return Image(f"data:image/jpeg;base64,{img}",width,height)

@register.filter(name='get_last')
def last_path(obj):
    path = obj.split('/')
    
    return '/'.join(path[:-2])

@register.filter(name='clean')
def clean_text(obj):
    sem_data = r'(.+)Sem_\d+$'
    
    sem:list[str] = re.findall(sem_data,obj)
    
    if(sem):
        sem = sem[0]
        return sem.strip().strip('_')
    
    return None

@register.filter(name='timestamp')
def timestamp(obj):
    try:
        return datetime.fromisoformat(obj).strftime("%d/%m/%Y, %H:%M:%S")
    except:
        return "Incorrect Time Format"