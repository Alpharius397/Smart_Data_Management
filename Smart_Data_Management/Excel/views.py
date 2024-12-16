from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Register.forms import RegisterForm
from django.contrib.auth import models
from Main.tools import *
from django.urls import reverse
from django.conf import settings


# Create your views here.
def upload_screen(req:HttpRequest):
    if(not req.user.is_authenticated):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unautheticated Request')
