from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from Register.forms import RegisterForm
from django.contrib.auth.models import User, Group
from tools.url_auth import is_hx_post, is_hx_get
from User.models import Manager, Admin
from University.models import Institute, Branch
from Logs.loggers import DEFAULT_ERROR
from django.db.models import Q

# Create your views here.
def register_view(req:HttpRequest) -> HttpResponse:
    
    if(req.method=="GET"):
        return render(req,'Register/index.html',{'form':RegisterForm})
    
    elif(is_hx_post(req)):
        f = RegisterForm(req.POST)
        context = {}
                
        if(f.is_valid()):
            user, email, passwrd, level = f.cleaned_data.get("username"), f.cleaned_data.get("email"), f.cleaned_data.get("password"), f.cleaned_data.get("level")
            branch = f.cleaned_data.get("branch")
            
            try:
                exists = User.objects.filter(Q(username=user)|Q(email=email)).exists()

                if(exists):
                    context['error'] = "Username/Email already exists"
                    return render(req,'HTMX/message.html',context=context)
                    
            except Exception as e:
                context['error'] = DEFAULT_ERROR
                return render(req,'HTMX/message.html',context=context)
            
            _branch = None
            
            try:
                _branch = Branch.objects.get(id=branch)
            except Exception as e:
                context['error'] = "Branch not found"
                return render(req,'HTMX/message.html',context=context)
                
            try:
                group = Group.objects.get(name='Admin')
                user = User.objects.create_user(user,email,passwrd)
                user.is_active = False
                user.save()
                
                if(level=='Manager'):
                    manager = Manager(user=user)
                    manager.belongs = _branch
                    manager.save()
                    
                elif(level=='Admin'):
                    admin = Admin(user=user)
                    admin.belongs = _branch
                    admin.user.groups.add(group)
                    admin.save()
                else:
                    context['error'] = "Level not found"
                context['msg'] = "Registered Successfully"
                
            except Exception as e:
                context['error'] = DEFAULT_ERROR
            
            return render(req,'HTMX/message.html',context=context)
            
        else:
            
            context['error'] = f.errors.as_text()
            
            return render(req,'HTMX/message.html',context=context)
                

def insti_change(req: HttpRequest) -> HttpResponse:
    
    if(is_hx_get(req)):
        uni = req.GET.get("university",'')
        
        if(uni):
            insti = list(Institute.objects.filter(university__id=uni))
        else:
            insti = list(Institute.objects.none())
            
        return render(req,'HTMX/option.html',{'option':insti})
    
    return HttpResponse(status=403)
    


def branch_change(req: HttpRequest) -> HttpResponse:

    if(is_hx_get(req)):
        insti = req.GET.get("institute",'')
        
        if(insti):
            branch = list(Branch.objects.filter(institute__id=insti))
        else:
            branch = list(Branch.objects.none())
            
        return render(req,'HTMX/option.html',{'option':branch})

    return HttpResponse(status=403)
