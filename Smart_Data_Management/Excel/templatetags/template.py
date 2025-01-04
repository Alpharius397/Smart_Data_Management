from django import template
from Excel.templatetags.bad_image import bad_image

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
def image(obj) -> str:
    raw_img = obj.split(':')
    
    default_height = 100
    
    if(len(raw_img)==3):
        width, height, img = raw_img

        width = int((int(width)/int(height))*default_height)
        height = default_height
    else:
        width, height = 100,100
        img = bad_image
        
    return f"img src=data:image/jpeg;base64,{img} width={width} height={height}"
        

@register.filter(name='in')
def in_check(obj,vector):
    return bool(obj in vector)
