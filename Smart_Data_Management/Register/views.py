from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from Register.forms import RegisterForm
from django.contrib.auth import models
from Main.tools import *
from User.models import Manager, Uploader
from University.models import University, Institute, Branch

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

def insti_change(req: HttpRequest) -> HttpResponse:
    
    if(req.method=='GET' and req.META.get('HTTP_HX_REQUEST')):
        uni = req.GET.get("university",'')
        
        if(uni):
            insti = list(Institute.objects.filter(university__id=uni))
        else:
            insti = list(Institute.objects.none())
            
        return render(req,'HTMX/option.html',{'option':insti})


def branch_change(req: HttpRequest) -> HttpResponse:

    if(req.method=='GET' and req.META.get('HTTP_HX_REQUEST')):
        insti = req.GET.get("institute",'')
        
        if(insti):
            branch = list(Branch.objects.filter(institute__id=insti))
        else:
            branch = list(Branch.objects.none())
            
        return render(req,'HTMX/option.html',{'option':branch})
