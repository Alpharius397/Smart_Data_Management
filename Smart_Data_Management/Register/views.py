from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from Register.forms import RegisterForm
from django.contrib.auth import models
from Main.tools import *
from Main.models import Manager, Uploader

# Create your views here.
def register_view(req:HttpRequest) -> HttpResponse:
    
    if(req.method=="GET"):
        return render(req,'Register/index.html',{'form':RegisterForm})
    
    elif(req.method=="POST"):
        f = RegisterForm(req.POST)
                
        if(f.is_valid()):
            user, email, passwrd, level = f.cleaned_data.get("username"), f.cleaned_data.get("email"), f.cleaned_data.get("password"), f.cleaned_data.get("level")
            
            exists = models.User.objects.filter(username=user).exists()
            
            if(exists):
                return render(req,'Register/index.html',{'form':f,'alert':'User Exists'})
            
            user = models.User.objects.create_user(user,email,passwrd)
            user.save()
            
            if(level=='Manager'):
                manager = Manager(user=user)
                manager.save()
                
            elif(level=='Uploader'):
                uploader = Uploader(user=user)
                uploader.save()
            else:
                return render(req,'Register/index.html',{'form':f,'alert':'Level not found'})
                                
            
            return render(req,'Register/index.html',{'form':f,'alert':'Register Confirmed'})
        
        return render(req,'Register/index.html',{'form':f,'alert':'Register Failed'})
