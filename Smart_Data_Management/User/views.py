from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from Upload.forms import ExcelForm
from Main.models import MongoConnection, MongoTemplate
from Logs.loggers import APP_LOG, LogStructure, DEFAULT_ERROR, Task
from User.models import is_admin, is_authenticated
import json

from bson.objectid import ObjectId
from tools.get_image import image_load
from tools.url_auth import is_auth_get, is_hx_get, is_hx_post, auth_needed, is_auth_post
from User.models import get_post_id
from django.contrib.auth.models import User
from django.contrib import messages

def account_view(req: HttpRequest) -> HttpResponse:
    if(not (is_authenticated(req.user))):
        return auth_needed(req)
    
    if(is_auth_get(req)):
        return render(req, "User/index.html")
    
    return HttpResponse(status=403)
    
def change_username(req: HttpRequest) -> HttpResponse:
    
    if(is_auth_get(req) and is_hx_get(req)):
        return render(req, "User/HTMX/username/username.change.html")
    
    if(is_auth_post(req) and is_hx_post(req)):
        user = req.POST.get("user", None)
        user_id = req.user.id
        previous_name = req.user.username
        context = {'user':previous_name}
        
        try:
            userObject = User.objects.get(id=user_id)
            userObject.username = user
            
            if(User.objects.filter(username=user).exists()):
                context['error'] = "Username already exists! Try Another"
                return render(req,'User/HTMX/username/username.html', context=context)
            
            userObject.save()
            context['user'] = user
            context['msg'] = f"Username changed from {previous_name} to {user}"
        except Exception as e:
            context['error'] = DEFAULT_ERROR
            
        return render(req,'User/HTMX/username/username.html', context=context)
    
    return HttpResponse(status=403)
    
    
def change_email(req: HttpRequest) -> HttpResponse:
    
    if(is_auth_get(req) and is_hx_get(req)):
        return render(req, "User/HTMX/email/email.change.html")
    
    if(is_auth_post(req) and is_hx_post(req)):
        email = req.POST.get("user", None)
        user_id = req.user.id
        previous_email = req.user.email
        context = {'user':previous_email}
        
        try:
            userObject = User.objects.get(id=user_id)
            userObject.email = email
            
            if(User.objects.filter(email=email).exists()):
                context['error'] = "Email already exists! Try Another"
                return render(req,'User/HTMX/email/email.html', context=context)
            
            userObject.save()
            context['user'] = email
            context['msg'] = f"Username changed from {previous_email} to {email}"
        except Exception as e:
            context['error'] = DEFAULT_ERROR
            
        return render(req,'User/HTMX/email/email.html', context=context)
    
    return HttpResponse(status=403)