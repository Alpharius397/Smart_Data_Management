from django.shortcuts import render # type: ignore
from django.http import HttpRequest # type: ignore
from Register.errors import UserExists 
from Register.forms import RegisterForm
from django.contrib.auth.models import Group # type: ignore
from tools.url_auth import htmx_response, is_hx_post, is_hx_get
from User.models import User, Role, RoleType
from University.models import Institute, Branch
from constants.constants import DEFAULT_ERROR, WARNING
from django.db.models import Q # type: ignore
from django.urls import reverse # type: ignore
from django.db import transaction # type: ignore
from tools.utils import setSwalAlert

def register_view(req:HttpRequest):
    
    if(req.method=="GET"):
        return render(req,'Register/HTML/index.html',{'form':RegisterForm()})
    
    return None

@htmx_response
def htmx_register_view(req: HttpRequest):
    if is_hx_post(req) :
        f = RegisterForm(req.POST)
        context = setSwalAlert(title="Registration Process")

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
                    context["redirect"] = reverse("Login:index")
                    setSwalAlert(context, "Registration was successful\nRedirecting to Login Page", 'success')
                else:
                    setSwalAlert(context, f.getErrors())
                    
        except UserExists as f:
            setSwalAlert(context, f.get_error())
        
        except Branch.DoesNotExist as g:
            setSwalAlert(context, f"Specified Branch does not exists")
        
        except Group.DoesNotExist as g:
            setSwalAlert(context, f"Specified Group (Admin) does not exists")
        
        except Exception as e:
            setSwalAlert(context, DEFAULT_ERROR)
            
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

