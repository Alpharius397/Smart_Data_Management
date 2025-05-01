from django.shortcuts import render, redirect
from Login.forms import LoginForm
from django.http import HttpRequest, HttpResponse
from Login.forms import LoginForm
from django.urls import reverse
from django.contrib.auth import login, authenticate
from User.models import is_manager, is_admin
from django.contrib import messages
from tools.url_auth import is_hx_post
from Logs.loggers import DEFAULT_ERROR

def login_view(req:HttpRequest) -> HttpResponse:
    
    if(req.method=="GET"):
        return render(req,'Login/index.html',{'form':LoginForm})
    
    elif(is_hx_post(req)):
        
        try:
            next_url = req.GET.get('next') if req.GET.get('next') else reverse('Dash:dash')
            f = LoginForm(req.POST)
            
            if(f.is_valid()):
                
                username = f.cleaned_data.get("username")
                password = f.cleaned_data.get("password")
                
                user = authenticate(req,username=username,password=password)
                
                if((user is not None) and (is_manager(user) or is_admin(user))):            
                    login(req,user)
                    return render(req,'Login/HTMX/messages.html',{'redirect':next_url})
                
                messages.error(req, 'Incorrect Credentials')
                return render(req,'Login/HTMX/messages.html')
            
            else:
                messages.error(req, 'Login Failed')
                return render(req,'Login/HTMX/messages.html')
        except:
            messages.error(req, DEFAULT_ERROR)
    
    return HttpResponse(status=403)