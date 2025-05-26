import random
from django.shortcuts import render # type: ignore
from django.http import HttpRequest, HttpResponse # type: ignore
from constants.constants import * # type: ignore
from django.db.models.expressions import Q # type: ignore
from tools.url_auth import is_auth_get, is_hx_get, is_hx_post, auth_needed, login_needed 
from django.contrib.auth.models import User # type: ignore
from django.contrib.auth.hashers import check_password # type: ignore

@login_needed()
def account_view(req: HttpRequest) -> HttpResponse:    
    if(is_auth_get(req)):
        return render(req, "User/index.html")
    
    return HttpResponse(status=403)

@auth_needed()
def get_username(req: HttpRequest):
    if(is_hx_get(req)):
        return render(req, "User/HTMX/username/username.html", context={"username": req.user.id})

@auth_needed()
def change_username(req: HttpRequest) -> HttpResponse:
    
    if(is_hx_get(req)):
        return render(req, "User/HTMX/username/username.change.html", context={"username": req.user.id})
    
    if(is_hx_post(req)):
        username = req.POST.get("username", None)
        user_id = req.user.id
        previous_name = req.user.username
        context = {'username':previous_name}
        
        try:
            userObject = User.objects.get(id=user_id)
            
            if(User.objects.filter(Q(username=username) & ~Q(id=user_id)).exists()):
                context['error'] = "Username already exists! Try Another"
                return render(req,'User/HTMX/username/username.html', context=context)
            
            userObject.username = username
            userObject.save()
            
            context['username'] = username
            context['msg'] = f"Username changed from {previous_name} to {username}"
            
        except Exception as e:
            print(e)
            context['error'] = DEFAULT_ERROR
            
        return render(req,'User/HTMX/username/username.html', context=context)

@auth_needed()
def get_email(req: HttpRequest):
    if(is_hx_get(req)):
        return render(req, "User/HTMX/email/email.html", context={"email": req.user.email})
    
@auth_needed()
def change_email(req: HttpRequest) -> HttpResponse:
    
    if(is_hx_get(req)):
        return render(req,'User/HTMX/email/email.change.html',context={"email":req.user.email})
    
    if(is_hx_post(req)):
        email = req.POST.get("email", None)
        user_id = req.user.id
        previous_email = req.user.email
        context = {'email':previous_email}
        
        try:
            userObject = User.objects.get(id=user_id)

            if(User.objects.filter(Q(email=email) & ~Q(id=user_id)).exists()):

                context['error'] = "Email already exists! Try Another"
                return render(req,'User/HTMX/email/email.html', context=context)
            
            userObject.email = email
            userObject.save()
            context['email'] = email
            context['msg'] = f"Username changed from {previous_email} to {email}"
        
        except Exception as e:
            print(e)
            context['error'] = DEFAULT_ERROR
            
        return render(req,'User/HTMX/email/email.html', context=context)
    
    return HttpResponse(status=403)

@auth_needed()
def get_password(req: HttpRequest):
    if(is_hx_get(req)):
        defaultPassword = '*'*random.randint(8,20)
        return render(req, "User/HTMX/password/password.html", context={"password": defaultPassword})

@auth_needed()
def change_password(req: HttpRequest) -> HttpResponse:

    if(is_hx_get(req)):
        return render(req, "User/HTMX/password/password.change.html")
    
    if(is_hx_post(req)):

        prevPass = req.POST.get("previous",None)
        newPass = req.POST.get("new",None)
        user_id = req.user.id
        context = {}
        
        try:
            userObject = User.objects.get(id=user_id)
            
            if(not check_password(prevPass,userObject.password)):
                context['error'] = "Previous Password doesn't match"
                return render(req,'User/HTMX/password/password.html', context=context)
            
            userObject.set_password(newPass)
            userObject.save()
            context['msg'] = f"Password change successful"
        except Exception as e:
            print(e)
            context['error'] = DEFAULT_ERROR
            
        return render(req,'User/HTMX/password/password.html', context=context)
    




    
