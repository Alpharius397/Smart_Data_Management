from django.shortcuts import render, redirect
from Login.forms import LoginForm
from django.http import HttpRequest, HttpResponse 
from Login.forms import LoginForm
from django.urls import reverse
from django.contrib.auth import models, login, logout, authenticate
from django.conf import settings

# Create your views here.
def logout_view(req:HttpRequest) -> HttpResponse:
    
    if(not req.user.is_authenticated):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    logout(req)
    return redirect(reverse(settings.LOGIN_URL) + '?alert=Logout Successfully')

