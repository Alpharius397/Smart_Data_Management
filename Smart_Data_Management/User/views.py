from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from Logs.loggers import DEFAULT_ERROR
from User.models import is_authenticated
from django.db.models.expressions import Q
from tools.url_auth import is_auth_get, is_hx_get, is_hx_post, auth_needed, is_auth_post, is_auth_put, is_hx_put, jwt_required, noneCheck
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.hashers import check_password

def account_view(req: HttpRequest) -> HttpResponse:
    if(not (is_authenticated(req.user))):
        return auth_needed(req)
    
    if(is_auth_get(req)):
        return render(req, "User/index.html")
    
    return HttpResponse(status=403)
    
def change_username(req: HttpRequest) -> HttpResponse:
    
    if(is_auth_put(req) and is_hx_put(req)):
        return render(req,'User/HTMX/username/username.html', context={"user":req.user.username})
    
    if(is_auth_get(req) and is_hx_get(req)):
        return render(req, "User/HTMX/username/username.change.html")
    
    if(is_auth_post(req) and is_hx_post(req)):
        user = req.POST.get("user", None)
        user_id = req.user.id
        previous_name = req.user.username
        context = {'user':previous_name}
        
        try:
            userObject = User.objects.get(id=user_id)
            
            if(User.objects.filter(username=user).exists()):
                context['error'] = "Username already exists! Try Another"
                return render(req,'User/HTMX/username/username.html', context=context)
            
            userObject.username = user
            userObject.save()
            context['user'] = user
            context['msg'] = f"Username changed from {previous_name} to {user}"
            
        except Exception as e:
            context['error'] = DEFAULT_ERROR
            
        return render(req,'User/HTMX/username/username.html', context=context)
    
    return HttpResponse(status=403)
    
def change_email(req: HttpRequest) -> HttpResponse:
    
    if(is_auth_put(req) and is_hx_put(req)):
        return render(req,'User/HTMX/email/email.html',context={"email":req.user.email})
    
    if(is_auth_get(req) and is_hx_get(req)):
        return render(req, "User/HTMX/email/email.change.html")
    
    if(is_auth_post(req) and is_hx_post(req)):
        email = req.POST.get("user", None)
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

def change_pass(req: HttpRequest) -> HttpResponse:

    if(is_auth_put(req) and is_hx_put(req)):
        return render(req,'User/HTMX/password/password.html')
    
    if(is_auth_get(req) and is_hx_get(req)):
        return render(req, "User/HTMX/password/password.change.html")
    
    if(is_auth_post(req) and is_hx_post(req)):

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
    
    return HttpResponse(status=403)
