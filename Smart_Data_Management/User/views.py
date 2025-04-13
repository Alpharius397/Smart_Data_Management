import datetime
import json
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse, QueryDict
from Logs.loggers import DEFAULT_ERROR
from User.models import is_student, is_authenticated, Student
from django.db.models.expressions import Q
from tools.url_auth import AccessPayLoad, PayLoad, RefreshPayLoad, is_auth_get, is_hx_get, is_hx_post, auth_needed, is_auth_post, is_auth_put, is_hx_put, noneCheck
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
import jwt
from django.conf import settings
from django.utils import timezone

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

@csrf_exempt
def mobile_login(req: HttpRequest) -> JsonResponse:
    if(req.method=="POST"):
        
        response = {'token':None, 'refresh':None, 'status':False, 'error':None}
        
        try:
            body:dict[str, str] = json.loads(req.body)
            username = req.POST.get('user',body.get('user',None))
            password = req.POST.get('password',body.get('password',None))

            user = User.objects.get(username=username)
            
            if(is_student(user) and user.check_password(password)):

                response['token'] = AccessPayLoad(user).getToken()
                response['refresh'] = RefreshPayLoad(user).getToken()
                response['status'] = True
                return JsonResponse(data=response, safe=False, status=200)
            
            else:
                response['error'] = 'Incorrect Credentials'
                return JsonResponse(data=response, safe=False, status=401)

        except User.DoesNotExist:
            response['error'] = 'Invalid credentials'
            return JsonResponse(data=response, safe=False, status=401)

        except Exception as e:
            response['error'] = DEFAULT_ERROR
            return JsonResponse(data=response, safe=False, status=500)
    
    return JsonResponse(data={'error':DEFAULT_ERROR}, safe=False, status=403)

@csrf_exempt
def mobile_refresh(req: HttpRequest) -> JsonResponse:
    if(req.method=="POST"):
        response = {'token':None, 'status':False, 'error':None}
        
        try:
            body:dict[str, str] = json.loads(req.body)
            
            refreshToken = req.POST.get('refresh',body.get('refresh'))
            payload:RefreshPayLoad = PayLoad.decodeToken(RefreshPayLoad,refreshToken)
            
            if (not payload.isCorrectType()):
                return JsonResponse({'error': 'Invalid refresh token'}, status=401)
            
            user = User.objects.get(id=payload.userID, username=payload.username)
            
            if(is_student(user)):
                
                token = AccessPayLoad(user).getToken()
                response['token'] = token
                response['status'] = True
                
                return JsonResponse(data=response, safe=False, status=200)
            
            else:
                response['error'] = 'Incorrect Credentials'
                return JsonResponse(data=response, safe=False, status=401)

        except User.DoesNotExist:
            response['error'] = 'Invalid credentials'
            return JsonResponse(data=response, safe=False, status=401)

        except Exception as e:
            print(e)
            response['error'] = DEFAULT_ERROR
            return JsonResponse(data=response, safe=False, status=500)
    
    return JsonResponse(data={'error':DEFAULT_ERROR}, safe=False, status=403)

@csrf_exempt
def mobile_register(req: HttpRequest) -> JsonResponse:
    if(req.method == "POST"):
        username = req.POST.get('user', None)
        email = req.POST.get('email', None)
        password = req.POST.get('password_1', None)
        confirm_password = req.POST.get('password_2', None)
        response = {'status': False, 'error': None}

        if(noneCheck(username, email, password, confirm_password)):
            response['error'] = "All fields must not be empty"
            return JsonResponse(data=response, safe=False, status=401)

        try:
            
            if(confirm_password != password):
                response['error'] = "Passwords don't match"

                return JsonResponse(data=response, safe=False, status=401)
            
            userExists = User.objects.filter(Q(username=username)|Q(email=email)).exists()
            
            if(userExists):
                response['error'] = 'User exists with same username or email'
                return JsonResponse(data=response, safe=False, status=422)
                
            user = User.objects.create_user(username, email,password)
            user.save()
            
            Student(user=user).save()

            response['status'] = True
            return JsonResponse(data=response, safe=False, status=200)

        except Exception as e:
            response['error'] = DEFAULT_ERROR
            return JsonResponse(data=response, safe=False, status=500)

    return JsonResponse(data={'error': DEFAULT_ERROR}, safe=False, status=403)
