from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Excel.forms import ExcelForm
from django.contrib.auth import models
from Main.tools import *
from Excel.models import VerificationTable
from django.urls import reverse
from django.conf import settings
import pymongo
import pandas as pd
from io import BytesIO
from typing import Any
import json
from bson.objectid import ObjectId

class MongoTemplate:
        
    def __init__(self, file_name:str ,data:dict[str,Any], belongs:str) -> None:
        
        self.excel = {'data':data,'name':file_name}
        self.belongs = belongs
        self.verify = []

    def get_json(self):
        
        to_get = ['excel','belongs','verify']
        
        return {i:self.__getattribute__(i) for i in to_get}
        


# Create your views here.
def upload_screen(req:HttpRequest):
    if(not req.user.is_authenticated):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    connect = pymongo.MongoClient(settings.MONGO_URL)
    
    excel = connect["smart"]["excel"]
    
    
    if(req.method=="POST"):
        f = ExcelForm(req.POST,req.FILES)
        
        if(f.is_valid()):
            excel_file = req.FILES["file"]
        
            pd_data = None
            with excel_file.open() as file:
                pd_data = json.loads(pd.read_excel(BytesIO(file.read())).to_json())
        
        
            if(pd_data is None):
                return render(req,'Excel/index.html',{'form':f,'alert':'Excel Extraction Failed'})
                
            file_name = req.POST.get("file_name")
            template = MongoTemplate(file_name,pd_data,user).get_json()
            
            res = excel.insert_one(template)
            
            verify = VerificationTable(mongo_id=res.inserted_id,belongs=req.user)
            verify.save()
            
            
            return render(req,'Excel/index.html',{'form':f,'alert':'Excel Extraction Success'})
        
        return render(req,'Excel/index.html',{'form':f,'alert':'Something Went Wrong'})
        
    else:
        f = ExcelForm(initial={'username':req.user.username})
    
    return render(req,'Excel/index.html',{'form':f})

def dash_board(req: HttpRequest) -> HttpResponse:
    if(not req.user.is_authenticated):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    connect = pymongo.MongoClient(settings.MONGO_URL)
    
    excel = connect["smart"]["excel"]
    
    
    upload = excel.find({"belongs":{"$eq":user}}).to_list()
    verify = excel.find({"verify.user":{"$eq":user}}).to_list()
    
    
    
    return render(req,'Excel/dash.html',{'upload':upload,'verify':verify})


def view_screen(req: HttpRequest,id) -> HttpResponse:
    if(not req.user.is_authenticated):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    connect = pymongo.MongoClient(settings.MONGO_URL)
    
    excel = connect["smart"]["excel"]
    
    result = excel.find_one({"$and":[{"_id":ObjectId(id)},{"$or":[{"belongs":{"$eq":user}},{"verify.user":{"$eq":user}}]}]})

    if(result is None):
        return redirect(reverse('Excel:dash')+'?alert=Record not found')
    
    
    pd_data = pd.read_json(json.dumps(result['excel']['data']))
    
    return render(req,'Excel/view.html',{'column':pd_data.columns,'result':pd_data.iterrows()})