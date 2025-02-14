from django.http import HttpRequest, HttpResponse
from User.models import is_authenticated
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse



def is_hx_get(req:HttpRequest) -> bool:
    return bool((req.method=="GET") and req.META.get('HTTP_HX_REQUEST'))

def is_hx_post(req:HttpRequest) -> bool:
    return bool((req.method=="POST") and req.META.get('HTTP_HX_REQUEST'))

def is_auth_get(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method=='GET')

def is_auth_post(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method=='POST')

def auth_needed(req:HttpRequest) -> HttpResponse:
    return redirect(reverse(settings.LOGIN_URL) + f"?next={req.path}&alert=Unauthenticated Request!")