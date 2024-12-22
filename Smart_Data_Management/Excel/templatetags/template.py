from django import template

register = template.Library()

@register.filter(name='getID')
def get_id(obj, attr):
    return obj.get(attr,None)

@register.filter(name='all')
def all_check(obj:list,attr:str):
    return obj if all(i['user'] for i in obj) else []