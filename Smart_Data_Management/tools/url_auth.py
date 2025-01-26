from django.http import HttpRequest
from User.models import is_authenticated

def is_hx_get(req:HttpRequest) -> bool:
    return bool((req.method=="GET") and req.META.get('HTTP_HX_REQUEST'))

def is_hx_post(req:HttpRequest) -> bool:
    return bool((req.method=="POST") and req.META.get('HTTP_HX_REQUEST'))

def is_auth_get(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method=='GET')

def is_auth_post(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method=='POST')