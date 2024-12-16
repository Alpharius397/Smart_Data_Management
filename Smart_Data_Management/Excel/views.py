from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Excel.forms import ExcelForm
from django.contrib.auth import models
from Main.tools import *
from django.urls import reverse
from django.conf import settings
import pymongo

MONGO_URL = "mongodb://127.0.0.1:27017/"

# Create your views here.
def upload_screen(req:HttpRequest):
    if(not req.user.is_authenticated):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    connect = pymongo.MongoClient(MONGO_URL)
    
    excel = connect["smart"]["excel"]
    
    print(excel.find({"bye":{"$exists":False}}).to_list())
    
    
    if(req.method=="POST"):
        f = ExcelForm(req.POST,req.FILES)
    else:
        f = ExcelForm
    
    return render(req,'Excel/index.html',{'form':f})
