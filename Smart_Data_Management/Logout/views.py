from django.urls import reverse
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import logout
from tools.url_auth import auth_needed
from django.http import HttpRequest, HttpResponse 

# Create your views here.
def logout_view(req:HttpRequest) -> HttpResponse:
    
    if(not req.user.is_authenticated):
        return auth_needed(req)
    
    logout(req)
    return redirect(reverse(settings.LOGIN_URL) + '?alert=Logout Successfully')

