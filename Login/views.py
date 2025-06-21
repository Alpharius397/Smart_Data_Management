from django.shortcuts import render  # type: ignore
from Login.forms import LoginForm  # type: ignore
from django.http import HttpRequest, HttpResponse  # type: ignore
from Login.forms import LoginForm
from django.urls import reverse  # type: ignore
from django.contrib.auth import login, authenticate  # type: ignore
from User.models import is_manager, is_admin
from django.contrib import messages  # type: ignore
from tools.url_auth import is_hx_post, htmx_response
from constants.constants import DEFAULT_ERROR, ERROR, SUCCESS, WARNING
from tools.utils import setSwalAlert


def login_view(req: HttpRequest) -> HttpResponse:
    if req.method == "GET":
        success = req.GET.get(SUCCESS, "")
        warning = req.GET.get(WARNING, "")
        
        context: dict[str, LoginForm | str] = {"form": LoginForm()}
        
        if warning :
            context.update({"message": warning, "icon": WARNING, "title": "Warning"})
        
        elif success:
            context.update({"message": success, "icon": SUCCESS, "title": "Successful Action"})

        return render(req, "Login/HTML/index.html", context)
    
    return HttpResponse(status=403)

@htmx_response
def htmx_login_view(req: HttpRequest) -> HttpResponse:
    context = {"error": False, "redirect":req.build_absolute_uri(), **setSwalAlert()}
    
    if is_hx_post(req):
        try:
            context["redirect"] = (
                next if ((next := req.GET.get("next")) and (next != req.build_absolute_uri() )) else reverse("Dash:index")
            )
            f = LoginForm(req.POST)

            if f.is_valid():
                username = f.cleaned_data.get("username")
                password = f.cleaned_data.get("password")

                user = authenticate(req, username=username, password=password)

                if (user is not None) and (is_manager(user) or is_admin(user)):
                    login(req, user)
                    setSwalAlert(context, "Login was successful!\nRedirecting to Dashboard", "success", "Login Success")
                else:
                    setSwalAlert(context, "Incorrect Credentials", "warning", "Login Failed")
                    context["error"] = True
                    

            else:
                setSwalAlert(context, f.getErrors(), "warning", "Login Failed")                
                context["error"] = True
                
        except Exception:
            context["error"] = True

        return render(req, "Login/HTMX/messages.html", context=context)
    
    return None
