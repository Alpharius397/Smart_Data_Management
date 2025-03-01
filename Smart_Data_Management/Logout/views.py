from django.urls import reverse
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import logout
from tools.url_auth import auth_needed
from django.http import HttpRequest, HttpResponse
from django.contrib.messages import error, info

# Create your views here.
def logout_view(req:HttpRequest) -> HttpResponse:

    logout(req)
    return redirect(reverse(settings.LOGIN_URL) + '?success=Logout Successfully')

