from django.urls import reverse
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse

# Create your views here.
def logout_view(req:HttpRequest) -> HttpResponse:

    logout(req)
    return redirect(reverse(settings.LOGIN_URL) + '?success=Logout Successfully')

