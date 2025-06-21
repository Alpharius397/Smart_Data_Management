from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from Register.errors import InvalidLevel, UserExists
from Register.forms import RegisterForm
from django.contrib.auth.models import Group
from tools.url_auth import htmx_response, is_hx_post, is_hx_get
from User.models import User, Role, RoleType
from University.models import Institute, Branch
from constants.constants import DEFAULT_ERROR, WARNING
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.db import transaction

from tools.utils import setSwalAlert

def register_view(req:HttpRequest):
    
    if(req.method=="GET"):
        return render(req,'Register/HTML/index.html',{'form':RegisterForm()})
    
    return None

@htmx_response
def htmx_register_view(req: HttpRequest):
    if is_hx_post(req) :
        f = RegisterForm(req.POST)
        context = {"error": False, "redirect":reverse("Login:index"), **setSwalAlert()}

        try:
            with transaction.atomic():
                if f.is_valid():
                    user = f.cleaned_data.get("username", "")
                    email = f.cleaned_data.get("email", "")
                    password = f.cleaned_data.get("password", "")
                    level = f.cleaned_data.get("level", "")
                    branch = f.cleaned_data.get("branch", "")
                    
                    exists = User.objects.filter(Q(username=user)|Q(email=email)).exists()

                    if(exists): raise UserExists()
                    
                    branchID = Branch.objects.filter(id=branch)
                    
                    if not branchID.exists(): raise Branch.DoesNotExist

                    user = User.objects.create_user(user,email,password,is_active=False)
                    role = Role(user=user, belongs=branchID.first(), role=level)
                    
                    if(level==RoleType.ADMIN):
                        group = Group.objects.get(name='Admin')
                        user.groups.add(group)
                        
                    role.save()
                    setSwalAlert(context, "Registration was successful", 'success', "Registration Success")
                else:
                    setSwalAlert(context, f.getErrors(), 'warning', "Registration Failed")
                    
        except UserExists as f:
            setSwalAlert(context, f.get_error(), 'warning', "Registration Failed")
        
        except Branch.DoesNotExist as g:
            setSwalAlert(context, f"Specified Branch does not exists", 'error', "Registration Failed")
        
        except Group.DoesNotExist as g:
            setSwalAlert(context, f"Specified Group (Admin) does not exists", 'error', "Registration Failed")
        
        except Exception as e:
            print(e)
            setSwalAlert(context, DEFAULT_ERROR, 'error', "Registration Failed")
            
        return render(req,'Register/HTMX/message.html',context=context)

@htmx_response
def insti_change(req: HttpRequest):
    
    if(is_hx_get(req)):
        uni = req.GET.get("university",'')
        insti = []
        
        try:            
            if(uni): insti = list(Institute.objects.filter(university__id=uni))
            else: insti = list(Institute.objects.none())
        except:
            pass
        
        return render(req,'Register/HTMX/option.html',{'option':insti})
    
    

@htmx_response
def branch_change(req: HttpRequest):

    if(is_hx_get(req)):
        insti = req.GET.get("institute",'')
        branch = []
        
        try:
            if(insti): branch = list(Branch.objects.filter(institute__id=insti))
            else:branch = list(Branch.objects.none())
        except:
            pass
        
        return render(req,'Register/HTMX/option.html',{'option':branch})

