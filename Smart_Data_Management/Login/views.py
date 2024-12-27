from django.shortcuts import render, redirect
from Login.forms import LoginForm
from django.http import HttpRequest, HttpResponse 
from Login.forms import LoginForm
from django.urls import reverse
from django.contrib.auth import models, login, logout, authenticate
from Main.views import is_manager, is_uploader

# Create your views here.
def login_view(req:HttpRequest) -> HttpResponse:
    
    if(req.method=="GET"):
        return render(req,'Login/index.html',{'form':LoginForm})
    
    elif(req.method=="POST"):
        f = LoginForm(req.POST)
        
        if(f.is_valid()):
            
            username = f.cleaned_data.get("username")
            level = f.cleaned_data.get("level")
            password = f.cleaned_data.get("password")
            
            user = authenticate(req,username=username,password=password)
            
            if(user is not None):
                
                if((level=='Uploader' and is_uploader(user)) or (level=='Manager' and is_manager(user))):                
                    login(req,user)
                    return redirect(reverse('Excel:dash') + '?alert=Login Successful')            

            return render(req,'Login/index.html',{'form':f,'alert':'Incorrect Credentials'})
        
        return render(req,'Login/index.html',{'form':f,'alert':'Login Failed'})

