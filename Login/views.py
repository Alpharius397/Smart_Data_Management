from django.shortcuts import render  # type: ignore
from Login.forms import LoginForm  # type: ignore
from django.http import HttpRequest, HttpResponse  # type: ignore
from Login.forms import LoginForm
from django.urls import reverse  # type: ignore
from django.contrib.auth import login, authenticate  # type: ignore
from User.models import is_manager, is_admin
from tools.url_auth import is_hx_post, htmx_response
from constants import SUCCESS, WARNING, DEFAULT_ERROR
from tools.utils import setSwalAlert


def login_view(req: HttpRequest) -> HttpResponse:
    if req.method == "GET":
        success = req.GET.get(SUCCESS, "")
        warning = req.GET.get(WARNING, "")
        
        context: dict[str, LoginForm | str] = {"form": LoginForm()}
        
        if warning :
            setSwalAlert(context, warning, title="Authentication Process")
        
        elif success:
            setSwalAlert(context, success, "success", title="Authentication Process")
            
        print(context)

        return render(req, "Login/HTML/index.html", context)
    
    return HttpResponse(status=403)

@htmx_response
def htmx_login_view(req: HttpRequest):
    context = {"error": False, **setSwalAlert(title="Login Process")}
    
    if is_hx_post(req):
        try:
            
            f = LoginForm(req.POST)

            if f.is_valid():
                username = f.cleaned_data.get("username")
                password = f.cleaned_data.get("password")

                user = authenticate(req, username=username, password=password)

                if (user is not None) and (is_manager(user) or is_admin(user)):
                    login(req, user)
                    context["redirect"] = (
                        next if ((next := req.GET.get("next")) and (next != req.build_absolute_uri() )) else reverse("Dash:index")
                    )
                    setSwalAlert(context, "Login was successful!\nRedirecting to Dashboard", "success")
                else:
                    setSwalAlert(context, "Incorrect Credentials")
                    

            else:
                setSwalAlert(context, f.getErrors())                
                
        except Exception:
            setSwalAlert(context, DEFAULT_ERROR)                
            

        return render(req, "Login/HTMX/messages.html", context=context)
