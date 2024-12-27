from django.shortcuts import render
from django.contrib.auth.models import User
from Main.models import Manager, Uploader
# Create your views here.

def is_manager(user:User) -> bool:
    try:
        manager = user.manager
        return True
    except:
        return False

def is_uploader(user:User) -> bool:
    try:
        uploader = user.uploader
        return True
    except:
        return False