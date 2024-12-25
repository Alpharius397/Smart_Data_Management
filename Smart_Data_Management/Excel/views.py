from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Excel.forms import ExcelForm,VerifyForm
from django.db.models import Q
from Main.tools import *
from Excel.models import VerificationTable,MongoConnection,VERIFY_COUNT
from django.urls import reverse
from django.conf import settings
import pymongo
import pandas as pd
from io import BytesIO,StringIO
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
        

def mongo_setup_failed(req, **kwargs):
    context = {'alert':'MongoDB connection failed'}
    context.update(kwargs)
    return render(req,'Excel/index.html',context)


# Create your views here.
def upload_screen(req:HttpRequest):
    if(not req.user.is_authenticated):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    connection = MongoConnection(settings.MONGO_URL)
    excel = connection.connect(settings.MONGO_CRED)
    pd_data = None
    
    if(excel is None):
        return render(req,'Excel/index.html',{'form':f,'alert':'MongoDB connection failed'})

    if(req.method=="POST"):
        f = ExcelForm(req.POST,req.FILES)
        
        if(f.is_valid()):
            excel_file = req.FILES["file"]
            file_name = f.cleaned_data.get("file_name")
        
            with excel_file.open() as file:
                pd_data = json.loads(pd.read_excel(BytesIO(file.read())).to_json())
        
            if(pd_data is None):
                return mongo_setup_failed(req,form=f)
                
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
    
    connection = MongoConnection(settings.MONGO_URL)
    excel = connection.connect(settings.MONGO_CRED)
    
    
    upload = excel.find({"belongs":{"$eq":user}}).to_list()
    verify = excel.find({"verify.user":{"$eq":user}}).to_list()
    
    return render(req,'Excel/dash.html',{'upload':upload,'verify':verify})

def owner_view(req: HttpRequest,id) -> HttpResponse:
    if(not req.user.is_authenticated):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    connection = MongoConnection(settings.MONGO_URL)
    excel = connection.connect(settings.MONGO_CRED)
    
    result = excel.find_one({"$and":[{"_id":ObjectId(id)},{"belongs":user}]})

    if(result is None):
        return redirect(reverse('Excel:dash')+'?alert=Record not found')
    
    pd_data = pd.read_json(StringIO(json.dumps(result['excel']['data'])))
    
    column = req.GET.get('column','')
    value = req.GET.get('search','')
    
    if((column) and (column not in pd_data.columns)):
        return render(req,'Excel/owner.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'alert':'Column Not found'})
    
    if(column and (value)):
        sample = pd_data[pd_data[column].astype(str).str.contains(value)]
        
        if(sample.empty):
            return render(req,'Excel/owner.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'alert':'Data was not found!'})
        
        pd_data = sample
            
    
    return render(req,'Excel/owner.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'feed':result['verify']})


def assign_view(req: HttpRequest,id) -> HttpResponse:
    if(not req.user.is_authenticated):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    connection = MongoConnection(settings.MONGO_URL)
    excel = connection.connect(settings.MONGO_CRED)
    
    result = excel.find_one({"$and":[{"_id":ObjectId(id)},{"verify.user":{"$eq":user}}]})

    if(result is None):
        return redirect(reverse('Excel:dash')+'?alert=Record not found')
    
    
    pd_data = pd.read_json(StringIO(json.dumps(result['excel']['data'])))
    
    column = req.GET.get('column','')
    value = req.GET.get('search','')
    
    if((column) and (column not in pd_data.columns)):
        return render(req,'Excel/assign.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'alert':'Column Not found'})
    
    if(column and (value)):
        sample = pd_data[pd_data[column].astype(str).str.contains(value)]
        
        if(sample.empty):
            return render(req,'Excel/assign.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'alert':'Data was not found!'})
        
        pd_data = sample
    
    query = Q(mongo_id=id)
    
    record = VerificationTable.objects.filter(query)[0]
    idx = record.get_user(req.user)
    if(idx is None): return redirect(reverse('Excel:dash')+'?alert=Not authorized for this task')
    
    if(req.method=='POST'):
        f=VerifyForm(req.POST)
        
        if(f.is_valid()):
            status = f.cleaned_data.get("status")
            feedback = f.cleaned_data.get("feedback")
            
            
            if(status=='True'):
                status = True
            elif(status=='False'):
                status = False
            else:
                status = None
            
            record.set_verify(idx,status,feedback)
            
            record.save()
            return render(req,'Excel/assign.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'form':f,'alert':'Task Submission done'})
            
            
    
    else:
        f=VerifyForm(initial={'status':record.get("verify_%s_status" % (idx),""),'feedback':record.get("verify_%s_feedback" % (idx),"")})
        
        return render(req,'Excel/assign.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'form':f})
        
