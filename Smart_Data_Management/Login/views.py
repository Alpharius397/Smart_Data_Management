from django.shortcuts import render, redirect
from Login.forms import LoginForm
from django.http import HttpRequest, HttpResponse 
from Login.forms import LoginForm
from django.urls import reverse
from django.contrib.auth import models, login, logout, authenticate

# Create your views here.
def login_view(req:HttpRequest) -> HttpResponse:
    
    if(req.method=="GET"):
        return render(req,'Login/index.html',{'form':LoginForm})
    
    elif(req.method=="POST"):
        f = LoginForm(req.POST)
                
        if(f.is_valid()):
            user = authenticate(req,username=f.cleaned_data.get("username",None),password=f.cleaned_data.get("password",None))
            
            if(user is not None):
                login(req,user)
                return redirect(reverse('') + '?alert=Login Successful')
            else:
                return render(req,'Login/index.html',{'form':f,'alert':'Incorrect Credentials'})
        
        return render(req,'Login/index.html',{'form':f,'alert':'Login Failed'})

