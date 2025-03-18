from django.http import HttpRequest, HttpResponse
from User.models import is_authenticated
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from User.models import Admin, Manager
from University.models import Color
from django.contrib.auth.models import User

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

def get_admin_color(req: HttpRequest, user: User):
    try:
        admin:Admin = user.admin
        color:Color = admin.belongs.institute.color
        main_color = color.main_color
        sec_color = color.sec_color
        req.session['mainColor'] = main_color
        req.session['secColor'] = sec_color
    except:
        pass
    

def get_manager_color(req: HttpRequest, user: User):
    try:
        admin:Manager = user.manager
        color:Color = admin.belongs.institute.color
        main_color = color.main_color
        sec_color = color.sec_color
        req.session['mainColor'] = main_color
        req.session['secColor'] = sec_color
    except:
        pass
