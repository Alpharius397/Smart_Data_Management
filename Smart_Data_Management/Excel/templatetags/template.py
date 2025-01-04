from django import template

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
    print(obj)
    return enumerate(obj)
