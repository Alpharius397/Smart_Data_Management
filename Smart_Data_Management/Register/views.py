from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from Register.forms import RegisterForm
from django.contrib.auth import models
from Main.tools import *

# Create your views here.
def register_view(req:HttpRequest) -> HttpResponse:
    
    if(req.method=="GET"):
        return render(req,'Register/index.html',{'form':RegisterForm})
    
    elif(req.method=="POST"):
        f = RegisterForm(req.POST)
                
        if(f.is_valid()):
            user, email, passwrd = get_var(f,"username"), get_var(f,"email"), get_var(f,"password")
            
            exists = models.User.objects.filter(username=user).exists()
            
            if(exists):
                return render(req,'Register/index.html',{'form':f,'alert':'User Exists'})
            
            user = models.User.objects.create_user(user,email,passwrd)
            user.save()
            
            return render(req,'Register/index.html',{'form':f,'alert':'Register Confirmed'})
        
        return render(req,'Register/index.html',{'form':f,'alert':'Register Failed'})
